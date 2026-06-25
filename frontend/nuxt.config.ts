export default defineNuxtConfig({
  compatibilityDate: '2026-06-19',
  devtools: { enabled: true },
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      // @ts-ignore
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000/api',
    },
  },
})
