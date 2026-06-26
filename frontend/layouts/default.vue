<script setup lang="ts">
const handleLogout = () => {
  const token = useCookie('auth_token')
  token.value = null
  navigateTo('/login')
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar" aria-label="Primary navigation">
      <NuxtLink class="brand" to="/">
        <span class="brand-mark">VR</span>
        <span>
          <strong>Veridical RAG</strong>
          <small>HR Policy Evaluation</small>
        </span>
      </NuxtLink>

      <nav class="nav-list">
        <NuxtLink to="/" class="nav-link">
          <span class="nav-icon" aria-hidden="true">⌁</span>
          Overview
        </NuxtLink>
        <NuxtLink to="/evaluations" class="nav-link">
          <span class="nav-icon" aria-hidden="true">▦</span>
          Evaluations
        </NuxtLink>
        <NuxtLink to="/regression" class="nav-link">
          <span class="nav-icon" aria-hidden="true">⇄</span>
          Regression
        </NuxtLink>
        <NuxtLink to="/ask" class="nav-link">
          <span class="nav-icon" aria-hidden="true">?</span>
          Ask Console
        </NuxtLink>
        
        <button @click="handleLogout" class="nav-link logout-btn">
          <span class="nav-icon" aria-hidden="true">⎋</span>
          Logout
        </button>
      </nav>

      <div class="sidebar-status">
        <span class="status-dot"></span>
        <span>Django API: local</span>
      </div>
    </aside>

    <main class="main-panel">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.logout-btn {
  background: none;
  border: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
}
</style>
