/* eslint-disable no-undef */
import { Category, DeliveryOption, Product } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

let lastTraceparent: string | null = null
let lastRequestId: string | null = null

const RETRYABLE_CODES = new Set([
  'CONFLICT.VERSION_MISMATCH',
  'RATE_LIMIT.EXCEEDED',
  'SERVER.INTERNAL_ERROR',
  'SERVER.BAD_GATEWAY',
  'SERVER.UNAVAILABLE',
  'SERVER.GATEWAY_TIMEOUT',
])

interface ProblemDetails {
  readonly type?: string
  readonly title: string
  readonly status: number
  readonly detail: string
  readonly instance?: string
  readonly code?: string
  readonly request_id?: string
  readonly trace_id?: string
  readonly details?: Record<string, unknown>
}

function genHex(bytes: number): string {
  const arr = crypto.getRandomValues(new Uint8Array(bytes))
  return Array.from(arr)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

function newTraceparent(): string {
  const traceId = genHex(16)
  const spanId = genHex(8)
  return `00-${traceId}-${spanId}-01`
}

function jitteredDelay(ms: number): number {
  const jitter = 0.25
  const delta = ms * jitter
  const min = ms - delta
  const max = ms + delta
  return Math.floor(min + Math.random() * (max - min))
}

async function parseProblem(resp: Response): Promise<ProblemDetails> {
  const ct = resp.headers.get('Content-Type') || ''
  if (ct.includes('application/problem+json')) {
    try {
      return (await resp.json()) as ProblemDetails
    } catch {
      // fallthrough
    }
  }
  return {
    type: 'about:blank',
    title: resp.statusText || 'Error',
    status: resp.status,
    detail: 'Request failed',
    instance: resp.url,
    code: undefined,
    request_id: resp.headers.get('X-Request-ID') || undefined,
    trace_id: undefined,
  }
}

function captureTraceHeaders(resp: Response): void {
  lastTraceparent = resp.headers.get('traceparent')
  lastRequestId = resp.headers.get('X-Request-ID')
}

function isRetryable(problem: ProblemDetails, status: number): boolean {
  if (problem?.code && RETRYABLE_CODES.has(problem.code)) return true
  return [502, 503, 504].includes(status)
}

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    let attempt = 0
    let delay = 100
    const maxDelay = 5000
    const maxAttempts = 3

    while (true) {
      attempt += 1
      const tp = newTraceparent()

      try {
        const resp = await fetch(`${API_BASE_URL}${endpoint}`, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            traceparent: tp,
            ...(options.headers || {}),
          },
        })

        captureTraceHeaders(resp)

        if (resp.ok) {
          const ct = resp.headers.get('Content-Type') || ''
          return ct.includes('application/json')
            ? ((await resp.json()) as T)
            : (undefined as unknown as T)
        }

        const problem = await parseProblem(resp)

        if (resp.status === 401) {
          window.location.href = '/login'
          throw problem
        }
        if (resp.status === 403) {
          throw problem
        }

        if (attempt < maxAttempts && isRetryable(problem, resp.status)) {
          await new Promise((res) => setTimeout(res, jitteredDelay(Math.min(delay, maxDelay))))
          delay = Math.min(delay * 2, maxDelay)
          continue
        }

        const err = new Error(problem.title || `HTTP ${resp.status}`)
        ;(err as Error & { problem?: ProblemDetails; request_id?: string }).problem = problem
        ;(err as Error & { problem?: ProblemDetails; request_id?: string }).request_id =
          lastRequestId || undefined
        throw err
      } catch (e: unknown) {
        if (
          e instanceof Error &&
          'problem' in e &&
          (e as Error & { problem?: ProblemDetails }).problem
        ) {
          throw e
        }
        if (attempt < maxAttempts) {
          await new Promise((res) => setTimeout(res, jitteredDelay(Math.min(delay, maxDelay))))
          delay = Math.min(delay * 2, maxDelay)
          continue
        }
        ;(e as Error & { request_id?: string }).request_id = lastRequestId || undefined
        throw e
      }
    }
  }

  async getCategories(): Promise<Category[]> {
    return this.request<Category[]>('/api/categories')
  }

  async getDeliveryOptions(): Promise<DeliveryOption[]> {
    return this.request<DeliveryOption[]>('/api/delivery-options')
  }

  async getProducts(params: {
    categoryId?: string
    deliveryOptionId?: string
    sort?: string
  } = {}): Promise<Product[]> {
    const searchParams = new URLSearchParams()
    if (params.categoryId) searchParams.set('categoryId', params.categoryId)
    if (params.deliveryOptionId) searchParams.set('deliveryOptionId', params.deliveryOptionId)
    if (params.sort) searchParams.set('sort', params.sort)

    return this.request<Product[]>(`/api/products?${searchParams.toString()}`)
  }
}

export const api = new ApiClient()
export function getLastCorrelation(): { traceparent: string | null; request_id: string | null } {
  return { traceparent: lastTraceparent, request_id: lastRequestId }
}
