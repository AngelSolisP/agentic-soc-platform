const BASE_URL = '/api'

// --- Auth token management ---
let _authToken: string | null = null

export function setAuthToken(token: string | null) {
  _authToken = token
  if (token) {
    sessionStorage.setItem('soc_auth_token', token)
  } else {
    sessionStorage.removeItem('soc_auth_token')
  }
}

export function getAuthToken(): string | null {
  if (_authToken) return _authToken
  const stored = sessionStorage.getItem('soc_auth_token')
  if (stored) _authToken = stored
  return _authToken
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getAuthToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const resp = await fetch(`${BASE_URL}${path}`, {
    headers,
    ...options,
  })
  // Session expired
  if (resp.type === 'opaqueredirect' || resp.status === 0) {
    window.dispatchEvent(new Event('auth:expired'))
    throw new ApiError(401, 'Session expired')
  }
  if (!resp.ok) {
    if (resp.status === 401 || resp.status === 403) {
      window.dispatchEvent(new Event('auth:expired'))
    }
    const body = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new ApiError(resp.status, body.detail || resp.statusText)
  }
  return resp.json()
}

// --- Cases ---
export interface Case {
  id: string
  name?: string
  resource_name?: string
  displayName?: string
  priority?: string
  status?: string
  environment?: string
  assignee?: string
  stage?: string
  alertCount?: number
  client_id: string
  pipeline?: {
    stages_completed: number
    total_stages: number
    latest_stage: string
    verdict?: string
  }
}

export interface CaseDetail {
  case: Record<string, unknown>
  alerts: Record<string, unknown>[]
  pipeline_stages: PipelineStage[]
  approvals: Approval[]
  client_id: string
}

export interface PipelineStage {
  stage_id: string
  stage_name: string
  stage_order: number
  status: string
  duration_seconds?: number
  output_structured?: Record<string, unknown>
  error?: string
  started_at?: string
  completed_at?: string
}

export interface Approval {
  approval_id: string
  client_id: string
  case_id: string
  status: string
  proposed_action: Record<string, unknown>
  triage_summary?: string
  decided_by?: string
  decided_at?: string
}

export interface ChatMessage {
  response: string
  tool_calls: { tool: string; args: Record<string, unknown>; result: string }[]
  session_id?: string
}

export interface AnalystMe {
  email: string
  role: 'analyst' | 'admin'
  allowed_clients: string[]
  auth_method: string
}

export const api = {
  me: () => request<AnalystMe>('/me'),
  cases: {
    list: (params?: { client_id?: string; status?: string }) => {
      const qs = new URLSearchParams()
      if (params?.client_id) qs.set('client_id', params.client_id)
      if (params?.status) qs.set('status', params.status)
      return request<{ cases: Case[]; total: number }>(`/cases?${qs}`)
    },
    get: (caseId: string, clientId: string) =>
      request<CaseDetail>(`/cases/${caseId}?client_id=${clientId}`),
    approve: (caseId: string, approvalId: string, notes: string = '') =>
      request<{ status: string }>(`/cases/${caseId}/approve`, {
        method: 'POST',
        body: JSON.stringify({ approval_id: approvalId, analyst_notes: notes }),
      }),
    reject: (caseId: string, approvalId: string, notes: string = '') =>
      request<{ status: string }>(`/cases/${caseId}/reject`, {
        method: 'POST',
        body: JSON.stringify({ approval_id: approvalId, analyst_notes: notes }),
      }),
    trigger: (caseId: string, clientId: string, alertType: string = 'GENERIC') =>
      request<{ status: string }>(`/cases/${caseId}/trigger`, {
        method: 'POST',
        body: JSON.stringify({ client_id: clientId, alert_type: alertType }),
      }),
    chat: (caseId: string, clientId: string, message: string, sessionId?: string) =>
      request<ChatMessage>(`/cases/${caseId}/chat`, {
        method: 'POST',
        body: JSON.stringify({ message, client_id: clientId, session_id: sessionId }),
      }),
  },
  admin: {
    dashboard: () => request<Record<string, unknown>>('/admin/dashboard'),
    clients: {
      list: () => request<{ clients: Record<string, unknown>[] }>('/admin/clients'),
      create: (data: Record<string, unknown>) =>
        request('/admin/clients', { method: 'POST', body: JSON.stringify(data) }),
      update: (id: string, data: Record<string, unknown>) =>
        request(`/admin/clients/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
      disable: (id: string) =>
        request(`/admin/clients/${id}`, { method: 'DELETE' }),
    },
    analysts: {
      list: () => request<{ analysts: Record<string, unknown>[] }>('/admin/analysts'),
      update: (email: string, data: { role: string; allowed_clients: string[] }) =>
        request(`/admin/analysts/${email}`, { method: 'PUT', body: JSON.stringify(data) }),
      delete: (email: string) =>
        request(`/admin/analysts/${encodeURIComponent(email)}`, { method: 'DELETE' }),
    },
    performance: (params?: { client_id?: string; days?: number }) => {
      const qs = new URLSearchParams()
      if (params?.client_id) qs.set('client_id', params.client_id)
      if (params?.days) qs.set('days', String(params.days))
      return request<{ metrics: Record<string, unknown>[] }>(`/admin/performance?${qs}`)
    },
    audit: (params?: { client_id?: string; action?: string; limit?: number }) => {
      const qs = new URLSearchParams()
      if (params?.client_id) qs.set('client_id', params.client_id)
      if (params?.action) qs.set('action', params.action)
      if (params?.limit) qs.set('limit', String(params.limit))
      return request<{ entries: Record<string, unknown>[] }>(`/admin/audit?${qs}`)
    },
  },
  watchlists: {
    list: (clientId: string) => request<Record<string, unknown>[]>(`/watchlists?client_id=${clientId}`),
    get: (clientId: string, watchlistId: string) =>
      request<Record<string, unknown>>(`/watchlists/${watchlistId}?client_id=${clientId}`),
    create: (clientId: string, data: Record<string, unknown>) =>

      request(`/watchlists?client_id=${clientId}`, { method: 'POST', body: JSON.stringify(data) }),
    update: (clientId: string, watchlistId: string, data: Record<string, unknown>) =>
      request(`/watchlists/${watchlistId}?client_id=${clientId}`, { method: 'PUT', body: JSON.stringify(data) }),
  },
  investigations: {
    list: (clientId: string, pageSize: number = 20, pageToken?: string) => {
      const qs = new URLSearchParams({ client_id: clientId, pageSize: String(pageSize) })
      if (pageToken) qs.set('pageToken', pageToken)
      return request<Record<string, unknown>>(`/investigations?${qs}`)
    },
    get: (clientId: string, investigationId: string) =>
      request<Record<string, unknown>>(`/investigations/${investigationId}?client_id=${clientId}`),
    trigger: (clientId: string, alertId: string) =>
      request<Record<string, unknown>>(`/investigations/trigger?client_id=${clientId}`, {
        method: 'POST',
        body: JSON.stringify({ alert_id: alertId }),
      }),
    getForAlert: (clientId: string, siemAlertId: string) =>
      request<Record<string, unknown>>(`/investigations/alerts/${siemAlertId}?client_id=${clientId}`),
    },
    }

