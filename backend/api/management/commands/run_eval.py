from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import EvaluationResult, EvaluationRun, QuestionSetItem
from api.services.ragas_eval import score_evaluation_result, update_run_averages
from api.services.rag import OllamaError, answer_question


class Command(BaseCommand):
    help = 'Runs the evaluation question set against the RAG pipeline.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            default='Manual RAG Evaluation',
            help='Name for this evaluation run.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of active questions to evaluate.',
        )
        parser.add_argument(
            '--top-k',
            type=int,
            default=5,
            help='Number of chunks to retrieve for each question.',
        )
        parser.add_argument(
            '--score-with-ragas',
            action='store_true',
            help='Run RAGAS scoring after each generated answer.',
        )
        parser.add_argument(
            '--run-id',
            type=int,
            default=None,
            help='Reuse existing EvaluationRun ID.',
        )

    def handle(self, *args, **options):
        questions = QuestionSetItem.objects.filter(is_active=True).order_by('question_id')
        if options['limit']:
            questions = questions[: options['limit']]

        run_id = options.get('run_id')
        if run_id:
            try:
                evaluation_run = EvaluationRun.objects.get(id=run_id)
                evaluation_run.status = 'running'
                evaluation_run.started_at = timezone.now()
                evaluation_run.save(update_fields=['status', 'started_at', 'updated_at'])
            except EvaluationRun.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"EvaluationRun #{run_id} does not exist."))
                return
        else:
            evaluation_run = EvaluationRun.objects.create(
                name=options['name'],
                status='running',
                started_at=timezone.now(),
            )

        self.stdout.write(f'Started evaluation run #{evaluation_run.id}: {evaluation_run.name}')

        try:
            for index, question_item in enumerate(questions, start=1):
                self.stdout.write(f'[{index}] {question_item.question_id}: {question_item.question}')
                self._evaluate_question(
                    evaluation_run=evaluation_run,
                    question_item=question_item,
                    top_k=options['top_k'],
                    score_with_ragas=options['score_with_ragas'],
                )
        except Exception as error:
            evaluation_run.status = 'failed'
            evaluation_run.completed_at = timezone.now()
            evaluation_run.notes = str(error)
            evaluation_run.save(update_fields=['status', 'completed_at', 'notes', 'updated_at'])
            raise

        evaluation_run.status = 'completed'
        evaluation_run.completed_at = timezone.now()
        evaluation_run.save(update_fields=['status', 'completed_at', 'updated_at'])
        update_run_averages(evaluation_run)

        self.stdout.write(
            self.style.SUCCESS(
                f'Completed evaluation run #{evaluation_run.id} with {evaluation_run.results.count()} results.'
            )
        )

    def _evaluate_question(self, evaluation_run, question_item, top_k, score_with_ragas):
        try:
            rag_result = answer_question(question=question_item.question, top_k=top_k)
        except OllamaError as error:
            EvaluationResult.objects.create(
                evaluation_run=evaluation_run,
                question_item=question_item,
                error_message=str(error),
            )
            return

        result = EvaluationResult.objects.create(
            evaluation_run=evaluation_run,
            question_item=question_item,
            rag_query_id=rag_result['id'],
            generated_answer=rag_result['answer'],
            retrieved_context=rag_result['retrieved_context'],
        )

        if not score_with_ragas:
            return

        try:
            scores = score_evaluation_result(result)
        except Exception as error:
            result.error_message = f'RAGAS scoring failed: {error}'
            result.save(update_fields=['error_message', 'updated_at'])
            return

        result.context_precision = scores.get('context_precision')
        result.faithfulness = scores.get('faithfulness')
        result.answer_relevance = scores.get('answer_relevance')
        result.save(
            update_fields=[
                'context_precision',
                'faithfulness',
                'answer_relevance',
                'updated_at',
            ]
        )
