import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from api.models import QuestionSetItem


class Command(BaseCommand):
    help = 'Loads evaluation questions from question.json.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            default=str(settings.BASE_DIR.parent / 'question.json'),
            help='Path to the evaluation question JSON file.',
        )

    def handle(self, *args, **options):
        questions_path = Path(options['file']).expanduser().resolve()
        if not questions_path.exists():
            raise CommandError(f'Questions file does not exist: {questions_path}')

        with questions_path.open('r', encoding='utf-8') as file:
            questions = json.load(file)

        if not isinstance(questions, list):
            raise CommandError('Questions file must contain a JSON array.')

        created_count = 0
        updated_count = 0

        for item in questions:
            question_id = item.get('id')
            if not question_id:
                raise CommandError('Every question must include an "id" field.')

            _, created = QuestionSetItem.objects.update_or_create(
                question_id=question_id,
                defaults={
                    'category': item.get('category', ''),
                    'difficulty': item.get('difficulty', ''),
                    'question': item.get('question', ''),
                    'expected_answer': item.get('expected_answer', ''),
                    'source_doc': item.get('source_doc', ''),
                    'source_section': item.get('source_section', ''),
                    'is_active': True,
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Loaded questions: {created_count} created, {updated_count} updated'
            )
        )
