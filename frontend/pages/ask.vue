<script setup lang="ts">
import type { AskResponse } from '~/types/api'
import { formatDuration } from '~/utils/format'

const question = ref('What is the resignation notice period?')
const topK = ref(5)
const minSimilarity = ref(0.0)
const answer = ref<AskResponse | null>(null)
const errorMessage = ref('')
const pending = ref(false)

const askQuestion = async () => {
  errorMessage.value = ''
  answer.value = null
  pending.value = true

  try {
    answer.value = await $fetch<AskResponse>(useApiUrl('/ask/'), {
      method: 'POST',
      body: {
        question: question.value,
        top_k: topK.value,
        min_similarity: minSimilarity.value,
      },
    })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Question failed.'
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <div class="page-stack">
    <header class="page-header compact">
      <div>
        <p class="section-kicker">Playground Console</p>
        <h1>Interactive Q&A console</h1>
        <p>Submit questions to test retrieval metrics, latency, and dual-trace logging.</p>
      </div>
    </header>

    <div class="ask-grid">
      <!-- Left Column: Form & Output -->
      <div class="ask-main-col">
        <section class="panel ask-panel">
          <form class="ask-form" @submit.prevent="askQuestion">
            <label class="form-label">
              <span>Question</span>
              <textarea v-model="question" rows="4" placeholder="Ask about an HR policy..."></textarea>
            </label>

            <button class="button primary submit-btn" type="submit" :disabled="pending || !question.trim()">
              {{ pending ? 'Running...' : 'Run RAG answer' }}
            </button>
          </form>
        </section>

        <section v-if="errorMessage" class="alert-panel">{{ errorMessage }}</section>

        <section v-if="answer" class="panel answer-panel">
          <div class="panel-header">
            <div>
              <h2>Answer</h2>
              <p>Latency: {{ formatDuration(answer.latency_ms) }} / Prompt: {{ answer.prompt_tokens ?? 'n/a' }} / Completion: {{ answer.completion_tokens ?? 'n/a' }}</p>
            </div>
          </div>

          <div class="answer-block">{{ answer.answer }}</div>

          <div class="source-list">
            <h3>Sources</h3>
            <div v-if="!answer.sources || answer.sources.length === 0" class="no-sources">
              No sources matched the minimum similarity threshold.
            </div>
            <div v-else v-for="source in answer.sources" :key="source.chunk_id" class="source-row">
              <strong>{{ source.document }}</strong>
              <span>Page {{ source.page_number ?? 'unknown' }} / score {{ source.score }}</span>
            </div>
          </div>

          <div style="margin-top: 24px;">
            <TraceTimeline
              :latency-ms="answer.latency_ms"
              :prompt-tokens="answer.prompt_tokens"
              :completion-tokens="answer.completion_tokens"
              :langsmith-trace-id="answer.langsmith_trace_id"
              :langfuse-trace-id="answer.langfuse_trace_id"
              :langfuse-project-id="answer.langfuse_project_id"
              :langfuse-host="answer.langfuse_host"
              :sources="answer.sources"
            />
          </div>
        </section>
      </div>

      <!-- Right Column: Settings Sidebar -->
      <div class="ask-sidebar-col">
        <section class="panel settings-panel">
          <div class="panel-header compact">
            <div>
              <h2>Retrieval settings</h2>
              <p>Tune pipeline parameters.</p>
            </div>
          </div>

          <div class="settings-form">
            <div class="setting-item">
              <div class="setting-label-row">
                <span class="setting-title">Top K</span>
                <span class="setting-val">{{ topK }}</span>
              </div>
              <p class="setting-desc">Number of relevant policy chunks to retrieve.</p>
              <input v-model.number="topK" type="range" min="1" max="10" step="1" class="slider-input" />
            </div>

            <div class="setting-item">
              <div class="setting-label-row">
                <span class="setting-title">Min Similarity</span>
                <span class="setting-val">{{ minSimilarity.toFixed(2) }}</span>
              </div>
              <p class="setting-desc">Minimum cosine similarity threshold score.</p>
              <input v-model.number="minSimilarity" type="range" min="0.0" max="1.0" step="0.05" class="slider-input" />
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ask-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 24px;
  align-items: start;
}

.ask-main-col {
  display: grid;
  gap: 24px;
}

.ask-sidebar-col {
  display: grid;
  gap: 24px;
}

.ask-form {
  display: grid;
  gap: 16px;
}

.submit-btn {
  justify-self: end;
  width: fit-content;
  min-width: 140px;
}

.form-label {
  display: grid;
  gap: 8px;
  font-weight: 600;
  font-size: 0.9rem;
}

.settings-panel {
  padding: 18px;
}

.settings-form {
  display: grid;
  gap: 20px;
  margin-top: 14px;
}

.setting-item {
  display: flex;
  flex-direction: column;
}

.setting-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.setting-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--ink);
}

.setting-val {
  font-family: "JetBrains Mono", monospace;
  font-size: 0.85rem;
  font-weight: 700;
  background: var(--surface-muted);
  border: 1px solid var(--border);
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--primary);
}

.setting-desc {
  font-size: 0.76rem;
  color: var(--muted);
  margin: 4px 0 8px 0;
  line-height: 1.3;
}

.slider-input {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 4px;
  border-radius: 999px;
  background: var(--border-strong);
  outline: none;
  cursor: pointer;
  margin: 8px 0;
}

.slider-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--primary);
  border: 2px solid var(--bg);
  box-shadow: 0 0 8px var(--primary);
  cursor: pointer;
  transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.slider-input::-webkit-slider-thumb:hover {
  transform: scale(1.25);
  box-shadow: 0 0 12px var(--primary);
}

.slider-input::-moz-range-thumb {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--primary);
  border: 2px solid var(--bg);
  box-shadow: 0 0 8px var(--primary);
  cursor: pointer;
  transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.slider-input::-moz-range-thumb:hover {
  transform: scale(1.25);
  box-shadow: 0 0 12px var(--primary);
}

.no-sources {
  padding: 12px;
  background-color: rgba(220, 38, 38, 0.1);
  border: 1px solid var(--danger);
  border-radius: var(--radius-sm);
  color: var(--danger);
  font-size: 0.9rem;
}

@media (max-width: 900px) {
  .ask-grid {
    grid-template-columns: 1fr;
  }
}
</style>
