from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PolicyDocument(TimeStampedModel):
    title = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255, unique=True)
    file_path = models.CharField(max_length=500)
    category = models.CharField(max_length=100, blank=True)
    page_count = models.PositiveIntegerField(default=0)
    content_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class DocumentChunk(TimeStampedModel):
    document = models.ForeignKey(
        PolicyDocument,
        related_name='chunks',
        on_delete=models.CASCADE,
    )
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    page_number = models.PositiveIntegerField(null=True, blank=True)
    section_title = models.CharField(max_length=255, blank=True)
    token_count = models.PositiveIntegerField(default=0)
    embedding = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['document_id', 'chunk_index']
        constraints = [
            models.UniqueConstraint(
                fields=['document', 'chunk_index'],
                name='unique_document_chunk_index',
            )
        ]

    def __str__(self):
        return f'{self.document.file_name} #{self.chunk_index}'


class QuestionSetItem(TimeStampedModel):
    question_id = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=50)
    question = models.TextField()
    expected_answer = models.TextField(blank=True)
    source_doc = models.CharField(max_length=255, blank=True)
    source_section = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['question_id']

    def __str__(self):
        return f'{self.question_id}: {self.question[:80]}'


class RagQuery(TimeStampedModel):
    question = models.TextField()
    answer = models.TextField(blank=True)
    retrieved_context = models.JSONField(default=list, blank=True)
    source_documents = models.JSONField(default=list, blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    prompt_tokens = models.PositiveIntegerField(null=True, blank=True)
    completion_tokens = models.PositiveIntegerField(null=True, blank=True)
    langsmith_trace_id = models.CharField(max_length=255, blank=True)
    langfuse_trace_id = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.question[:100]


class EvaluationRun(TimeStampedModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    average_context_precision = models.FloatField(null=True, blank=True)
    average_faithfulness = models.FloatField(null=True, blank=True)
    average_answer_relevance = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class EvaluationResult(TimeStampedModel):
    evaluation_run = models.ForeignKey(
        EvaluationRun,
        related_name='results',
        on_delete=models.CASCADE,
    )
    question_item = models.ForeignKey(
        QuestionSetItem,
        related_name='evaluation_results',
        on_delete=models.PROTECT,
    )
    rag_query = models.ForeignKey(
        RagQuery,
        related_name='evaluation_results',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    generated_answer = models.TextField(blank=True)
    retrieved_context = models.JSONField(default=list, blank=True)
    context_precision = models.FloatField(null=True, blank=True)
    faithfulness = models.FloatField(null=True, blank=True)
    answer_relevance = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['evaluation_run_id', 'question_item_id']
        constraints = [
            models.UniqueConstraint(
                fields=['evaluation_run', 'question_item'],
                name='unique_eval_result_per_question',
            )
        ]

    def __str__(self):
        return f'{self.evaluation_run.name} - {self.question_item.question_id}'
