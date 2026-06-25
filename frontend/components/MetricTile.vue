<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  detail?: string
  tone?: 'neutral' | 'good' | 'warn'
}>()
</script>

<template>
  <section class="metric-tile" :data-tone="tone || 'neutral'">
    <span class="metric-label">{{ label }}</span>
    <strong class="metric-value">{{ value }}</strong>
    <span v-if="detail" class="metric-detail">{{ detail }}</span>
  </section>
</template>
