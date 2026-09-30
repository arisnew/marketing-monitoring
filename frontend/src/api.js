const TOKEN_KEY = 'mm_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json'
  }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(path, { ...options, headers })
  if (res.status === 401) {
    clearToken()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }
  if (res.status === 204) return null
  const text = await res.text()
  if (!text) return null
  const data = JSON.parse(text)
  if (!res.ok) {
    const detail = data.detail
    const msg = Array.isArray(detail)
      ? detail.map((d) => d.msg).join(', ')
      : detail || res.statusText
    throw new Error(msg)
  }
  return data
}

export const api = {
  login: (email, password) =>
    request('/api/v1/auth/login/json', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  me: () => request('/api/v1/auth/me'),
  dashboard: () => request('/api/v1/monitors/dashboard'),
  platforms: () => request('/api/v1/platforms'),
  createPlatform: (body) =>
    request('/api/v1/platforms', { method: 'POST', body: JSON.stringify(body) }),
  testPlatform: (platformId, params = { window_days: 7 }) =>
    request(`/api/v1/platforms/${platformId}/test`, {
      method: 'POST',
      body: JSON.stringify({ params }),
    }),
  rules: () => request('/api/v1/monitors/rules'),
  createRule: (body) =>
    request('/api/v1/monitors/rules', { method: 'POST', body: JSON.stringify(body) }),
  runs: (ruleId) => request(`/api/v1/monitors/rules/${ruleId}/runs`),
  dailyMetrics: (ruleId) => request(`/api/v1/monitors/rules/${ruleId}/metrics/daily`),
  runCheck: (ruleId) =>
    request(`/api/v1/monitors/rules/${ruleId}/run`, { method: 'POST' }),
  aggregateDaily: () => request('/api/v1/monitors/aggregate/daily', { method: 'POST' }),
  createUser: (body) =>
    request('/api/v1/auth/users', { method: 'POST', body: JSON.stringify(body) }),
}
