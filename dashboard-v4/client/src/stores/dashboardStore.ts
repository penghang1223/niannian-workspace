import { create } from 'zustand'
import type { Agent, Task, TaskStats, OverviewMetrics, Alert, WSMessage } from '../types'

interface DashboardStore {
  // Agents
  agents: Agent[]
  setAgents: (agents: Agent[]) => void
  updateAgent: (agent: Agent) => void

  // Tasks
  tasks: Task[]
  setTasks: (tasks: Task[]) => void
  updateTask: (task: Task) => void
  addTask: (task: Task) => void
  removeTask: (taskId: string) => void

  // Stats
  taskStats: TaskStats | null
  setTaskStats: (stats: TaskStats) => void
  overview: OverviewMetrics | null
  setOverview: (overview: OverviewMetrics) => void

  // Alerts
  alerts: Alert[]
  addAlert: (alert: Alert) => void
  acknowledgeAlert: (alertId: string) => void

  // Connection
  wsConnected: boolean
  setWsConnected: (connected: boolean) => void

  // WS handler
  handleWSMessage: (msg: WSMessage) => void
}

export const useDashboardStore = create<DashboardStore>((set, get) => ({
  agents: [],
  setAgents: (agents) => set({ agents }),
  updateAgent: (agent) =>
    set((s) => ({
      agents: s.agents.map((a) => (a.id === agent.id ? { ...a, ...agent } : a)),
    })),

  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  updateTask: (task) =>
    set((s) => ({
      tasks: s.tasks.map((t) => (t.id === task.id ? { ...t, ...task } : t)),
    })),
  addTask: (task) => set((s) => ({ tasks: [task, ...s.tasks] })),
  removeTask: (taskId) =>
    set((s) => ({ tasks: s.tasks.filter((t) => t.id !== taskId) })),

  taskStats: null,
  setTaskStats: (taskStats) => set({ taskStats }),
  overview: null,
  setOverview: (overview) => set({ overview }),

  alerts: [],
  addAlert: (alert) => set((s) => ({ alerts: [alert, ...s.alerts].slice(0, 50) })),
  acknowledgeAlert: (alertId) =>
    set((s) => ({
      alerts: s.alerts.map((a) =>
        a.id === alertId ? { ...a, acknowledged: true } : a
      ),
    })),

  wsConnected: false,
  setWsConnected: (wsConnected) => set({ wsConnected }),

  handleWSMessage: (msg) => {
    const { type, payload } = msg
    switch (type) {
      case 'agent:status-change':
      case 'agent:heartbeat': {
        const agent = get().agents.find((a) => a.id === payload.agent_id)
        if (agent) get().updateAgent({ ...agent, ...payload })
        break
      }
      case 'task:created':
        get().addTask(payload.task)
        break
      case 'task:updated':
        get().updateTask(payload.task)
        break
      case 'task:deleted':
        get().removeTask(payload.taskId)
        break
      case 'system:alert':
        get().addAlert({
          id: `alert-${Date.now()}`,
          level: payload.level,
          message: payload.message,
          created_at: new Date().toISOString(),
          acknowledged: false,
        })
        break
      case 'metrics:update':
        if (payload.type === 'overview') get().setOverview(payload.data)
        break
    }
  },
}))
