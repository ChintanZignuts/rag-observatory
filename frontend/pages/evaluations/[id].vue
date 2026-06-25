<script setup lang="ts">
import type { EvaluationRunDetail } from '~/types/api'
import { formatDateTime, formatScore } from '~/utils/format'

const route = useRoute()
const { data: run, pending, error } = await useFetch<EvaluationRunDetail>(
  useApiUrl(`/evaluation-runs/${route.params.id}/`),
)
</script>

<template>
  <div class="page-stack">
    <header class="page-header compact">
      <div>
        <p class="section-kicker">Run Detail</p>
        <h1>{{ run?.name || 'Evaluation run' }}</h1>
        <p>{{ run ? `Completed ${formatDateTime(run.completed_at)}` : 'Loading run details...' }}</p>
      </div>
      <NuxtLink class="button secondary" to="/evaluations">Back to runs</NuxtLink>
    </header>

    <section v-if="error" class="alert-panel">Unable to load this evaluation run.</section>

    <section v-if="run" class="metrics-grid three">
      <MetricTile label="Context precision" :value="formatScore(run.average_context_precision)" detail="RAGAS" />
      <MetricTile label="Faithfulness" :value="formatScore(run.average_faithfulness)" detail="RAGAS" />
      <MetricTile label="Answer relevance" :value="formatScore(run.average_answer_relevance)" detail="RAGAS" />
    </section>

    <section class="panel">
      <div class="panel-header">
        <div>
          <h2>Question results</h2>
          <p>Generated answer, RAGAS scores, and retrieval evidence.</p>
        </div>
        <RunStatus v-if="run" :status="run.status" />
      </div>

      <div v-if="pending" class="empty-state">Loading question results...</div>

      <div v-if="run" class="result-list">
        <article v-for="result in run.results" :key="result.id" class="result-row">
          <div class="result-main">
            <div class="result-title">
              <strong>{{ result.question_id }}</strong>
              <span>{{ result.category }} / {{ result.difficulty }}</span>
            </div>
            <h3>{{ result.question }}</h3>
            <p>{{ result.generated_answer || result.error_message || 'No answer saved.' }}</p>
          </div>
          <div class="result-scores">
            <ScoreBar label="Context" :value="result.context_precision" />
            <ScoreBar label="Faithfulness" :value="result.faithfulness" />
            <ScoreBar label="Relevance" :value="result.answer_relevance" />
          </div>
        </article>
      </div>
    </section>
  </div>
</template>
