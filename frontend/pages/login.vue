<script setup lang="ts">
// Disable default layout for login page
definePageMeta({
  layout: false
})

const username = ref('')
const password = ref('')
const errorMessage = ref('')
const pending = ref(false)

const handleLogin = async () => {
  errorMessage.value = ''
  pending.value = true
  
  try {
    const data = await $fetch<{ token: string }>(useApiUrl('/login/'), {
      method: 'POST',
      body: {
        username: username.value,
        password: password.value
      }
    })
    
    // Save token to cookie
    const tokenCookie = useCookie('auth_token', {
      maxAge: 60 * 60 * 24 * 7, // 1 week
      path: '/'
    })
    tokenCookie.value = data.token
    
    // Redirect to home overview
    await navigateTo('/')
  } catch (error: any) {
    if (error.response && error.response.status === 400) {
      errorMessage.value = 'Invalid username or password.'
    } else {
      errorMessage.value = 'Failed to connect to API server. Ensure backend is running.'
    }
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="login-brand">
        <span class="brand-mark">VR</span>
        <div>
          <strong>Veridical RAG</strong>
          <small>AI Quality Observability Portal</small>
        </div>
      </div>

      <div class="login-intro">
        <h2>Console Authentication</h2>
        <p>Access quality evaluation reports, trace playgrounds, and observability trends.</p>
      </div>

      <div v-if="errorMessage" class="alert-panel login-error">
        {{ errorMessage }}
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <label>
          <span class="label-desc">Username</span>
          <input 
            v-model="username" 
            type="text" 
            required 
            placeholder="Enter username" 
            class="text-input"
            :disabled="pending"
          />
        </label>

        <label>
          <span class="label-desc">Password</span>
          <input 
            v-model="password" 
            type="password" 
            required 
            placeholder="Enter password" 
            class="text-input"
            :disabled="pending"
          />
        </label>

        <button type="submit" class="button primary submit-btn" :disabled="pending || !username.trim() || !password.trim()">
          {{ pending ? 'Authenticating...' : 'Sign In' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style>
/* Load global fonts and root styles for the login page */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

.login-wrapper {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background-color: #090a0f;
  color: #ffffff;
  font-family: "Inter", ui-sans-serif, system-ui, -apple-system, sans-serif;
  padding: 20px;
}

.login-card {
  background-color: #12131a;
  border: 1px solid #1e2130;
  border-radius: 12px;
  width: 100%;
  max-width: 420px;
  padding: 32px;
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;
}

.brand-mark {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: 4px;
  background: #1a1c26;
  border: 1px solid #2d3142;
  color: #00f5d4;
  font-family: "JetBrains Mono", monospace;
  font-weight: 700;
  font-size: 0.95rem;
}

.login-brand strong {
  display: block;
  font-size: 1.05rem;
  font-weight: 700;
  color: #ffffff;
}

.login-brand small {
  display: block;
  color: #8f95b2;
  font-size: 0.8rem;
}

.login-intro h2 {
  margin: 0 0 6px;
  font-size: 1.25rem;
  font-weight: 700;
  color: #ffffff;
}

.login-intro p {
  margin: 0 0 24px;
  color: #8f95b2;
  font-size: 0.88rem;
  line-height: 1.45;
}

.login-form {
  display: grid;
  gap: 16px;
}

.label-desc {
  display: block;
  font-weight: 600;
  margin-bottom: 6px;
  font-size: 0.85rem;
  color: #ffffff;
}

.text-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #2d3142;
  border-radius: 6px;
  font-size: 0.95rem;
  background-color: #1a1c26;
  color: #ffffff;
  box-sizing: border-box;
}

.text-input:focus {
  outline: none;
  border-color: #00d4ff;
  background-color: #12131a;
}

.submit-btn {
  margin-top: 10px;
  width: 100%;
}

.login-error {
  margin-bottom: 20px;
}
</style>
