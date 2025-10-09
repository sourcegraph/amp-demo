import { getLastCorrelation } from '../api/client'

interface ProblemDetails {
  readonly status?: number
  readonly request_id?: string
  readonly code?: string
}

export function formatUserError(action: string, problem?: ProblemDetails): string {
  const rid = problem?.request_id || getLastCorrelation().request_id || ''
  const next = (() => {
    if (problem?.status === 401) return 'Please log in again.'
    if (problem?.status === 403) return "You don't have permission to perform this action."
    if (problem?.status === 429) return 'Please wait a moment and try again.'
    return 'Please try again or contact support'
  })()
  const suffix = rid ? ` with Request ID: ${rid}` : ''
  return `${action} failed. ${next}${suffix ? ' ' + suffix : ''}`
}
