export type AgentId =
  | 'main'
  | 'product_manager'
  | 'dev_engineer'
  | 'frontend_dev'
  | 'qa_engineer'
  | 'chief_cute_officer'
  | 'taiyi'
  | 'tiangong'
  | 'lingxi'
  | 'jinghong'
  | 'zhiming'
  | 'yueying'
  | 'shichen'
  | string

export type AgentStatus = 'online' | 'busy' | 'idle' | 'offline' | 'error'

export type ModelPolicy = {
  preferred: string
  fallback?: string[]
  budget?: {
    max_tokens_per_turn?: number
    max_cost_per_day_usd?: number
  }
}

export type PermissionScope =
  | 'filesystem:read'
  | 'filesystem:write'
  | 'git:read'
  | 'git:write'
  | 'network:read'
  | 'network:write'
  | 'browser:use'
  | 'secrets:read'
  | 'external:publish'

export type MemoryScope = {
  private_paths: string[]
  shared_paths: string[]
  write_policy: 'agent-owned' | 'coordinator-reviewed' | 'append-only'
}

export type AgentManifest = {
  id: AgentId
  display_name: string
  role: string
  mission: string
  status?: AgentStatus
  capabilities: string[]
  primary_tools: string[]
  model_policy: ModelPolicy
  memory: MemoryScope
  permissions: PermissionScope[]
  playbook_paths: string[]
  output_contracts: string[]
}

export type TaskStatus = 'todo' | 'in_progress' | 'review' | 'done' | 'cancelled' | 'blocked'
export type TaskPriority = 'P0' | 'P1' | 'P2' | 'P3'

export type WorkflowNode = {
  id: string
  title: string
  description?: string
  owner: AgentId
  status: TaskStatus
  priority: TaskPriority
  required_capabilities: string[]
  inputs?: string[]
  outputs?: string[]
}

export type WorkflowEdge = {
  from: string
  to: string
  type: 'blocks' | 'informs' | 'reviews' | 'hands_off_to'
}

export type WorkflowDefinition = {
  id: string
  title: string
  goal: string
  created_at: string
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  approval_gates: string[]
}

export type RuntimeEventType =
  | 'agent.started'
  | 'agent.heartbeat'
  | 'agent.stopped'
  | 'task.created'
  | 'task.started'
  | 'task.updated'
  | 'task.completed'
  | 'task.blocked'
  | 'tool.called'
  | 'memory.written'
  | 'approval.requested'
  | 'approval.resolved'

export type AgentRuntimeEvent = {
  id: string
  type: RuntimeEventType
  timestamp: string
  source_agent?: AgentId
  workflow_id?: string
  task_id?: string
  severity?: 'debug' | 'info' | 'warn' | 'error'
  payload: Record<string, unknown>
}
