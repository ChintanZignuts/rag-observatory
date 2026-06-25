<script setup lang="ts">
import type { EvaluationRunSummary } from '~/types/api'
import { formatScore, formatDateTime } from '~/utils/format'

const props = defineProps<{
  runs: EvaluationRunSummary[]
}>()

// Reverse runs to show chronologically from left to right
const chronologicalRuns = computed(() => {
  return [...props.runs]
    .filter(r => r.status === 'completed')
    .reverse()
})

const hoveredIndex = ref<number | null>(null)
const hoveredRun = computed(() => {
  if (hoveredIndex.value === null) return null
  return chronologicalRuns.value[hoveredIndex.value]
})

// SVG dimensions
const width = 600
const height = 240
const padding = { top: 20, right: 30, bottom: 40, left: 45 }

const chartWidth = width - padding.left - padding.right
const chartHeight = height - padding.top - padding.bottom

// Coordinate conversion helpers
const getX = (index: number) => {
  if (chronologicalRuns.value.length <= 1) return padding.left + chartWidth / 2
  return padding.left + (index / (chronologicalRuns.value.length - 1)) * chartWidth
}

const getY = (score: number | null) => {
  const value = score !== null ? score : 0
  // Ragas scores are 0.0 to 1.0, map to height
  return padding.top + chartHeight - value * chartHeight
}

// Generate SVG path for a specific metric
const getPathData = (key: 'average_context_precision' | 'average_faithfulness' | 'average_answer_relevance') => {
  if (chronologicalRuns.value.length === 0) return ''
  return chronologicalRuns.value
    .map((run, index) => {
      const x = getX(index)
      const y = getY(run[key])
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(' ')
}

const precisionPath = computed(() => getPathData('average_context_precision'))
const faithfulnessPath = computed(() => getPathData('average_faithfulness'))
const relevancePath = computed(() => getPathData('average_answer_relevance'))
</script>

<template>
  <div class="chart-container">
    <div v-if="chronologicalRuns.length === 0" class="chart-empty">
      No completed evaluation runs to display.
    </div>
    
    <div v-else class="chart-wrapper">
      <!-- Legends -->
      <div class="chart-legend" aria-label="Chart legends">
        <span class="legend-item"><span class="legend-color precision"></span>Context Precision</span>
        <span class="legend-item"><span class="legend-color faithfulness"></span>Faithfulness</span>
        <span class="legend-item"><span class="legend-color relevance"></span>Answer Relevance</span>
      </div>

      <svg :viewBox="`0 0 ${width} ${height}`" class="svg-chart">
        <!-- Grid lines -->
        <g class="grid-lines">
          <line 
            v-for="tick in [0, 0.25, 0.5, 0.75, 1]" 
            :key="tick"
            :x1="padding.left" 
            :y1="getY(tick)" 
            :x2="width - padding.right" 
            :y2="getY(tick)" 
          />
        </g>

        <!-- Y Axis Labels -->
        <g class="axis-labels y-labels">
          <text 
            v-for="tick in [0, 0.25, 0.5, 0.75, 1]" 
            :key="tick"
            :x="padding.left - 10" 
            :y="getY(tick) + 4" 
            text-anchor="end"
          >
            {{ Math.round(tick * 100) }}%
          </text>
        </g>

        <!-- X Axis Labels (Runs name or dates) -->
        <g class="axis-labels x-labels">
          <text
            v-for="(run, index) in chronologicalRuns"
            :key="run.id"
            :x="getX(index)"
            :y="height - padding.bottom + 22"
            text-anchor="middle"
            class="x-label-text"
          >
            Run #{{ run.id }}
          </text>
        </g>

        <!-- Value Lines -->
        <g class="chart-paths">
          <path :d="precisionPath" class="path-line precision" />
          <path :d="faithfulnessPath" class="path-line faithfulness" />
          <path :d="relevancePath" class="path-line relevance" />
        </g>

        <!-- Interactive hover regions and dots -->
        <g class="interactive-dots">
          <!-- Hover vertical line indicator -->
          <line
            v-if="hoveredIndex !== null"
            :x1="getX(hoveredIndex)"
            :y1="padding.top"
            :x2="getX(hoveredIndex)"
            :y2="height - padding.bottom"
            class="hover-line"
          />

          <!-- Dots for each point -->
          <g v-for="(run, index) in chronologicalRuns" :key="'dots-' + run.id">
            <!-- Context precision dot -->
            <circle
              :cx="getX(index)"
              :cy="getY(run.average_context_precision)"
              r="4"
              class="dot-circle precision"
              :class="{ active: hoveredIndex === index }"
            />
            <!-- Faithfulness dot -->
            <circle
              :cx="getX(index)"
              :cy="getY(run.average_faithfulness)"
              r="4"
              class="dot-circle faithfulness"
              :class="{ active: hoveredIndex === index }"
            />
            <!-- Relevance dot -->
            <circle
              :cx="getX(index)"
              :cy="getY(run.average_answer_relevance)"
              r="4"
              class="dot-circle relevance"
              :class="{ active: hoveredIndex === index }"
            />

            <!-- Hidden interactive hover area over each point position -->
            <rect
              :x="getX(index) - (chartWidth / Math.max(1, chronologicalRuns.length - 1)) / 2"
              :y="padding.top"
              :width="chartWidth / Math.max(1, chronologicalRuns.length - 1)"
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
        v-if="hoveredRun" 
        class="chart-tooltip"
      >
        <div class="tooltip-title">{{ hoveredRun.name }}</div>
        <div class="tooltip-date">{{ formatDateTime(hoveredRun.completed_at) }}</div>
        <div class="tooltip-grid">
          <div class="tooltip-cell">
            <span class="indicator precision"></span>
            <span>Precision: <strong>{{ formatScore(hoveredRun.average_context_precision) }}</strong></span>
          </div>
          <div class="tooltip-cell">
            <span class="indicator faithfulness"></span>
            <span>Faithfulness: <strong>{{ formatScore(hoveredRun.average_faithfulness) }}</strong></span>
          </div>
          <div class="tooltip-cell">
            <span class="indicator relevance"></span>
            <span>Relevance: <strong>{{ formatScore(hoveredRun.average_answer_relevance) }}</strong></span>
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
  border-radius: 999px;
  display: inline-block;
}

.legend-color.precision, .indicator.precision { background: var(--primary); }
.legend-color.faithfulness, .indicator.faithfulness { background: var(--success); }
.legend-color.relevance, .indicator.relevance { background: var(--warning); }

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

.x-label-text {
  font-size: 0.68rem;
}

.path-line {
  fill: none;
  stroke-width: 2.5px;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.path-line.precision { stroke: var(--primary); }
.path-line.faithfulness { stroke: var(--success); }
.path-line.relevance { stroke: var(--warning); }

.dot-circle {
  fill: white;
  stroke-width: 2px;
  transition: r 120ms ease;
}

.dot-circle.precision { stroke: var(--primary); }
.dot-circle.faithfulness { stroke: var(--success); }
.dot-circle.relevance { stroke: var(--warning); }

.dot-circle.active {
  r: 6px;
  fill: inherit;
}

.dot-circle.precision.active { fill: var(--primary); }
.dot-circle.faithfulness.active { fill: var(--success); }
.dot-circle.relevance.active { fill: var(--warning); }

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
  background: var(--ink);
  color: white;
  padding: 10px 14px;
  border-radius: var(--radius);
  font-size: 0.78rem;
  box-shadow: var(--shadow);
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

.tooltip-date {
  color: oklch(0.8 0 0);
  font-size: 0.68rem;
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
