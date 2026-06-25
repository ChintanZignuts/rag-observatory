<script setup lang="ts">
defineProps<{
  status: string
}>()
</script>

<template>
  <span class="run-status" :data-status="status">
    {{ status }}
  </span>
</template>
