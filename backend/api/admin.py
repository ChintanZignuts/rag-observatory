from django.contrib import admin

from .models import (
    DocumentChunk,
    EvaluationResult,
    EvaluationRun,
    PolicyDocument,
    QuestionSetItem,
    RagQuery,
)


@admin.register(PolicyDocument)
class PolicyDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'file_name', 'page_count', 'updated_at')
    search_fields = ('title', 'file_name', 'category')


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('document', 'chunk_index', 'page_number', 'token_count')
    search_fields = ('document__title', 'text')
    list_filter = ('document',)


@admin.register(QuestionSetItem)
class QuestionSetItemAdmin(admin.ModelAdmin):
    list_display = ('question_id', 'category', 'difficulty', 'is_active')
    search_fields = ('question_id', 'question', 'expected_answer')
    list_filter = ('category', 'difficulty', 'is_active')


@admin.register(RagQuery)
class RagQueryAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'latency_ms', 'created_at')
    search_fields = ('question', 'answer')


@admin.register(EvaluationRun)
class EvaluationRunAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'started_at', 'completed_at')
    list_filter = ('status',)


@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = ('evaluation_run', 'question_item', 'context_precision', 'faithfulness', 'answer_relevance')
    search_fields = ('question_item__question_id', 'generated_answer')
