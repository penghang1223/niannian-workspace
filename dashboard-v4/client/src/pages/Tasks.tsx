import { useMemo, useState } from 'react'
import { Card, Tag, Select, Input, Empty, Row, Col } from 'antd'
import { UserOutlined } from '@ant-design/icons'
import { useDashboardStore } from '../stores/dashboardStore'
import type { Task, TaskPriority, TaskStatus } from '../types'

const COLUMNS: { key: TaskStatus; title: string; color: string }[] = [
  { key: 'todo', title: 'Todo', color: '#6b7280' },
  { key: 'in_progress', title: 'In Progress', color: '#6366f1' },
  { key: 'review', title: 'Review', color: '#f59e0b' },
  { key: 'done', title: 'Done', color: '#10b981' },
]

const PRIORITY_COLORS: Record<TaskPriority, string> = {
  P0: '#ef4444',
  P1: '#f59e0b',
  P2: '#3b82f6',
  P3: '#6b7280',
}

function TaskCard({ task }: { task: Task }) {
  const agents = useDashboardStore((state) => state.agents)
  const ownerAgent = agents.find((agent) => agent.id === task.assignee_id)

  return (
    <Card
      size="small"
      style={{ marginBottom: 8 }}
      styles={{ body: { padding: '12px 14px' } }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <Tag
          color={PRIORITY_COLORS[task.priority]}
          style={{ margin: 0, borderRadius: 4, fontSize: 11, fontWeight: 600, border: 'none' }}
        >
          {task.priority}
        </Tag>
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{task.id}</span>
      </div>

      <div
        style={{
          fontSize: 13,
          fontWeight: 500,
          color: 'var(--color-text-primary)',
          marginBottom: 8,
          lineHeight: 1.4,
        }}
      >
        {task.title}
      </div>

      {task.description && (
        <div
          style={{
            fontSize: 12,
            color: 'var(--color-text-secondary)',
            marginBottom: 10,
            lineHeight: 1.4,
          }}
        >
          {task.description}
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
          <UserOutlined style={{ marginRight: 4 }} />
          {ownerAgent?.name || task.assignee_name || 'Unassigned'}
        </span>
        <Tag color="default" style={{ margin: 0, borderRadius: 4, fontSize: 11 }}>
          wave {task.wave}
        </Tag>
      </div>
    </Card>
  )
}

export default function TasksPage() {
  const { tasks, agents } = useDashboardStore()
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all')
  const [agentFilter, setAgentFilter] = useState<string>('all')
  const [query, setQuery] = useState('')

  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      if (statusFilter !== 'all' && task.status !== statusFilter) return false
      if (agentFilter !== 'all' && task.assignee_id !== agentFilter) return false
      const haystack = `${task.title} ${task.description ?? ''} ${task.id}`.toLowerCase()
      return haystack.includes(query.trim().toLowerCase())
    })
  }, [tasks, statusFilter, agentFilter, query])

  const groupedTasks = useMemo(() => {
    return COLUMNS.reduce<Record<TaskStatus, Task[]>>((acc, column) => {
      acc[column.key] = filteredTasks.filter((task) => task.status === column.key)
      return acc
    }, {
      todo: [],
      in_progress: [],
      review: [],
      done: [],
      cancelled: [],
    })
  }, [filteredTasks])

  return (
    <div>
      <Card size="small" style={{ marginBottom: 16 }} styles={{ body: { padding: 16 } }}>
        <Row gutter={[12, 12]} align="middle">
          <Col xs={24} md={10}>
            <Input.Search
              placeholder="Search tasks"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              allowClear
            />
          </Col>
          <Col xs={12} md={5}>
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: '100%' }}
              options={[
                { label: 'All status', value: 'all' },
                ...COLUMNS.map((column) => ({ label: column.title, value: column.key })),
              ]}
            />
          </Col>
          <Col xs={12} md={5}>
            <Select
              value={agentFilter}
              onChange={setAgentFilter}
              style={{ width: '100%' }}
              options={[
                { label: 'All agents', value: 'all' },
                ...agents.map((agent) => ({ label: agent.name, value: agent.id })),
              ]}
            />
          </Col>
          <Col xs={24} md={4}>
            <span style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
              {filteredTasks.length} of {tasks.length} tasks
            </span>
          </Col>
        </Row>
      </Card>

      <Row gutter={[12, 12]}>
        {COLUMNS.map((column) => (
          <Col key={column.key} xs={24} lg={6}>
            <Card
              size="small"
              title={
                <span style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{column.title}</span>
                  <Tag color={column.color} style={{ margin: 0 }}>
                    {groupedTasks[column.key].length}
                  </Tag>
                </span>
              }
              styles={{ body: { padding: 12, minHeight: 360 } }}
            >
              {groupedTasks[column.key].length === 0 ? (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No tasks" />
              ) : (
                groupedTasks[column.key].map((task) => <TaskCard key={task.id} task={task} />)
              )}
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  )
}
