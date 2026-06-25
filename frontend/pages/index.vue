<script setup lang="ts">
import type { EvaluationRunsResponse, Overview, QueriesResponse } from '~/types/api'
import { formatDateTime, formatScore, formatDuration } from '~/utils/format'

const overviewUrl = useApiUrl('/overview/')
const runsUrl = useApiUrl('/evaluation-runs/')
const queriesUrl = useApiUrl('/queries/')

const { data: overview, pending: overviewPending, error: overviewError } = await useFetch<Overview>(overviewUrl)
const { data: runs } = await useFetch<EvaluationRunsResponse>(runsUrl)
const { data: recentQueries, refresh: refreshQueries } = await useFetch<QueriesResponse>(queriesUrl)

const latestRuns = computed(() => runs.value?.results || [])
const latest = computed(() => overview.value?.latest_evaluation_run || null)

// Dashboard tab switching
const activeTab = ref<'evaluations' | 'queries'>('evaluations')

const handleTabChange = (tab: 'evaluations' | 'queries') => {
  activeTab.value = tab
  if (tab === 'queries') {
    refreshQueries()
  }
}
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

    <!-- Trends Charts Section -->
    <section class="content-grid trends-section">
      <div class="panel chart-panel-wrapper">
        <div class="panel-header">
          <div>
            <h2>RAGAS Quality Trends</h2>
            <p>Evaluation run averages over time.</p>
          </div>
        </div>
        <ScoreTrendsChart :runs="latestRuns" />
      </div>

      <div class="panel chart-panel-wrapper">
        <div class="panel-header">
          <div>
            <h2>Token Usage & Latency</h2>
            <p>Recent ask queries execution metrics.</p>
          </div>
        </div>
        <TokenLatencyChart :queries="recentQueries?.results || []" />
      </div>
    </section>

    <!-- Tabbed Data Lists -->
    <section class="panel tabbed-panel">
      <div class="tab-header">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'evaluations' }"
          @click="handleTabChange('evaluations')"
        >
          ▦ Evaluation Runs
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'queries' }"
          @click="handleTabChange('queries')"
        >
          ⌁ Real-time Queries
        </button>
      </div>

      <!-- 1. EVALUATION RUNS TAB -->
      <div v-show="activeTab === 'evaluations'" class="tab-content content-grid">
        <div class="run-summary-card">
          <h3>Latest Run Summary</h3>
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

        <div class="run-table-card">
          <h3>Recent History</h3>
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
                <tr v-for="run in latestRuns.slice(0, 8)" :key="run.id">
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
      </div>

      <!-- 2. REAL-TIME QUERIES TAB -->
      <div v-show="activeTab === 'queries'" class="tab-content">
        <div class="table-wrap">
          <table class="queries-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Question & Sources</th>
                <th class="text-right">Latency</th>
                <th class="text-right">Tokens (P/C)</th>
                <th>Traces</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in recentQueries?.results || []" :key="q.id">
                <td class="cell-monospace">#{{ q.id }}</td>
                <td>
                  <div class="query-question"><strong>{{ q.question }}</strong></div>
                  <div class="query-answer-preview">{{ q.answer.substring(0, 100) }}{{ q.answer.length > 100 ? '...' : '' }}</div>
                  <div v-if="q.sources.length > 0" class="query-sources">
                    <span v-for="(src, idx) in q.sources" :key="idx" class="source-tag">
                      📄 {{ src.document }} (p.{{ src.page_number ?? 'n/a' }})
                    </span>
                  </div>
                </td>
                <td class="text-right cell-monospace">{{ formatDuration(q.latency_ms) }}</td>
                <td class="text-right cell-monospace">
                  {{ q.prompt_tokens ?? 0 }}/{{ q.completion_tokens ?? 0 }}
                </td>
                <td>
                  <div class="trace-badge-container">
                    <span 
                      class="trace-badge langfuse" 
                      :class="{ active: q.langfuse_trace_id }" 
                      :title="q.langfuse_trace_id || 'Offline'"
                    >
                      LF
                    </span>
                    <span 
                      class="trace-badge langsmith" 
                      :class="{ active: q.langsmith_trace_id }" 
                      :title="q.langsmith_trace_id || 'Offline'"
                    >
                      LS
                    </span>
                  </div>
                </td>
              </tr>
              <tr v-if="!recentQueries?.results || recentQueries.results.length === 0">
                <td colspan="5" class="muted-cell text-center">No queries run yet. Use the Ask Console to test a query.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.trends-section {
  margin-bottom: 8px;
}

.chart-panel-wrapper {
  padding: 16px;
}

.tabbed-panel {
  padding: 20px;
}

.tab-header {
  display: flex;
  gap: 14px;
  border-bottom: 2px solid var(--surface-muted);
  margin-bottom: 20px;
  padding-bottom: 8px;
}

.tab-btn {
  background: none;
  border: none;
  font-size: 1rem;
  font-weight: 700;
  color: var(--muted);
  padding: 8px 12px;
  cursor: pointer;
  border-radius: var(--radius);
  transition: all 120ms ease;
}

.tab-btn:hover {
  background: var(--surface-muted);
  color: var(--ink);
}

.tab-btn.active {
  color: var(--primary);
  background: oklch(from var(--primary) l c h / 0.1);
}

.tab-content {
  animation: fadeIn 180ms ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.run-summary-card h3,
.run-table-card h3 {
  font-size: 0.95rem;
  margin: 0 0 14px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.queries-table {
  width: 100%;
}

.queries-table th, 
.queries-table td {
  padding: 14px 10px;
}

.cell-monospace {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.78rem;
}

.query-question {
  font-size: 0.88rem;
  color: var(--ink);
  margin-bottom: 4px;
}

.query-answer-preview {
  font-size: 0.82rem;
  color: var(--muted);
  margin-bottom: 6px;
}

.query-sources {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
}

.source-tag {
  font-size: 0.7rem;
  background: var(--surface-muted);
  color: var(--muted);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid var(--border);
}

.trace-badge-container {
  display: flex;
  gap: 6px;
}

.trace-badge {
  font-size: 0.65rem;
  font-weight: 700;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  border: 1px solid var(--border);
  color: var(--muted);
  opacity: 0.4;
  background: var(--surface-muted);
}

.trace-badge.active.langfuse {
  background: oklch(from var(--primary) l c h / 0.15);
  color: var(--primary);
  border-color: var(--primary);
  opacity: 1;
}

.trace-badge.active.langsmith {
  background: oklch(from var(--success) l c h / 0.15);
  color: var(--success);
  border-color: var(--success);
  opacity: 1;
}

.text-right {
  text-align: right;
}

.text-center {
  text-align: center;
}
</style>
