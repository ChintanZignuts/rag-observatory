<script setup lang="ts">
const props = defineProps<{
  label: string
  value: number | null
}>()

const percent = computed(() => {
  if (props.value === null || Number.isNaN(props.value)) return 0
  return Math.round(Math.max(0, Math.min(1, props.value)) * 100)
})
</script>

<template>
  <div class="score-bar">
    <div class="score-bar-header">
      <span>{{ label }}</span>
      <strong>{{ value === null ? 'Pending' : `${percent}%` }}</strong>
    </div>
    <div class="score-track">
      <span :style="{ width: `${percent}%` }"></span>
    </div>
  </div>
</template>
