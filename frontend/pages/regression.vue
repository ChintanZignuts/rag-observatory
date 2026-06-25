<script setup lang="ts">
import type { EvaluationRunsResponse, EvaluationRunDetail } from '~/types/api'
import { formatScore } from '~/utils/format'

const runsUrl = useApiUrl('/evaluation-runs/')

const { data: runsListResponse, pending: loadingList } = await useFetch<EvaluationRunsResponse>(runsUrl)
const runs = computed(() => runsListResponse.value?.results?.filter(r => r.status === 'completed') || [])

// Selected run IDs
const runAId = ref<number | null>(null)
const runBId = ref<number | null>(null)

// Fetch details when runs are selected
const runADetail = ref<EvaluationRunDetail | null>(null)
const runBDetail = ref<EvaluationRunDetail | null>(null)

const loadingA = ref(false)
const loadingB = ref(false)

watch(runAId, async (newVal) => {
  if (!newVal) {
    runADetail.value = null
    return
  }
  loadingA.value = true
  try {
    runADetail.value = await $fetch<EvaluationRunDetail>(useApiUrl(`/evaluation-runs/${newVal}/`))
  } catch (err) {
    console.error('Failed to load Run A', err)
  } finally {
    loadingA.value = false
  }
})

watch(runBId, async (newVal) => {
  if (!newVal) {
    runBDetail.value = null
    return
  }
  loadingB.value = true
  try {
    runBDetail.value = await $fetch<EvaluationRunDetail>(useApiUrl(`/evaluation-runs/${newVal}/`))
  } catch (err) {
    console.error('Failed to load Run B', err)
  } finally {
    loadingB.value = false
  }
})

// Automatically set default selected runs if available
onMounted(() => {
  if (runs.value.length >= 2) {
    runAId.value = runs.value[1].id // older run
    runBId.value = runs.value[0].id // newer run
  } else if (runs.value.length === 1) {
    runAId.value = runs.value[0].id
  }
})

// Compare questions side by side
const comparisonRows = computed(() => {
  if (!runADetail.value || !runBDetail.value) return []
  
  const mapA = new Map(runADetail.value.results.map(r => [r.question_id, r]))
  const mapB = new Map(runBDetail.value.results.map(r => [r.question_id, r]))
  
  // Get all unique question IDs
  const allIds = Array.from(new Set([...mapA.keys(), ...mapB.keys()])).sort()
  
  return allIds.map(id => {
    const resultA = mapA.get(id)
    const resultB = mapB.get(id)
    
    const questionText = resultB?.question || resultA?.question || 'Unknown Question'
    
    // Helper to calculate delta and check drop
    const getDelta = (valA: number | null, valB: number | null) => {
      if (valA === null || valB === null) return null
      return valB - valA
    }
    
    const precisionDelta = getDelta(resultA?.context_precision ?? null, resultB?.context_precision ?? null)
    const faithfulnessDelta = getDelta(resultA?.faithfulness ?? null, resultB?.faithfulness ?? null)
    const relevanceDelta = getDelta(resultA?.answer_relevance ?? null, resultB?.answer_relevance ?? null)
    
    return {
      question_id: id,
      question: questionText,
      resultA,
      resultB,
      precisionDelta,
      faithfulnessDelta,
      relevanceDelta
    }
  })
})

const getDeltaClass = (delta: number | null) => {
  if (delta === null) return 'delta-neutral'
  if (delta <= -0.10) return 'delta-negative' // regression! (drop of 10%+)
  if (delta >= 0.10) return 'delta-positive' // improvement!
  return 'delta-neutral'
}

const formatDelta = (delta: number | null) => {
  if (delta === null) return '-'
  const pct = Math.round(delta * 100)
  return pct > 0 ? `+${pct}%` : `${pct}%`
}
</script>

<template>
  <div class="page-stack">
    <header class="page-header compact">
      <div>
        <p class="section-kicker">Quality Assurance</p>
        <h1>Regression Comparison</h1>
        <p>Compare RAGAS scores side-by-side across two evaluation runs to detect performance drops.</p>
      </div>
    </header>

    <!-- Run Selector Panel -->
    <section class="panel selector-panel">
      <div class="selectors">
        <!-- Older Run A Selection -->
        <label class="select-box">
          <span>Run A (Baseline / Older)</span>
          <select v-model="runAId" :disabled="loadingList">
            <option :value="null">-- Select Evaluation Run --</option>
            <option v-for="run in runs" :key="run.id" :value="run.id">
              #{{ run.id }} - {{ run.name }} ({{ formatScore(run.average_faithfulness) }} Faithfulness)
            </option>
          </select>
        </label>

        <span class="compare-vs">VS</span>

        <!-- Newer Run B Selection -->
        <label class="select-box">
          <span>Run B (Comparison / Newer)</span>
          <select v-model="runBId" :disabled="loadingList">
            <option :value="null">-- Select Evaluation Run --</option>
            <option v-for="run in runs" :key="run.id" :value="run.id">
              #{{ run.id }} - {{ run.name }} ({{ formatScore(run.average_faithfulness) }} Faithfulness)
            </option>
          </select>
        </label>
      </div>
    </section>

    <!-- Comparison details -->
    <div v-if="loadingA || loadingB" class="panel empty-state text-center">
      <strong>Fetching run comparisons...</strong>
    </div>

    <div v-else-if="!runADetail || !runBDetail" class="panel empty-state">
      <strong>Select two completed runs to analyze</strong>
      <span>Choose a baseline run and a comparison run to view regression analysis.</span>
    </div>

    <!-- Comparison Results -->
    <div v-else class="comparison-results">
      <!-- High level run summary comparison cards -->
      <section class="metrics-grid">
        <div class="metric-card panel">
          <h3>Context Precision</h3>
          <div class="comparison-value">
            <span class="val-a">{{ formatScore(runADetail.average_context_precision) }}</span>
            <span class="arrow">→</span>
            <span class="val-b">{{ formatScore(runBDetail.average_context_precision) }}</span>
          </div>
        </div>

        <div class="metric-card panel">
          <h3>Faithfulness</h3>
          <div class="comparison-value">
            <span class="val-a">{{ formatScore(runADetail.average_faithfulness) }}</span>
            <span class="arrow">→</span>
            <span class="val-b">{{ formatScore(runBDetail.average_faithfulness) }}</span>
          </div>
        </div>

        <div class="metric-card panel">
          <h3>Answer Relevance</h3>
          <div class="comparison-value">
            <span class="val-a">{{ formatScore(runADetail.average_answer_relevance) }}</span>
            <span class="arrow">→</span>
            <span class="val-b">{{ formatScore(runBDetail.average_answer_relevance) }}</span>
          </div>
        </div>
      </section>

      <!-- Side-by-side Table of Questions -->
      <section class="panel table-panel">
        <div class="panel-header">
          <div>
            <h2>Question Regression Breakdown</h2>
            <p>Highlights performance updates across all tested questions.</p>
          </div>
        </div>

        <div class="table-wrap">
          <table class="regression-table">
            <thead>
              <tr>
                <th>ID & Question</th>
                <th class="text-center">Precision A → B</th>
                <th class="text-center">Faithfulness A → B</th>
                <th class="text-center">Relevance A → B</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in comparisonRows" :key="row.question_id" class="regression-row">
                <td class="question-cell">
                  <div class="cell-id">{{ row.question_id }}</div>
                  <div class="cell-question">{{ row.question }}</div>
                </td>
                
                <!-- Precision Comparison -->
                <td class="score-comparison-cell">
                  <div class="score-flow">
                    <span>{{ formatScore(row.resultA?.context_precision) }}</span>
                    <span class="small-arrow">→</span>
                    <span>{{ formatScore(row.resultB?.context_precision) }}</span>
                  </div>
                  <span class="delta-badge" :class="getDeltaClass(row.precisionDelta)">
                    {{ formatDelta(row.precisionDelta) }}
                  </span>
                </td>

                <!-- Faithfulness Comparison -->
                <td class="score-comparison-cell">
                  <div class="score-flow">
                    <span>{{ formatScore(row.resultA?.faithfulness) }}</span>
                    <span class="small-arrow">→</span>
                    <span>{{ formatScore(row.resultB?.faithfulness) }}</span>
                  </div>
                  <span class="delta-badge" :class="getDeltaClass(row.faithfulnessDelta)">
                    {{ formatDelta(row.faithfulnessDelta) }}
                  </span>
                </td>

                <!-- Relevance Comparison -->
                <td class="score-comparison-cell">
                  <div class="score-flow">
                    <span>{{ formatScore(row.resultA?.answer_relevance) }}</span>
                    <span class="small-arrow">→</span>
                    <span>{{ formatScore(row.resultB?.answer_relevance) }}</span>
                  </div>
                  <span class="delta-badge" :class="getDeltaClass(row.relevanceDelta)">
                    {{ formatDelta(row.relevanceDelta) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.selector-panel {
  padding: 16px;
}

.selectors {
  display: flex;
  align-items: center;
  gap: 20px;
  width: 100%;
}

.select-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-grow: 1;
  font-weight: 600;
  color: var(--muted);
}

select {
  min-height: 42px;
  padding: 0 12px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: white;
  color: var(--ink);
  font-size: 0.9rem;
}

.compare-vs {
  font-weight: 700;
  color: var(--muted);
  font-size: 1.1rem;
  margin-top: 24px;
}

.comparison-results {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.metric-card h3 {
  margin: 0 0 10px;
  font-size: 0.85rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.comparison-value {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1.8rem;
  font-weight: 700;
}

.val-a {
  color: var(--muted);
}

.arrow {
  color: var(--border);
  font-weight: 400;
}

.val-b {
  color: var(--ink);
}

.table-panel {
  padding: 18px;
}

.regression-table {
  width: 100%;
  border-collapse: collapse;
}

.regression-row th,
.regression-row td {
  padding: 14px 10px;
}

.question-cell {
  max-width: 380px;
}

.cell-id {
  font-family: ui-monospace, monospace;
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--primary);
  margin-bottom: 4px;
}

.cell-question {
  font-size: 0.88rem;
  line-height: 1.45;
  color: var(--ink);
}

.score-comparison-cell {
  text-align: center;
  vertical-align: middle;
  width: 160px;
}

.score-flow {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 600;
  font-size: 0.88rem;
  margin-bottom: 6px;
  font-family: ui-monospace, monospace;
}

.small-arrow {
  color: var(--muted);
  font-weight: 400;
}

.delta-badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  font-family: ui-monospace, monospace;
}

.delta-neutral {
  background: var(--surface-muted);
  color: var(--muted);
}

.delta-positive {
  background: oklch(0.95 0.02 150);
  color: var(--success);
}

.delta-negative {
  background: oklch(0.95 0.02 28);
  color: var(--danger);
  animation: pulse 1.8s infinite alternate;
}

.text-center {
  text-align: center;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 oklch(0.55 0.16 28 / 0.25); }
  100% { box-shadow: 0 0 0 4px oklch(0.55 0.16 28 / 0.1); }
}

@media (max-width: 860px) {
  .selectors {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .compare-vs {
    margin-top: 0;
    text-align: center;
  }
}
</style>
