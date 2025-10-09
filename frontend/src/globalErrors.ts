/* eslint-disable no-undef */
import { reportError } from './errorReporter'

export function installGlobalHandlers(): void {
  window.onerror = (message, source, lineno, colno, error): void => {
    reportError({
      error,
      context: {
        message,
        source,
        lineno,
        colno,
        url: window.location.href,
        userAgent: navigator.userAgent,
      },
    })
  }

  window.onunhandledrejection = (event: PromiseRejectionEvent): void => {
    reportError({
      error: event.reason,
      context: {
        url: window.location.href,
        userAgent: navigator.userAgent,
      },
    })
  }
}
