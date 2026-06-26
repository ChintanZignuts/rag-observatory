<script setup lang="ts">
import { formatDuration } from '~/utils/format'

const props = defineProps<{
  latencyMs: number | null | undefined
  promptTokens: number | null | undefined
  completionTokens: number | null | undefined
  langsmithTraceId: string | null | undefined
  langfuseTraceId: string | null | undefined
  langfuseProjectId: string | null | undefined
  langfuseHost: string | null | undefined
  sources: Array<{ document: string; page_number: number | null; score?: number }>
}>()

const copiedSmith = ref(false)
const copiedFuse = ref(false)

const copyId = async (text: string, type: 'smith' | 'fuse') => {
  try {
    await navigator.clipboard.writeText(text)
    if (type === 'smith') copiedSmith.value = true
    else copiedFuse.value = true
    setTimeout(() => {
      if (type === 'smith') copiedSmith.value = false
      else copiedFuse.value = false
    }, 1500)
  } catch (err) {
    console.error('Failed to copy ID', err)
  }
}

// Compute generic dashboard links
const langfuseLink = computed(() => {
  if (!props.langfuseProjectId) return '#'
  const host = props.langfuseHost || 'https://cloud.langfuse.com'
  return `${host}/project/${props.langfuseProjectId}/traces`
})

const langsmithLink = computed(() => {
  if (!props.langsmithTraceId) return '#'
  return `https://smith.langchain.com/projects`
})
</script>

<template>
  <div class="timeline-box">
    <h3 class="timeline-title">Dual Tracing & Execution Timeline</h3>
    
    <div class="timeline">
      <!-- 1. ENTRY POINT -->
      <div class="timeline-step active">
        <div class="step-marker">●</div>
        <div class="step-content">
          <div class="step-header">
            <span class="step-name">Chain Execution</span>
            <span class="step-meta duration">{{ formatDuration(latencyMs) }}</span>
          </div>
          <p class="step-desc">Overall RAG question-answering workflow lifecycle.</p>
        </div>
      </div>

      <!-- 2. RETRIEVAL -->
      <div class="timeline-step">
        <div class="step-marker">●</div>
        <div class="step-content">
          <div class="step-header">
            <span class="step-name">Context Retrieval</span>
            <span class="step-meta duration">{{ formatDuration(Math.round((latencyMs || 0) * 0.15)) }}</span>
          </div>
          <p class="step-desc">Queried local vector database embeddings for top relevant company policies.</p>
          
          <div v-if="sources.length > 0" class="step-sublist">
            <div v-for="(source, idx) in sources" :key="idx" class="sublist-item">
              <span class="sub-doc">📄 {{ source.document }} (Page {{ source.page_number ?? 'n/a' }})</span>
              <span class="sub-score" v-if="source.score">Score: {{ source.score }}</span>
            </div>
          </div>
          <div v-else class="step-sublist-empty">No source documents retrieved.</div>
        </div>
      </div>

      <!-- 3. GENERATION -->
      <div class="timeline-step">
        <div class="step-marker">●</div>
        <div class="step-content">
          <div class="step-header">
            <span class="step-name">LLM Generation</span>
            <span class="step-meta duration">{{ formatDuration(Math.round((latencyMs || 0) * 0.85)) }}</span>
          </div>
          <p class="step-desc">Generated final response using local Qwen model from context.</p>
          
          <div class="step-sublist tokens-sublist">
            <span class="token-tag">Prompt: {{ promptTokens ?? 'n/a' }} tokens</span>
            <span class="token-tag">Completion: {{ completionTokens ?? 'n/a' }} tokens</span>
            <span class="token-tag">Total: {{ (promptTokens || 0) + (completionTokens || 0) }} tokens</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Observability Links -->
    <div class="observability-panel">
      <!-- Langfuse Trace -->
      <div class="obs-item">
        <div class="obs-header">
          <span class="obs-badge langfuse">Langfuse</span>
          <span class="obs-status" :class="{ enabled: langfuseTraceId, disabled: !langfuseTraceId }">
            {{ langfuseTraceId ? 'Active' : 'Offline' }}
          </span>
        </div>
        <div class="obs-body">
          <div v-if="langfuseTraceId" class="obs-id-row">
            <code>{{ langfuseTraceId }}</code>
            <button class="icon-btn" @click="copyId(langfuseTraceId, 'fuse')" title="Copy ID">
              {{ copiedFuse ? '✓ Copied' : '⧉ Copy' }}
            </button>
          </div>
          <div v-else class="obs-missing-note">Set `LANGFUSE_PUBLIC_KEY` in `.env` to trace.</div>
          <a :href="langfuseLink" target="_blank" class="obs-link" :class="{ disabled: !props.langfuseProjectId }">
            Open Langfuse Traces ↗
          </a>
        </div>
      </div>

      <!-- LangSmith Trace -->
      <div class="obs-item">
        <div class="obs-header">
          <span class="obs-badge langsmith">LangSmith</span>
          <span class="obs-status" :class="{ enabled: langsmithTraceId, disabled: !langsmithTraceId }">
            {{ langsmithTraceId ? 'Active' : 'Offline' }}
          </span>
        </div>
        <div class="obs-body">
          <div v-if="langsmithTraceId" class="obs-id-row">
            <code>{{ langsmithTraceId }}</code>
            <button class="icon-btn" @click="copyId(langsmithTraceId, 'smith')" title="Copy ID">
              {{ copiedSmith ? '✓ Copied' : '⧉ Copy' }}
            </button>
          </div>
          <div v-else class="obs-missing-note">Set `LANGCHAIN_TRACING_V2=True` in `.env` to trace.</div>
          <a :href="langsmithLink" target="_blank" class="obs-link" :class="{ disabled: !langsmithTraceId }">
            Open LangSmith Project ↗
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline-box {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px;
}

.timeline-title {
  margin: 0 0 16px;
  font-size: 1.05rem;
}

.timeline {
  display: flex;
  flex-direction: column;
  position: relative;
  padding-left: 12px;
  margin-bottom: 22px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 16px;
  top: 10px;
  bottom: 10px;
  width: 2px;
  background: var(--border);
  z-index: 1;
}

.timeline-step {
  display: flex;
  position: relative;
  gap: 16px;
  padding-bottom: 20px;
  z-index: 2;
}

.timeline-step:last-child {
  padding-bottom: 0;
}

.step-marker {
  color: var(--muted);
  background: var(--surface);
  border-radius: 999px;
  font-size: 12px;
  width: 10px;
  height: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 5px;
  z-index: 3;
}

.timeline-step.active .step-marker {
  color: var(--primary);
  text-shadow: 0 0 8px var(--primary);
}

.step-content {
  flex-grow: 1;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.step-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.step-meta.duration {
  font-size: 0.76rem;
  color: var(--muted);
  font-family: ui-monospace, monospace;
}

.step-desc {
  margin: 4px 0 0;
  font-size: 0.78rem;
  color: var(--muted);
}

.step-sublist {
  margin-top: 10px;
  background: var(--surface-muted);
  border-radius: var(--radius);
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.step-sublist-empty {
  margin-top: 10px;
  font-size: 0.72rem;
  color: var(--muted);
  font-style: italic;
}

.sublist-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  font-size: 0.75rem;
}

.sub-doc {
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.sub-score {
  font-family: ui-monospace, monospace;
  color: var(--primary);
}

.tokens-sublist {
  flex-direction: row;
  justify-content: space-around;
  padding: 6px 10px;
}

.token-tag {
  font-size: 0.72rem;
  font-family: ui-monospace, monospace;
  color: var(--muted);
}

.observability-panel {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  border-top: 1px solid var(--border);
  padding-top: 18px;
}

.obs-item {
  background: var(--surface-muted);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  padding: 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.obs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.obs-badge {
  font-size: 0.78rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}

.obs-badge.langfuse {
  background: rgba(0, 212, 255, 0.12);
  color: #00d4ff;
  border: 1px solid rgba(0, 212, 255, 0.3);
}

.obs-badge.langsmith {
  background: rgba(0, 245, 212, 0.12);
  color: #00f5d4;
  border: 1px solid rgba(0, 245, 212, 0.3);
}

.obs-status {
  font-size: 0.72rem;
  font-weight: 600;
}

.obs-status.enabled {
  color: var(--success);
}

.obs-status.disabled {
  color: var(--muted);
}

.obs-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.obs-id-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 4px 6px;
  border-radius: 4px;
  font-size: 0.72rem;
}

.obs-id-row code {
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
  font-family: ui-monospace, monospace;
}

.icon-btn {
  background: none;
  border: none;
  color: var(--primary);
  cursor: pointer;
  padding: 2px;
  font-size: 0.72rem;
  font-weight: 600;
}

.icon-btn:hover {
  text-decoration: underline;
}

.obs-missing-note {
  font-size: 0.68rem;
  color: var(--muted);
  line-height: 1.3;
}

.obs-link {
  font-size: 0.78rem;
  color: var(--primary);
  text-decoration: none;
  font-weight: 600;
}

.obs-link:hover {
  text-decoration: underline;
}

.obs-link.disabled {
  opacity: 0.5;
  pointer-events: none;
}

@media (max-width: 640px) {
  .observability-panel {
    grid-template-columns: 1fr;
  }
}
</style>
