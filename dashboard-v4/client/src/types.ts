// ===== Dashboard v4.0 类型定义 =====

export type AgentStatus = 'online' | 'busy' | 'idle' | 'offline' | 'error'

// 后端实际返回的 Agent 字段
export interface Agent {
  id: string
  name: string
  role: string
  emoji: string
  status: AgentStatus
  last_active: string | null
  tasks_completed: number
  tasks_in_progress: number
  success_rate: number
  created_at: string
  updated_at: string
}

export type TaskStatus = 'todo' | 'in_progress' | 'review' | 'done' | 'cancelled'
export type TaskPriority = 'P0' | 'P1' | 'P2' | 'P3'

// 后端实际返回的 Task 字段
export interface Task {
  id: string
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  assignee_id: string | null
  wave: number
  depends_on: string
  created_at: string
  updated_at: string
  completed_at: string | null
  assignee_name: string | null
  assignee_emoji: string | null
}

export interface TaskStats {
  total: number
  todo: number
  in_progress: number
  review: number
  done: number
  cancelled: number
}

export interface OverviewMetrics {
  agents_online: number
  agents_total: number
  tasks_today: number
  tasks_completed_today: number
  completion_rate: number
  avg_response_time_ms: number
  alerts_count: number
}

// WebSocket 事件
export interface WSMessage {
  type: string
  payload: any
  timestamp: string
}

export interface Alert {
  id: string
  level: 'info' | 'warn' | 'error'
  message: string
  entity_type?: string
  entity_id?: string
  created_at: string
  acknowledged: boolean
}
