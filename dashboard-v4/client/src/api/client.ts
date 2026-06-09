import type { Agent, Task, TaskStats, OverviewMetrics, WorkspaceSummary } from '../types'

const API_BASE = '/api'

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) throw new Error(`API Error: ${res.status} ${res.statusText}`)
  const json = await res.json()
  return (json && typeof json === 'object' && 'data' in json ? json.data : json) as T
}

export const api = {
  // Agents
  getAgents: () => fetchJson<Agent[]>('/agents'),
  getAgent: (id: string) => fetchJson<Agent>(`/agents/${id}`),

  // Tasks
  getTasks: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return fetchJson<Task[]>(`/tasks${qs}`)
  },
  createTask: (task: Partial<Task>) =>
    fetchJson<Task>('/tasks', { method: 'POST', body: JSON.stringify(task) }),
  updateTask: (id: string, updates: Partial<Task>) =>
    fetchJson<Task>(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(updates) }),
  deleteTask: (id: string) =>
    fetchJson<void>(`/tasks/${id}`, { method: 'DELETE' }),
  getTaskStats: () => fetchJson<TaskStats>('/tasks/stats'),

  // Metrics
  getOverview: () => fetchJson<OverviewMetrics>('/metrics/overview'),

  // Workspace
  getWorkspaceSummary: () => fetchJson<WorkspaceSummary>('/workspace/summary'),

  // Health
  health: () => fetchJson<{ status: string; timestamp: string }>('/health'),
}
