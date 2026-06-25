export const useApiBase = () => {
  const config = useRuntimeConfig()
  return config.public.apiBase
}

export const useApiUrl = (path: string) => {
  const base = useApiBase().replace(/\/$/, '')
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${base}${normalizedPath}`
}
