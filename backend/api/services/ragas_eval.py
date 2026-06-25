import math
import sys
import types

from django.conf import settings
from openai import OpenAI


def score_evaluation_result(result):
    _install_ragas_vertexai_import_shim()

    from datasets import Dataset
    from langchain_ollama import OllamaEmbeddings
    from ragas import evaluate
    from ragas.llms import llm_factory
    from ragas.metrics import _answer_relevancy, _context_precision, _faithfulness

    contexts = [
        context.get('text', '')
        for context in result.retrieved_context
        if context.get('text')
    ]

    if not contexts:
        return {}

    dataset = Dataset.from_list(
        [
            {
                'user_input': result.question_item.question,
                'question': result.question_item.question,
                'response': result.generated_answer,
                'answer': result.generated_answer,
                'retrieved_contexts': contexts,
                'contexts': contexts,
                'reference': result.question_item.expected_answer or result.generated_answer,
                'ground_truth': result.question_item.expected_answer or result.generated_answer,
            }
        ]
    )

    client = OpenAI(api_key='ollama', base_url=f'{settings.OLLAMA_BASE_URL}/v1')
    llm = llm_factory(settings.OLLAMA_LLM_MODEL, provider='openai', client=client)
    embeddings = OllamaEmbeddings(
        model=settings.OLLAMA_EMBED_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )

    scores = evaluate(
        dataset=dataset,
        metrics=[_context_precision, _faithfulness, _answer_relevancy],
        llm=llm,
        embeddings=embeddings,
        show_progress=False,
        raise_exceptions=False,
    )

    row = scores.to_pandas().iloc[0].to_dict()

    return {
        'context_precision': _clean_score(row.get('context_precision')),
        'faithfulness': _clean_score(row.get('faithfulness')),
        'answer_relevance': _clean_score(row.get('answer_relevancy')),
    }


def update_run_averages(evaluation_run):
    results = evaluation_run.results.all()
    fields = [
        ('context_precision', 'average_context_precision'),
        ('faithfulness', 'average_faithfulness'),
        ('answer_relevance', 'average_answer_relevance'),
    ]

    updates = {}
    for source_field, average_field in fields:
        values = [
            getattr(result, source_field)
            for result in results
            if getattr(result, source_field) is not None
        ]
        updates[average_field] = sum(values) / len(values) if values else None

    for field, value in updates.items():
        setattr(evaluation_run, field, value)

    evaluation_run.save(
        update_fields=[
            'average_context_precision',
            'average_faithfulness',
            'average_answer_relevance',
            'updated_at',
        ]
    )


def _install_ragas_vertexai_import_shim():
    module_name = 'langchain_community.chat_models.vertexai'
    if module_name in sys.modules:
        return

    try:
        from langchain_google_vertexai import ChatVertexAI
    except ImportError:
        return

    module = types.ModuleType(module_name)
    module.ChatVertexAI = ChatVertexAI
    sys.modules[module_name] = module


def _clean_score(value):
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if math.isnan(number):
        return None

    return number
