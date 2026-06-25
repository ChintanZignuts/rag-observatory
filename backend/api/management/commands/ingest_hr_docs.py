import hashlib
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from pypdf import PdfReader

from api.models import DocumentChunk, PolicyDocument


CHUNK_SIZE = 1800
CHUNK_OVERLAP = 250


class Command(BaseCommand):
    help = 'Extracts HR policy PDFs into searchable document chunks.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--docs-dir',
            default=str(settings.BASE_DIR.parent / 'HR docs'),
            help='Directory containing HR policy PDF files.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recreate chunks even when the PDF hash has not changed.',
        )

    def handle(self, *args, **options):
        docs_dir = Path(options['docs_dir']).expanduser().resolve()
        if not docs_dir.exists():
            raise CommandError(f'Docs directory does not exist: {docs_dir}')

        pdf_paths = sorted(docs_dir.glob('*.pdf'))
        if not pdf_paths:
            raise CommandError(f'No PDF files found in: {docs_dir}')

        total_documents = 0
        total_chunks = 0

        for pdf_path in pdf_paths:
            document, chunk_count = self._ingest_pdf(pdf_path, force=options['force'])
            total_documents += 1
            total_chunks += chunk_count
            self.stdout.write(
                self.style.SUCCESS(
                    f'Ingested {document.file_name}: {chunk_count} chunks'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Completed ingestion: {total_documents} documents, {total_chunks} chunks'
            )
        )

    def _ingest_pdf(self, pdf_path, force=False):
        file_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        reader = PdfReader(str(pdf_path))

        document, created = PolicyDocument.objects.update_or_create(
            file_name=pdf_path.name,
            defaults={
                'title': pdf_path.stem.strip(),
                'file_path': str(pdf_path),
                'category': self._category_from_filename(pdf_path.name),
                'page_count': len(reader.pages),
                'content_hash': file_hash,
            },
        )

        if not created and document.content_hash == file_hash and not force and document.chunks.exists():
            return document, document.chunks.count()

        document.chunks.all().delete()

        chunk_index = 0
        for page_number, page in enumerate(reader.pages, start=1):
            text = self._normalize_text(page.extract_text() or '')
            if not text:
                continue

            for chunk_text in self._split_text(text):
                DocumentChunk.objects.create(
                    document=document,
                    chunk_index=chunk_index,
                    text=chunk_text,
                    page_number=page_number,
                    token_count=len(chunk_text.split()),
                )
                chunk_index += 1

        return document, chunk_index

    def _normalize_text(self, text):
        text = text.replace('\x00', ' ')
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _split_text(self, text):
        if len(text) <= CHUNK_SIZE:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            chunk = text[start:end].strip()

            if end < len(text):
                last_break = max(chunk.rfind('\n\n'), chunk.rfind('. '))
                if last_break > CHUNK_SIZE * 0.55:
                    end = start + last_break + 1
                    chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            next_start = end - CHUNK_OVERLAP
            start = max(next_start, end) if next_start <= start else next_start

        return chunks

    def _category_from_filename(self, file_name):
        name = file_name.lower()
        if 'leave' in name:
            return 'Leave'
        if 'remote' in name:
            return 'Remote Work'
        if 'working' in name or 'hours' in name:
            return 'Attendance'
        if 'resignation' in name or 'termination' in name or 'separation' in name:
            return 'Separation'
        if 'social' in name or 'attire' in name:
            return 'Conduct'
        if 'service request' in name:
            return 'Service Request'
        return 'General'
