<script setup lang="ts">
import type { AskResponse } from '~/types/api'
import { formatDuration } from '~/utils/format'

const question = ref('What is the resignation notice period?')
const topK = ref(3)
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
        <p class="section-kicker">Ask Console</p>
        <h1>Test retrieval and answer generation</h1>
        <p>Send a question through the same RAG path used by evaluation runs.</p>
      </div>
    </header>

    <section class="panel ask-panel">
      <form class="ask-form" @submit.prevent="askQuestion">
        <label>
          <span>Question</span>
          <textarea v-model="question" rows="4" placeholder="Ask about an HR policy"></textarea>
        </label>

        <label>
          <span>Retrieved chunks</span>
          <input v-model.number="topK" type="number" min="1" max="10" />
        </label>

        <button class="button primary" type="submit" :disabled="pending || !question.trim()">
          {{ pending ? 'Running...' : 'Run RAG answer' }}
        </button>
      </form>
    </section>

    <section v-if="errorMessage" class="alert-panel">{{ errorMessage }}</section>

    <section v-if="answer" class="panel">
      <div class="panel-header">
        <div>
          <h2>Answer</h2>
          <p>{{ formatDuration(answer.latency_ms) }} / prompt {{ answer.prompt_tokens ?? 'n/a' }} / completion {{ answer.completion_tokens ?? 'n/a' }}</p>
        </div>
      </div>

      <div class="answer-block">{{ answer.answer }}</div>

      <div class="source-list">
        <h3>Sources</h3>
        <div v-for="source in answer.sources" :key="source.chunk_id" class="source-row">
          <strong>{{ source.document }}</strong>
          <span>Page {{ source.page_number ?? 'unknown' }} / score {{ source.score }}</span>
        </div>
      </div>
    </section>
  </div>
</template>
