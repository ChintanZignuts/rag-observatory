import { ofetch } from 'ofetch'

export default defineNuxtPlugin((nuxtApp) => {
  const token = useCookie('auth_token')
  
  globalThis.$fetch = ofetch.create({
    onRequest({ options }) {
      if (token.value) {
        const headers = (options.headers || {}) as any
        if (headers instanceof Headers) {
          headers.set('Authorization', `Token ${token.value}`)
        } else if (Array.isArray(headers)) {
          headers.push(['Authorization', `Token ${token.value}`])
        } else {
          headers['Authorization'] = `Token ${token.value}`
        }
        options.headers = headers
      }
    },
    onResponseError({ response }) {
      if (response.status === 401) {
        token.value = null
        if (import.meta.client) {
          window.location.href = '/login'
        }
      }
    }
  }) as any
})
