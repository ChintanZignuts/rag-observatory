import threading
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import (
    DocumentChunk,
    EvaluationResult,
    EvaluationRun,
    PolicyDocument,
    QuestionSetItem,
    RagQuery,
)
from .services.rag import OllamaError, answer_question, search_chunks, langfuse_client


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'ok'})


@api_view(['GET'])
def overview(request):
    latest_run = EvaluationRun.objects.order_by('-created_at').first()

    return Response(
        {
            'documents_count': PolicyDocument.objects.count(),
            'chunks_count': DocumentChunk.objects.count(),
            'questions_count': QuestionSetItem.objects.filter(is_active=True).count(),
            'latest_evaluation_run': {
                'id': latest_run.id,
                'name': latest_run.name,
                'status': latest_run.status,
                'average_context_precision': latest_run.average_context_precision,
                'average_faithfulness': latest_run.average_faithfulness,
                'average_answer_relevance': latest_run.average_answer_relevance,
                'created_at': latest_run.created_at,
            }
            if latest_run
            else None,
        }
    )


@api_view(['POST'])
def search(request):
    query = (request.data.get('query') or '').strip()
    top_k = int(request.data.get('top_k') or 5)

    if not query:
        return Response(
            {'error': 'query is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    top_k = max(1, min(top_k, 10))

    try:
        results = search_chunks(query=query, top_k=top_k)
    except OllamaError as error:
        return Response(
            {'error': str(error)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return Response(
        {
            'query': query,
            'top_k': top_k,
            'results': results,
        }
    )


@api_view(['POST'])
def ask(request):
    question = (request.data.get('question') or request.data.get('query') or '').strip()
    top_k = int(request.data.get('top_k') or 5)
    include_context = bool(request.data.get('include_context'))
    min_similarity = request.data.get('min_similarity')

    if min_similarity is not None:
        try:
            min_similarity = float(min_similarity)
        except ValueError:
            min_similarity = None

    if not question:
        return Response(
            {'error': 'question is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    top_k = max(1, min(top_k, 10))

    try:
        result = answer_question(question=question, top_k=top_k, min_similarity=min_similarity)
        try:
            from langfuse.decorators import langfuse_context
            langfuse_context.flush()
        except Exception:
            pass
    except OllamaError as error:
        return Response(
            {'error': str(error)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if not include_context:
        result.pop('retrieved_context', None)

    # Extract Langfuse Project ID from Langfuse client or fallback to Public Key
    project_id = ''
    if langfuse_client:
        try:
            project_id = langfuse_client._get_project_id() or ''
        except Exception:
            pass

    if not project_id:
        public_key = getattr(settings, 'LANGFUSE_PUBLIC_KEY', '')
        project_id = public_key.replace('pk-lf-', '') if public_key.startswith('pk-lf-') else ''

    result['langfuse_project_id'] = project_id
    result['langfuse_host'] = getattr(settings, 'LANGFUSE_HOST', 'https://cloud.langfuse.com')

    return Response(result)


@api_view(['POST'])
def run_evaluation(request):
    name = (request.data.get('name') or '').strip()
    if not name:
        name = f"Manual Run - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"

    score_with_ragas = bool(request.data.get('score_with_ragas', True))

    evaluation_run = EvaluationRun.objects.create(
        name=name,
        status='running',
        started_at=timezone.now(),
    )

    def execute_eval():
        from django.core.management import call_command
        try:
            call_command(
                'run_eval',
                name=name,
                run_id=evaluation_run.id,
                score_with_ragas=score_with_ragas,
            )
        except Exception as e:
            evaluation_run.status = 'failed'
            evaluation_run.completed_at = timezone.now()
            evaluation_run.notes = f"Subprocess error: {e}"
            evaluation_run.save(update_fields=['status', 'completed_at', 'notes', 'updated_at'])

    thread = threading.Thread(target=execute_eval)
    thread.daemon = True
    thread.start()

    return Response(
        {
            'id': evaluation_run.id,
            'name': evaluation_run.name,
            'status': evaluation_run.status,
            'started_at': evaluation_run.started_at,
            'created_at': evaluation_run.created_at,
        },
        status=status.HTTP_202_ACCEPTED
    )


@api_view(['GET'])
def evaluation_runs(request):
    runs = EvaluationRun.objects.order_by('-created_at')[:50]

    return Response(
        {
            'results': [
                {
                    'id': run.id,
                    'name': run.name,
                    'status': run.status,
                    'started_at': run.started_at,
                    'completed_at': run.completed_at,
                    'average_context_precision': run.average_context_precision,
                    'average_faithfulness': run.average_faithfulness,
                    'average_answer_relevance': run.average_answer_relevance,
                    'results_count': run.results.count(),
                    'created_at': run.created_at,
                }
                for run in runs
            ]
        }
    )


@api_view(['GET'])
def evaluation_run_detail(request, run_id):
    try:
        run = EvaluationRun.objects.get(id=run_id)
    except EvaluationRun.DoesNotExist:
        return Response(
            {'error': 'evaluation run not found'},
            status=status.HTTP_404_NOT_FOUND,
        )

    results = EvaluationResult.objects.select_related('question_item').filter(
        evaluation_run=run
    )

    return Response(
        {
            'id': run.id,
            'name': run.name,
            'status': run.status,
            'started_at': run.started_at,
            'completed_at': run.completed_at,
            'average_context_precision': run.average_context_precision,
            'average_faithfulness': run.average_faithfulness,
            'average_answer_relevance': run.average_answer_relevance,
            'notes': run.notes,
            'results': [
                {
                    'id': result.id,
                    'question_id': result.question_item.question_id,
                    'category': result.question_item.category,
                    'difficulty': result.question_item.difficulty,
                    'question': result.question_item.question,
                    'expected_answer': result.question_item.expected_answer,
                    'generated_answer': result.generated_answer,
                    'context_precision': result.context_precision,
                    'faithfulness': result.faithfulness,
                    'answer_relevance': result.answer_relevance,
                    'error_message': result.error_message,
                    'retrieved_context': result.retrieved_context,
                }
                for result in results
            ],
        }
    )


@api_view(['GET'])
def queries(request):
    queries = RagQuery.objects.order_by('-created_at')[:50]

    return Response(
        {
            'results': [
                {
                    'id': q.id,
                    'question': q.question,
                    'answer': q.answer,
                    'latency_ms': q.latency_ms,
                    'prompt_tokens': q.prompt_tokens,
                    'completion_tokens': q.completion_tokens,
                    'langsmith_trace_id': q.langsmith_trace_id,
                    'langfuse_trace_id': q.langfuse_trace_id,
                    'created_at': q.created_at,
                    'sources': [
                        {
                            'document': context.get('document'),
                            'page_number': context.get('page_number'),
                            'score': context.get('score'),
                        }
                        for context in q.retrieved_context
                    ] if isinstance(q.retrieved_context, list) else []
                }
                for q in queries
            ]
        }
    )

