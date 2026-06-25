from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from api.models import DocumentChunk
from api.services.rag import OllamaError, create_embedding


class Command(BaseCommand):
    help = 'Generates embeddings for document chunks using local Ollama.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate embeddings for chunks that already have embeddings.',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of chunks to embed in this run.',
        )

    def handle(self, *args, **options):
        chunks = DocumentChunk.objects.select_related('document').order_by('id')
        if not options['force']:
            chunks = chunks.filter(embedding__isnull=True)
        if options['limit']:
            chunks = chunks[: options['limit']]

        total = len(chunks)
        if total == 0:
            self.stdout.write(self.style.SUCCESS('No chunks need embeddings.'))
            return

        self.stdout.write(
            f'Embedding {total} chunks with {settings.OLLAMA_EMBED_MODEL}...'
        )

        embedded_count = 0
        for index, chunk in enumerate(chunks, start=1):
            embedding = self._create_embedding(chunk.text)
            chunk.embedding = embedding
            chunk.save(update_fields=['embedding', 'updated_at'])
            embedded_count += 1

            self.stdout.write(
                f'[{index}/{total}] Embedded {chunk.document.file_name} #{chunk.chunk_index}'
            )

        self.stdout.write(
            self.style.SUCCESS(f'Completed embeddings for {embedded_count} chunks.')
        )

    def _create_embedding(self, text):
        try:
            return create_embedding(text)
        except OllamaError as error:
            raise CommandError(
                'Could not connect to Ollama. Make sure `ollama serve` is running '
                f'at {settings.OLLAMA_BASE_URL}. Original error: {error}'
            ) from error
