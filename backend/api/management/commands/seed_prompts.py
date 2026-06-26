from django.core.management.base import BaseCommand
from django.conf import settings
from langsmith import traceable
import logging

logger = logging.getLogger(__name__)

PROMPT_CONTENT = """You are an HR policy assistant for an internal company knowledge base.

Rules:
- Answer only using the provided policy context.
- If the context does not contain the answer, say: "I could not find this in the provided HR policy documents."
- Do not invent policy details.
- Keep the answer concise and practical.
- Include a "Sources" section listing document names and page numbers used.

Question:
{{question}}

Policy context:
{{contexts}}

Answer:"""

class Command(BaseCommand):
    help = 'Seeds the HR policy QA prompt into the Langfuse Prompt Registry.'

    def handle(self, *args, **options):
        if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
            self.stdout.write(
                self.style.ERROR(
                    'Langfuse credentials are not set in backend/.env. Cannot seed prompt.'
                )
            )
            return

        from langfuse import Langfuse
        self.stdout.write('Initializing Langfuse client...')
        langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST
        )

        self.stdout.write('Seeding hr_policy_qa_prompt to Langfuse Prompt Registry...')
        try:
            prompt = langfuse_client.create_prompt(
                name="hr_policy_qa_prompt",
                prompt=PROMPT_CONTENT,
                labels=["production"]
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully registered prompt version {prompt.version} and set label "production".'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Failed to seed prompt: {e}'
                )
            )
