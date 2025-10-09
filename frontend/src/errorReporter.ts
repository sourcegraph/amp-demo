export interface ErrorReportPayload {
  readonly error: unknown
  readonly info?: unknown
  readonly context?: Record<string, unknown>
}

export function reportError(payload: ErrorReportPayload): void {
  if (import.meta.env.DEV) {
    console.error('Error reported:', payload)
  }
}
