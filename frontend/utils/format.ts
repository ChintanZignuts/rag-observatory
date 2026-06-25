export const formatDateTime = (value: string | null | undefined) => {
  if (!value) return 'Not available'
  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export const formatScore = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) return 'Pending'
  return `${Math.round(value * 100)}%`
}

export const formatDuration = (milliseconds: number | null | undefined) => {
  if (!milliseconds) return 'Not measured'
  if (milliseconds < 1000) return `${milliseconds} ms`
  return `${(milliseconds / 1000).toFixed(1)} s`
}
