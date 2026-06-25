<script setup lang="ts">
import type { EvaluationRunsResponse, Overview } from '~/types/api'
import { formatDateTime, formatScore } from '~/utils/format'

const overviewUrl = useApiUrl('/overview/')
const runsUrl = useApiUrl('/evaluation-runs/')

const { data: overview, pending: overviewPending, error: overviewError } = await useFetch<Overview>(overviewUrl)
const { data: runs } = await useFetch<EvaluationRunsResponse>(runsUrl)

const latestRuns = computed(() => runs.value?.results?.slice(0, 5) || [])
const latest = computed(() => overview.value?.latest_evaluation_run || null)
</script>

<template>
  <div class="page-stack">
    <header class="page-header">
      <div>
        <p class="section-kicker">Production AI Evaluation</p>
        <h1>HR policy assistant quality</h1>
        <p>
          Monitor document coverage, evaluation runs, and answer quality for the local RAG pipeline.
        </p>
      </div>
      <NuxtLink class="button primary" to="/ask">Test a question</NuxtLink>
    </header>

    <section v-if="overviewError" class="alert-panel">
      Django API is not reachable. Start the backend on port 8001 and refresh this page.
    </section>

    <section class="metrics-grid" aria-label="System summary">
      <MetricTile label="Policy documents" :value="overviewPending ? '...' : overview?.documents_count ?? 0" detail="PDFs ingested" />
      <MetricTile label="Searchable chunks" :value="overviewPending ? '...' : overview?.chunks_count ?? 0" detail="Embedded vectors" />
      <MetricTile label="Eval questions" :value="overviewPending ? '...' : overview?.questions_count ?? 0" detail="Active test set" />
      <MetricTile
        label="Latest faithfulness"
        :value="latest ? formatScore(latest.average_faithfulness) : 'Pending'"
        detail="RAGAS score"
        :tone="latest?.average_faithfulness && latest.average_faithfulness > 0.75 ? 'good' : 'neutral'"
      />
    </section>

    <section class="content-grid">
      <div class="panel">
        <div class="panel-header">
          <div>
            <h2>Latest evaluation</h2>
            <p>Most recent saved quality run.</p>
          </div>
          <NuxtLink class="button secondary" to="/evaluations">View all</NuxtLink>
        </div>

        <div v-if="latest" class="run-summary">
          <div class="summary-line">
            <span>Name</span>
            <strong>{{ latest.name }}</strong>
          </div>
          <div class="summary-line">
            <span>Status</span>
            <RunStatus :status="latest.status" />
          </div>
          <div class="summary-line">
            <span>Completed</span>
            <strong>{{ formatDateTime(latest.completed_at) }}</strong>
          </div>
          <ScoreBar label="Context precision" :value="latest.average_context_precision" />
          <ScoreBar label="Faithfulness" :value="latest.average_faithfulness" />
          <ScoreBar label="Answer relevance" :value="latest.average_answer_relevance" />
        </div>

        <div v-else class="empty-state">
          <strong>No scored run yet</strong>
          <span>Run `python manage.py run_eval --name "Baseline" --limit 3` to create the first record.</span>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header">
          <div>
            <h2>Recent runs</h2>
            <p>Evaluation history from Django.</p>
          </div>
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Status</th>
                <th>Faithfulness</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="run in latestRuns" :key="run.id">
                <td>
                  <NuxtLink :to="`/evaluations/${run.id}`">{{ run.name }}</NuxtLink>
                  <small>{{ formatDateTime(run.created_at) }}</small>
                </td>
                <td><RunStatus :status="run.status" /></td>
                <td>{{ formatScore(run.average_faithfulness) }}</td>
              </tr>
              <tr v-if="latestRuns.length === 0">
                <td colspan="3" class="muted-cell">No evaluations saved yet.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>
