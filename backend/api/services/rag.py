import json
import math
import urllib.error
import urllib.request
from time import perf_counter

from django.conf import settings
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree
from langfuse.decorators import observe, langfuse_context

from api.models import DocumentChunk, RagQuery


class OllamaError(RuntimeError):
    pass


def create_embedding(text):
    payload = json.dumps(
        {
            'model': settings.OLLAMA_EMBED_MODEL,
            'prompt': text,
        }
    ).encode('utf-8')

    request = urllib.request.Request(
        f'{settings.OLLAMA_BASE_URL}/api/embeddings',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as error:
        raise OllamaError(
            f'Could not connect to Ollama at {settings.OLLAMA_BASE_URL}: {error}'
        ) from error

    embedding = data.get('embedding')
    if not isinstance(embedding, list) or not embedding:
        raise OllamaError(f'Ollama returned an invalid embedding response: {data}')

    return embedding


@observe(as_type="span", name="Retrieve Chunks")
@traceable(name="Retrieve Chunks", run_type="retriever")
def search_chunks(query, top_k=5):
    query_embedding = create_embedding(query)
    candidates = DocumentChunk.objects.select_related('document').exclude(
        embedding__isnull=True
    )

    scored_chunks = []
    for chunk in candidates:
        score = cosine_similarity(query_embedding, chunk.embedding)
        scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda item: item[0], reverse=True)

    return [
        {
            'chunk_id': chunk.id,
            'score': round(score, 6),
            'document': chunk.document.file_name,
            'category': chunk.document.category,
            'page_number': chunk.page_number,
            'chunk_index': chunk.chunk_index,
            'text': chunk.text,
        }
        for score, chunk in scored_chunks[:top_k]
    ]


@observe(name="HR Policy RAG Q&A")
@traceable(name="HR Policy RAG Q&A", run_type="chain")
def answer_question(question, top_k=5):
    started_at = perf_counter()
    contexts = search_chunks(question, top_k=top_k)
    prompt = build_answer_prompt(question=question, contexts=contexts)
    generation = generate_text(prompt)
    latency_ms = int((perf_counter() - started_at) * 1000)

    answer = generation.get('response', '').strip()
    source_documents = sorted({context['document'] for context in contexts})

    langsmith_trace_id = ""
    try:
        run_tree = get_current_run_tree()
        if run_tree:
            langsmith_trace_id = str(run_tree.id)
    except Exception:
        pass

    langfuse_trace_id = ""
    try:
        langfuse_trace_id = langfuse_context.get_current_trace_id() or ""
    except Exception:
        pass

    try:
        langfuse_context.update_current_trace(
            input=question,
            output=answer,
            metadata={"top_k": top_k, "source_documents": source_documents}
        )
    except Exception:
        pass

    rag_query = RagQuery.objects.create(
        question=question,
        answer=answer,
        retrieved_context=contexts,
        source_documents=source_documents,
        latency_ms=latency_ms,
        prompt_tokens=generation.get('prompt_eval_count'),
        completion_tokens=generation.get('eval_count'),
        langsmith_trace_id=langsmith_trace_id,
        langfuse_trace_id=langfuse_trace_id,
    )

    return {
        'id': rag_query.id,
        'question': question,
        'answer': answer,
        'sources': [
            {
                'document': context['document'],
                'page_number': context['page_number'],
                'score': context['score'],
                'chunk_id': context['chunk_id'],
            }
            for context in contexts
        ],
        'retrieved_context': contexts,
        'latency_ms': latency_ms,
        'prompt_tokens': rag_query.prompt_tokens,
        'completion_tokens': rag_query.completion_tokens,
    }


@observe(as_type="generation", name="Generate Text")
@traceable(name="Generate Text", run_type="llm")
def generate_text(prompt):
    payload = json.dumps(
        {
            'model': settings.OLLAMA_LLM_MODEL,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.1,
                'num_predict': 700,
            },
        }
    ).encode('utf-8')

    request = urllib.request.Request(
        f'{settings.OLLAMA_BASE_URL}/api/generate',
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            data = json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as error:
        raise OllamaError(
            f'Could not connect to Ollama at {settings.OLLAMA_BASE_URL}: {error}'
        ) from error

    if not isinstance(data.get('response'), str):
        raise OllamaError(f'Ollama returned an invalid generation response: {data}')

    langfuse_context.update_current_observation(
        input=prompt,
        output=data.get('response'),
        model=settings.OLLAMA_LLM_MODEL,
        usage={
            "input": data.get('prompt_eval_count', 0),
            "output": data.get('eval_count', 0)
        }
    )

    return data


def build_answer_prompt(question, contexts):
    context_blocks = []
    for index, context in enumerate(contexts, start=1):
        context_blocks.append(
            '\n'.join(
                [
                    f'Source {index}',
                    f'Document: {context["document"]}',
                    f'Page: {context["page_number"] or "unknown"}',
                    f'Similarity score: {context["score"]}',
                    'Policy text:',
                    context['text'],
                ]
            )
        )

    joined_context = '\n\n---\n\n'.join(context_blocks)

    return f"""You are an HR policy assistant for an internal company knowledge base.

Rules:
- Answer only using the provided policy context.
- If the context does not contain the answer, say: "I could not find this in the provided HR policy documents."
- Do not invent policy details.
- Keep the answer concise and practical.
- Include a "Sources" section listing document names and page numbers used.

Question:
{question}

Policy context:
{joined_context}

Answer:"""


def cosine_similarity(left, right):
    if not left or not right or len(left) != len(right):
        return 0.0

    dot_product = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot_product / (left_norm * right_norm)
