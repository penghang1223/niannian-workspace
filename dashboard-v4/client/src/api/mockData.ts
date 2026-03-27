// 本地模拟数据 — 后端未连接时使用
import type { Agent, Task, TaskStats, OverviewMetrics } from '../types'

const now = new Date().toISOString()

export const MOCK_AGENTS: Agent[] = [
  { id: 'main', name: '年年', role: '协调员/团队领导', emoji: '🎀', status: 'online', last_active: now, tasks_completed: 15, tasks_in_progress: 2, success_rate: 100, created_at: '2026-01-01', updated_at: now },
  { id: 'dev_engineer', name: '开发工程师', role: '后端开发', emoji: '💻', status: 'online', last_active: now, tasks_completed: 6, tasks_in_progress: 1, success_rate: 100, created_at: '2026-01-01', updated_at: now },
  { id: 'frontend_dev', name: '夕尔', role: '前端开发', emoji: '🎨', status: 'online', last_active: now, tasks_completed: 3, tasks_in_progress: 1, success_rate: 100, created_at: '2026-01-01', updated_at: now },
  { id: 'qa_engineer', name: '本尔', role: '测试工程师', emoji: '🛡️', status: 'idle', last_active: new Date(Date.now() - 120000).toISOString(), tasks_completed: 5, tasks_in_progress: 0, success_rate: 100, created_at: '2026-01-01', updated_at: now },
  { id: 'product_manager', name: '娜尔', role: '产品经理', emoji: '📋', status: 'online', last_active: now, tasks_completed: 8, tasks_in_progress: 0, success_rate: 100, created_at: '2026-01-01', updated_at: now },
  { id: 'taiyi', name: '太一', role: '架构师', emoji: '🏗️', status: 'online', last_active: now, tasks_completed: 4, tasks_in_progress: 0, success_rate: 100, created_at: '2026-01-01', updated_at: now },
  { id: 'chief_cute_officer', name: '岁岁', role: '首席可爱官', emoji: '🎉', status: 'idle', last_active: new Date(Date.now() - 300000).toISOString(), tasks_completed: 2, tasks_in_progress: 0, success_rate: 100, created_at: '2026-01-01', updated_at: now },
  { id: 'lingxi', name: '灵犀', role: '策略顾问', emoji: '💡', status: 'idle', last_active: new Date(Date.now() - 600000).toISOString(), tasks_completed: 1, tasks_in_progress: 0, success_rate: 100, created_at: '2026-01-01', updated_at: now },
  { id: 'jinghong', name: '惊鸿', role: '翰林/文案', emoji: '📝', status: 'idle', last_active: new Date(Date.now() - 900000).toISOString(), tasks_completed: 1, tasks_in_progress: 0, success_rate: 100, created_at: '2026-01-01', updated_at: now },
  { id: 'tiangong', name: '天工', role: '首席架构师', emoji: '⚙️', status: 'idle', last_active: new Date(Date.now() - 1200000).toISOString(), tasks_completed: 1, tasks_in_progress: 0, success_rate: 100, created_at: '2026-01-01', updated_at: now },
  { id: 'zhiming', name: '执明', role: '协调员', emoji: '🔄', status: 'idle', last_active: null, tasks_completed: 0, tasks_in_progress: 0, success_rate: 100, created_at: '2026-01-01', updated_at: now },
  { id: 'yueying', name: '月影', role: '数据分析', emoji: '📊', status: 'idle', last_active: null, tasks_completed: 0, tasks_in_progress: 0, success_rate: 100, created_at: '2026-01-01', updated_at: now },
  { id: 'shichen', name: '司辰', role: '时间管理', emoji: '⏰', status: 'idle', last_active: null, tasks_completed: 0, tasks_in_progress: 0, success_rate: 100, created_at: '2026-01-01', updated_at: now },
]

export const MOCK_TASKS: Task[] = [
  { id: 'DASH-001', title: 'PRD 需求文档', description: 'Dashboard v4.0 产品需求文档', status: 'done', priority: 'P0', assignee_id: 'product_manager', wave: 1, depends_on: '[]', created_at: now, updated_at: now, completed_at: now, assignee_name: '娜尔', assignee_emoji: '📋' },
  { id: 'DASH-002', title: '技术架构方案', description: 'Dashboard v4.0 技术架构设计', status: 'done', priority: 'P0', assignee_id: 'taiyi', wave: 1, depends_on: '[]', created_at: now, updated_at: now, completed_at: now, assignee_name: '太一', assignee_emoji: '🏗️' },
  { id: 'DASH-003', title: '后端 API 开发', description: 'Fastify + SQLite 后端服务', status: 'in_progress', priority: 'P0', assignee_id: 'dev_engineer', wave: 2, depends_on: '[]', created_at: now, updated_at: now, completed_at: null, assignee_name: '开发工程师', assignee_emoji: '💻' },
  { id: 'DASH-004', title: '前端 UI 实现', description: 'React + Vite 前端页面', status: 'in_progress', priority: 'P0', assignee_id: 'frontend_dev', wave: 2, depends_on: '[]', created_at: now, updated_at: now, completed_at: null, assignee_name: '夕尔', assignee_emoji: '🎨' },
  { id: 'DASH-005', title: '前后端联调', description: 'API 对接 + WebSocket 调试', status: 'todo', priority: 'P0', assignee_id: 'dev_engineer', wave: 3, depends_on: '[]', created_at: now, updated_at: now, completed_at: null, assignee_name: '开发工程师', assignee_emoji: '💻' },
  { id: 'DASH-006', title: '测试验收', description: '全面功能测试 + 性能测试', status: 'todo', priority: 'P0', assignee_id: 'qa_engineer', wave: 4, depends_on: '[]', created_at: now, updated_at: now, completed_at: null, assignee_name: '本尔', assignee_emoji: '🛡️' },
  { id: 'DASH-007', title: '部署上线', description: 'pm2 守护进程 + 启动脚本', status: 'todo', priority: 'P1', assignee_id: 'dev_engineer', wave: 4, depends_on: '[]', created_at: now, updated_at: now, completed_at: null, assignee_name: '开发工程师', assignee_emoji: '💻' },
]

export const MOCK_TASK_STATS: TaskStats = {
  total: 7,
  todo: 3,
  in_progress: 2,
  review: 0,
  done: 2,
  cancelled: 0,
}

export const MOCK_OVERVIEW: OverviewMetrics = {
  agents_online: 6,
  agents_total: 13,
  tasks_today: 7,
  tasks_completed_today: 2,
  completion_rate: 29,
  avg_response_time_ms: 1250,
  alerts_count: 0,
}
