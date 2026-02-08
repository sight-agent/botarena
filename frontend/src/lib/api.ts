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

export class ApiError extends Error {
  status: number
  detail: string
  body: any

  constructor(status: number, detail: string, body: any) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.body = body
  }
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
  let body: any = null
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    body = { raw: text }
  }

  if (!res.ok) {
    const detail = body?.detail || `HTTP ${res.status}`
    throw new ApiError(res.status, String(detail), body)
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
        env_id: string
        name: string
        description: string | null
        submitted: boolean
      }>
    >('/api/bots', { auth: true })
  },
  async createBot(envId: string, name: string, description: string, code: string) {
    return request<{ id: number; env_id: string; name: string }>(`/api/bots`, {
      method: 'POST',
      auth: true,
      body: JSON.stringify({ env_id: envId, name, description, code })
    })
  },
  async getBot(botId: string) {
    return request<{
      id: number
      env_id: string
      name: string
      description: string | null
      submitted: boolean
      code: string
    }>(`/api/bots/${botId}`, { auth: true })
  },
  async updateBotCode(botId: string, code: string) {
    return request<{ id: number; updated_at: string }>(`/api/bots/${botId}`, {
      method: 'PUT',
      auth: true,
      body: JSON.stringify({ code })
    })
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
  },
  async deleteBot(botId: number) {
    return request<{ ok: true }>(`/api/bots/${botId}`, {
      method: 'DELETE',
      auth: true
    })
  },
  // bot versions removed in MVP refactor
  async ipdLeaderboard() {
    return request<
      Array<{ bot_id: number; bot_name: string; best_score: number; matches: number }>
    >('/api/env/ipd/leaderboard')
  },
  async submitBot(botId: string) {
    return request<{ id: number; env_id: string; submitted: boolean }>(
      `/api/bots/${botId}/submit`,
      { method: 'POST', auth: true }
    )
  }
}
