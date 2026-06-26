<script setup lang="ts">
import type { RagQuery } from '~/types/api'
import { formatDuration } from '~/utils/format'

const props = defineProps<{
  queries: RagQuery[]
}>()

// Use the last 15 queries in chronological order
const chartQueries = computed(() => {
  return [...props.queries]
    .slice(0, 15)
    .reverse()
})

const hoveredIndex = ref<number | null>(null)
const hoveredQuery = computed(() => {
  if (hoveredIndex.value === null) return null
  return chartQueries.value[hoveredIndex.value]
})

// SVG Dimensions
const width = 600
const height = 240
const padding = { top: 20, right: 40, bottom: 40, left: 45 }

const chartWidth = width - padding.left - padding.right
const chartHeight = height - padding.top - padding.bottom

// Helper calculations
const maxTokens = computed(() => {
  const values = chartQueries.value.map(q => (q.prompt_tokens || 0) + (q.completion_tokens || 0))
  const max = Math.max(...values, 100) // minimum scale of 100 tokens
  return Math.ceil(max / 100) * 100 // round up to nearest 100
})

const maxLatency = computed(() => {
  const values = chartQueries.value.map(q => q.latency_ms || 0)
  const max = Math.max(...values, 1000) // minimum scale of 1s
  return Math.ceil(max / 1000) * 1000 // round up to nearest 1s
})

const getX = (index: number) => {
  if (chartQueries.value.length <= 1) return padding.left + chartWidth / 2
  return padding.left + (index / Math.max(1, chartQueries.value.length - 1)) * chartWidth
}

// Map tokens to Y coordinate (Left axis)
const getTokensY = (tokens: number) => {
  return padding.top + chartHeight - (tokens / maxTokens.value) * chartHeight
}

// Map latency to Y coordinate (Right axis)
const getLatencyY = (latency: number) => {
  return padding.top + chartHeight - (latency / maxLatency.value) * chartHeight
}

// Generate path for Latency Line
const latencyPath = computed(() => {
  if (chartQueries.value.length === 0) return ''
  return chartQueries.value
    .map((q, index) => {
      const x = getX(index)
      const y = getLatencyY(q.latency_ms || 0)
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(' ')
})
</script>

<template>
  <div class="chart-container">
    <div v-if="chartQueries.length === 0" class="chart-empty">
      No recent query metrics to display.
    </div>

    <div v-else class="chart-wrapper">
      <!-- Legends -->
      <div class="chart-legend" aria-label="Chart legends">
        <span class="legend-item"><span class="legend-color prompt"></span>Prompt Tokens</span>
        <span class="legend-item"><span class="legend-color completion"></span>Completion Tokens</span>
        <span class="legend-item"><span class="legend-color latency"></span>Latency</span>
      </div>

      <svg :viewBox="`0 0 ${width} ${height}`" class="svg-chart">
        <!-- Grid lines (Horizontal, relative to tokens) -->
        <g class="grid-lines">
          <line 
            v-for="tick in [0, 0.25, 0.5, 0.75, 1]" 
            :key="tick"
            :x1="padding.left" 
            :y1="padding.top + tick * chartHeight" 
            :x2="width - padding.right" 
            :y2="padding.top + tick * chartHeight" 
          />
        </g>

        <!-- Left Y Axis Labels (Tokens) -->
        <g class="axis-labels y-labels">
          <text 
            v-for="tick in [0, 0.25, 0.5, 0.75, 1]" 
            :key="tick"
            :x="padding.left - 10" 
            :y="padding.top + (1 - tick) * chartHeight + 4" 
            text-anchor="end"
          >
            {{ Math.round(tick * maxTokens) }}
          </text>
        </g>

        <!-- Right Y Axis Labels (Latency) -->
        <g class="axis-labels y-labels latency-labels">
          <text 
            v-for="tick in [0, 0.5, 1]" 
            :key="tick"
            :x="width - padding.right + 10" 
            :y="padding.top + (1 - tick) * chartHeight + 4" 
            text-anchor="start"
          >
            {{ ((tick * maxLatency) / 1000).toFixed(1) }}s
          </text>
        </g>

        <!-- X Axis Labels -->
        <g class="axis-labels x-labels">
          <text
            v-for="(q, index) in chartQueries"
            :key="q.id"
            :x="getX(index)"
            :y="height - padding.bottom + 22"
            text-anchor="middle"
            class="x-label-text"
          >
            #{{ q.id }}
          </text>
        </g>

        <!-- Stacked Bar Charts for Tokens -->
        <g class="chart-bars">
          <g v-for="(q, index) in chartQueries" :key="'bar-' + q.id">
            <!-- Prompt tokens bar (bottom part of stacked bar) -->
            <rect
              :x="getX(index) - 6"
              :y="getTokensY(q.prompt_tokens || 0)"
              :width="12"
              :height="Math.max(0, getTokensY(0) - getTokensY(q.prompt_tokens || 0))"
              class="bar-rect prompt"
            />
            <!-- Completion tokens bar (top part of stacked bar) -->
            <rect
              :x="getX(index) - 6"
              :y="getTokensY((q.prompt_tokens || 0) + (q.completion_tokens || 0))"
              :width="12"
              :height="Math.max(0, getTokensY(q.prompt_tokens || 0) - getTokensY((q.prompt_tokens || 0) + (q.completion_tokens || 0)))"
              class="bar-rect completion"
            />
          </g>
        </g>

        <!-- Latency Line Overlaid -->
        <g class="chart-paths">
          <path :d="latencyPath" class="path-line latency" />
        </g>

        <!-- Interactive dots & hover triggers -->
        <g class="interactive-dots">
          <!-- Hover line indicator -->
          <line
            v-if="hoveredIndex !== null"
            :x1="getX(hoveredIndex)"
            :y1="padding.top"
            :x2="getX(hoveredIndex)"
            :y2="height - padding.bottom"
            class="hover-line"
          />

          <g v-for="(q, index) in chartQueries" :key="'dots-' + q.id">
            <!-- Latency dot indicator -->
            <circle
              :cx="getX(index)"
              :cy="getLatencyY(q.latency_ms || 0)"
              r="4"
              class="dot-circle latency"
              :class="{ active: hoveredIndex === index }"
            />

            <!-- Hidden interactive hover area over each column -->
            <rect
              :x="getX(index) - (chartWidth / Math.max(1, chartQueries.length - 1)) / 2"
              :y="padding.top"
              :width="chartWidth / Math.max(1, chartQueries.length - 1)"
              :height="chartHeight"
              fill="transparent"
              class="hover-trigger"
              @mouseenter="hoveredIndex = index"
              @mouseleave="hoveredIndex = null"
            />
          </g>
        </g>
      </svg>

      <!-- Tooltip overlay -->
      <div 
        v-if="hoveredQuery" 
        class="chart-tooltip"
      >
        <div class="tooltip-title">Query #{{ hoveredQuery.id }}</div>
        <div class="tooltip-question">"{{ hoveredQuery.question.substring(0, 45) }}{{ hoveredQuery.question.length > 45 ? '...' : '' }}"</div>
        <div class="tooltip-grid">
          <div class="tooltip-cell">
            <span class="indicator prompt"></span>
            <span>Prompt: <strong>{{ hoveredQuery.prompt_tokens ?? 0 }} tokens</strong></span>
          </div>
          <div class="tooltip-cell">
            <span class="indicator completion"></span>
            <span>Completion: <strong>{{ hoveredQuery.completion_tokens ?? 0 }} tokens</strong></span>
          </div>
          <div class="tooltip-cell">
            <span class="indicator latency"></span>
            <span>Latency: <strong>{{ formatDuration(hoveredQuery.latency_ms) }}</strong></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-container {
  width: 100%;
  position: relative;
}

.chart-empty {
  height: 240px;
  display: grid;
  place-items: center;
  color: var(--muted);
  background: var(--surface-muted);
  border-radius: var(--radius);
  border: 1px dashed var(--border);
}

.chart-wrapper {
  position: relative;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
}

.chart-legend {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  font-size: 0.78rem;
  margin-bottom: 8px;
  color: var(--muted);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  width: 10px;
  height: 10px;
  border-radius: var(--radius);
  display: inline-block;
}

.legend-color.prompt, .indicator.prompt { background: oklch(0.55 0.15 230); }
.legend-color.completion, .indicator.completion { background: oklch(0.6 0.13 160); }
.legend-color.latency, .indicator.latency { background: oklch(0.55 0.20 300); }

.svg-chart {
  width: 100%;
  height: auto;
  overflow: visible;
}

.grid-lines line {
  stroke: var(--border);
  stroke-dasharray: 4 4;
  stroke-width: 1px;
}

.axis-labels {
  font-size: 0.72rem;
  fill: var(--muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.latency-labels text {
  fill: oklch(0.55 0.20 300);
}

.x-label-text {
  font-size: 0.68rem;
}

.bar-rect {
  transition: opacity 120ms ease;
}

.bar-rect.prompt {
  fill: oklch(0.55 0.15 230 / 0.8);
}

.bar-rect.completion {
  fill: oklch(0.6 0.13 160 / 0.85);
}

.path-line.latency {
  fill: none;
  stroke: oklch(0.55 0.20 300);
  stroke-width: 2px;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.dot-circle.latency {
  fill: var(--surface);
  stroke: oklch(0.55 0.20 300);
  stroke-width: 2px;
  transition: r 120ms ease;
}

.dot-circle.latency.active {
  r: 6px;
  fill: oklch(0.55 0.20 300);
}

.hover-line {
  stroke: var(--muted);
  stroke-dasharray: 2 2;
  stroke-width: 1px;
  opacity: 0.65;
}

.hover-trigger {
  cursor: pointer;
}

.chart-tooltip {
  position: absolute;
  top: 48px;
  left: 65px;
  background: var(--surface-muted);
  color: var(--ink);
  border: 1px solid var(--border-strong);
  padding: 10px 14px;
  border-radius: var(--radius);
  font-size: 0.78rem;
  pointer-events: none;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 180px;
}

.tooltip-title {
  font-weight: 700;
}

.tooltip-question {
  color: oklch(0.8 0 0);
  font-style: italic;
  font-size: 0.72rem;
  margin-bottom: 4px;
}

.tooltip-grid {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tooltip-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.indicator {
  width: 6px;
  height: 6px;
  border-radius: 999px;
}
</style>
