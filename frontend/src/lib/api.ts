// If served behind the same origin (recommended on VPS), leave VITE_API_BASE empty
// and use relative URLs so we avoid CORS/mixed-content issues.
export const API_BASE = (import.meta as any).env?.VITE_API_BASE || ''

export function getToken(): string | null {
  return localStorage.getItem('access_token')
}

export function setToken(token: string) {
  localStorage.setItem('access_token', token)
}

export function clearToken() {
  localStorage.removeItem('access_token')
}

async function request<T>(
  path: string,
  opts: RequestInit & { auth?: boolean } = {}
): Promise<T> {
  const headers = new Headers(opts.headers || {})
  headers.set('Content-Type', 'application/json')
  if (opts.auth) {
    const t = getToken()
    if (t) headers.set('Authorization', `Bearer ${t}`)
  }
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    headers
  })
  const text = await res.text()
  const body = text ? JSON.parse(text) : null
  if (!res.ok) {
    const detail = body?.detail || `HTTP ${res.status}`
    throw new Error(detail)
  }
  return body as T
}

export const api = {
  async health() {
    return request<{ status: string }>('/api/health')
  },
  async register(username: string, password: string) {
    return request<{ id: number; username: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    })
  },
  async login(username: string, password: string) {
    return request<{ access_token: string; token_type: string }>(
      '/api/auth/login',
      {
        method: 'POST',
        body: JSON.stringify({ username, password })
      }
    )
  },
  async listBots() {
    return request<
      Array<{
        id: number
        name: string
        description: string | null
        active_version_id: number | null
      }>
    >('/api/bots', { auth: true })
  },
  async createBot(name: string, description: string, code: string) {
    return request<{ id: number; name: string }>(`/api/bots`, {
      method: 'POST',
      auth: true,
      body: JSON.stringify({ name, description, code })
    })
  },
  async getBot(botId: string) {
    return request<{
      id: number
      name: string
      description: string | null
      active_version_id: number | null
      versions: Array<{ id: number; version_num: number; code: string }>
    }>(`/api/bots/${botId}`, { auth: true })
  },
  async createVersion(botId: string, code: string) {
    return request<{ id: number; version_num: number; code: string }>(
      `/api/bots/${botId}/versions`,
      { method: 'POST', auth: true, body: JSON.stringify({ code }) }
    )
  },
  async setActiveVersion(botId: string, versionId: number) {
    return request<{ id: number; active_version_id: number | null }>(
      `/api/bots/${botId}/active_version`,
      {
        method: 'POST',
        auth: true,
        body: JSON.stringify({ version_id: versionId })
      }
    )
  },
  async runTest(botId: string) {
    return request<{ match_id: number; cum_a: number; cum_b: number }>(
      `/api/bots/${botId}/run-test`,
      { method: 'POST', auth: true }
    )
  },
  async getMatch(matchId: number) {
    return request<{
      id: number
      env_id: string
      opponent_name: string
      seed: number
      status: string
      cum_a?: number
      cum_b?: number
      steps: Array<any>
    }>(`/api/matches/${matchId}`, { auth: true })
  }
}
