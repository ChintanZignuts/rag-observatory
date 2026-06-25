<script setup lang="ts">
import type { EvaluationRunsResponse } from '~/types/api'
import { formatDateTime, formatScore } from '~/utils/format'

const { data, pending, error } = await useFetch<EvaluationRunsResponse>(useApiUrl('/evaluation-runs/'))
const runs = computed(() => data.value?.results || [])
</script>

<template>
  <div class="page-stack">
    <header class="page-header compact">
      <div>
        <p class="section-kicker">Evaluation Runs</p>
        <h1>Weekly quality history</h1>
        <p>Review saved baseline and RAGAS-scored evaluations.</p>
      </div>
    </header>

    <section v-if="error" class="alert-panel">Unable to load evaluation runs from Django.</section>

    <section class="panel">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Results</th>
              <th>Context precision</th>
              <th>Faithfulness</th>
              <th>Answer relevance</th>
              <th>Completed</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="pending">
              <td colspan="7" class="muted-cell">Loading evaluation runs...</td>
            </tr>
            <tr v-for="run in runs" :key="run.id">
              <td>
                <NuxtLink :to="`/evaluations/${run.id}`">{{ run.name }}</NuxtLink>
                <small>#{{ run.id }}</small>
              </td>
              <td><RunStatus :status="run.status" /></td>
              <td>{{ run.results_count ?? 0 }}</td>
              <td>{{ formatScore(run.average_context_precision) }}</td>
              <td>{{ formatScore(run.average_faithfulness) }}</td>
              <td>{{ formatScore(run.average_answer_relevance) }}</td>
              <td>{{ formatDateTime(run.completed_at) }}</td>
            </tr>
            <tr v-if="!pending && runs.length === 0">
              <td colspan="7" class="muted-cell">No evaluation runs found.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
