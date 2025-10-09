import { test, expect } from '@playwright/test'

test.describe('Error Handling', () => {
  test('API requests include traceparent header', async ({ page }) => {
    const requestPromise = page.waitForRequest((request) => 
      request.url().includes('/api/products')
    )

    await page.goto('http://localhost:3001')
    const request = await requestPromise

    expect(request.headers()['traceparent']).toBeTruthy()
    const traceparent = request.headers()['traceparent']
    const parts = traceparent?.split('-')
    expect(parts).toHaveLength(4)
    expect(parts?.[0]).toBe('00')
  })

  test('API responses include trace headers', async ({ page }) => {
    const responsePromise = page.waitForResponse((response) =>
      response.url().includes('/api/products')
    )

    await page.goto('http://localhost:3001')
    const response = await responsePromise

    expect(response.headers()['x-request-id']).toBeTruthy()
    expect(response.headers()['traceparent']).toBeTruthy()
  })

  test('404 errors return RFC 7807 problem details', async ({ page }) => {
    const response = await page.request.get('http://localhost:8001/products/999999')

    expect(response.status()).toBe(404)
    expect(response.headers()['content-type']).toContain('application/problem+json')

    const body = await response.json()
    expect(body.type).toContain('https://docs.lineasupply.com/errors/')
    expect(body.status).toBe(404)
    expect(body.code).toBe('RESOURCE.NOT_FOUND')
    expect(body.request_id).toBeTruthy()
    expect(body.trace_id).toBeTruthy()
  })

  test('validation errors return RFC 7807 with field details', async ({ page }) => {
    const response = await page.request.post('http://localhost:8001/categories', {
      data: { invalid: 'data' },
    })

    expect(response.status()).toBe(400)
    expect(response.headers()['content-type']).toContain('application/problem+json')

    const body = await response.json()
    expect(body.code).toBe('VALIDATION.INVALID_FIELDS')
    expect(body.details).toBeTruthy()
    expect(body.details.fields).toBeTruthy()
    expect(Array.isArray(body.details.fields)).toBe(true)
  })

  test('conflict errors return 409 status', async ({ page }) => {
    await page.request.post('http://localhost:8001/categories', {
      data: { name: 'Duplicate Test Category' },
    })

    const response = await page.request.post('http://localhost:8001/categories', {
      data: { name: 'Duplicate Test Category' },
    })

    expect(response.status()).toBe(409)
    const body = await response.json()
    expect(body.code).toBe('CONFLICT.DUPLICATE')
  })
})
