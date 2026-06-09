import { Card, Row, Col, Statistic, Tag, Tooltip, Progress, Empty, Spin, Space } from 'antd'
import {
  TeamOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ThunderboltOutlined,
  DatabaseOutlined,
  BookOutlined,
  ToolOutlined,
  InboxOutlined,
} from '@ant-design/icons'
import { useDashboardStore } from '../stores/dashboardStore'
import type { Agent } from '../types'

const STATUS_CONFIG: Record<string, { color: string; label: string; glow: string }> = {
  online: { color: '#10b981', label: 'Online', glow: '0 0 12px rgba(16,185,129,0.3)' },
  busy: { color: '#f59e0b', label: 'Busy', glow: '0 0 12px rgba(245,158,11,0.3)' },
  idle: { color: '#6b7280', label: 'Idle', glow: 'none' },
  offline: { color: '#ef4444', label: 'Offline', glow: '0 0 12px rgba(239,68,68,0.2)' },
  error: { color: '#dc2626', label: 'Error', glow: '0 0 12px rgba(220,38,38,0.4)' },
}

function formatLastActive(value: string | null) {
  if (!value) return 'unknown'
  const diff = Date.now() - new Date(value).getTime()
  if (Number.isNaN(diff)) return 'unknown'
  if (diff < 60_000) return 'just now'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} min ago`
  return `${Math.floor(diff / 3_600_000)} hr ago`
}

function AgentCard({ agent }: { agent: Agent }) {
  const cfg = STATUS_CONFIG[agent.status] ?? STATUS_CONFIG.idle
  const isOnline = agent.status !== 'offline'

  return (
    <Card
      size="small"
      className="animate-in"
      style={{
        borderColor: isOnline ? `${cfg.color}40` : undefined,
        boxShadow: cfg.glow,
        transition: 'all 0.2s ease',
      }}
      styles={{ body: { padding: '16px' } }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: `linear-gradient(135deg, ${cfg.color}30, ${cfg.color}10)`,
            border: `2px solid ${cfg.color}60`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 18,
          }}
        >
          {agent.emoji || 'AI'}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--color-text-primary)' }}>
            {agent.name}
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{agent.role}</div>
        </div>
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            background: cfg.color,
            boxShadow: `0 0 8px ${cfg.color}80`,
            animation: agent.status === 'online' ? 'pulse-glow 2s ease-in-out infinite' : undefined,
          }}
        />
      </div>

      <div style={{ display: 'flex', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
        <Tag color={cfg.color} style={{ margin: 0, borderRadius: 4, fontSize: 11, border: 'none' }}>
          {cfg.label}
        </Tag>
        {agent.tasks_in_progress > 0 && (
          <Tag color="purple" style={{ margin: 0, borderRadius: 4, fontSize: 11, border: 'none' }}>
            {agent.tasks_in_progress} active
          </Tag>
        )}
      </div>

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: 11,
          color: 'var(--color-text-muted)',
        }}
      >
        <Tooltip title={`${agent.tasks_completed} tasks completed, ${agent.success_rate}% success`}>
          <span>{agent.tasks_completed} done</span>
        </Tooltip>
        <span>{formatLastActive(agent.last_active)}</span>
      </div>
    </Card>
  )
}

export default function DashboardPage() {
  const { agents, tasks, taskStats, overview, workspaceSummary } = useDashboardStore()

  const rawStats = taskStats ?? {
    total: tasks.length,
    todo: tasks.filter((task) => task.status === 'todo').length,
    in_progress: tasks.filter((task) => task.status === 'in_progress').length,
    review: tasks.filter((task) => task.status === 'review').length,
    done: tasks.filter((task) => task.status === 'done').length,
    cancelled: 0,
  }
  const completionRate = rawStats.total ? Math.round((rawStats.done / rawStats.total) * 100) : 0
  const stats = { ...rawStats, completion_rate: completionRate }

  const overviewData = overview ?? {
    agents_online: agents.filter((agent) => agent.status !== 'offline').length,
    agents_total: agents.length,
    tasks_today: tasks.length,
    tasks_completed_today: stats.done,
    completion_rate: stats.completion_rate,
    avg_response_time_ms: 0,
    alerts_count: agents.filter((agent) => agent.status === 'offline' || agent.status === 'error').length,
  }

  if (agents.length === 0 && !workspaceSummary) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" tip="Loading dashboard..." />
      </div>
    )
  }

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card size="small" styles={{ body: { padding: '20px' } }}>
            <Statistic
              title="Agents Online"
              value={overviewData.agents_online}
              suffix={<span style={{ fontSize: 14, color: 'var(--color-text-muted)' }}>/{overviewData.agents_total}</span>}
              valueStyle={{ color: '#10b981', fontSize: 28, fontWeight: 700 }}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small" styles={{ body: { padding: '20px' } }}>
            <Statistic
              title="Tasks"
              value={overviewData.tasks_today}
              valueStyle={{ color: '#6366f1', fontSize: 28, fontWeight: 700 }}
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small" styles={{ body: { padding: '20px' } }}>
            <Statistic
              title="Completion"
              value={overviewData.completion_rate}
              suffix="%"
              valueStyle={{
                color: overviewData.completion_rate >= 50 ? '#10b981' : '#f59e0b',
                fontSize: 28,
                fontWeight: 700,
              }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small" styles={{ body: { padding: '20px' } }}>
            <Statistic
              title="Alerts"
              value={overviewData.alerts_count}
              valueStyle={{
                color: overviewData.alerts_count > 0 ? '#ef4444' : '#10b981',
                fontSize: 28,
                fontWeight: 700,
              }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {workspaceSummary && (
        <Card
          title="Workspace Inventory"
          size="small"
          style={{ marginBottom: 24 }}
          styles={{ body: { padding: '16px 20px' } }}
        >
          <Row gutter={[16, 16]}>
            <Col xs={12} md={6}>
              <Statistic title="Agent Profiles" value={workspaceSummary.agents.total} prefix={<TeamOutlined />} />
            </Col>
            <Col xs={12} md={6}>
              <Statistic title="Skills" value={workspaceSummary.skills.total} prefix={<ToolOutlined />} />
            </Col>
            <Col xs={12} md={6}>
              <Statistic title="Memory Files" value={workspaceSummary.memory.files} prefix={<DatabaseOutlined />} />
            </Col>
            <Col xs={12} md={6}>
              <Statistic title="Knowledge Files" value={workspaceSummary.knowledge.files} prefix={<BookOutlined />} />
            </Col>
          </Row>
          <Space wrap style={{ marginTop: 16 }}>
            <Tag color="lime">
              registry {workspaceSummary.agents.registry_total}/{workspaceSummary.agents.total}
            </Tag>
            <Tag color="blue">daily notes {workspaceSummary.memory.daily_notes}</Tag>
            <Tag color="cyan">latest {workspaceSummary.memory.latest_daily_note ?? 'none'}</Tag>
            <Tag color="purple">docs {workspaceSummary.docs.files}</Tag>
            <Tag color="gold">
              inbox {workspaceSummary.queues.inbox.pending}/{workspaceSummary.queues.inbox.processing}/{workspaceSummary.queues.inbox.done}
            </Tag>
            <Tag color="green">
              outbox {workspaceSummary.queues.outbox.pending}/{workspaceSummary.queues.outbox.done}
            </Tag>
            <Tag color={workspaceSummary.apps.legacy_dashboard ? 'orange' : 'default'}>
              legacy dashboard {workspaceSummary.apps.legacy_dashboard ? 'present' : 'absent'}
            </Tag>
          </Space>
        </Card>
      )}

      <Card
        title="Task Distribution"
        size="small"
        style={{ marginBottom: 24 }}
        styles={{ body: { padding: '16px 20px' } }}
      >
        <Row gutter={[24, 16]}>
          <Col xs={24} md={12}>
            <div style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>Overall progress</span>
                <span style={{ fontSize: 13, color: 'var(--color-text-primary)', fontWeight: 600 }}>
                  {stats.completion_rate}%
                </span>
              </div>
              <Progress
                percent={stats.completion_rate}
                strokeColor={{ '0%': '#6366f1', '100%': '#10b981' }}
                trailColor="#2a2a3e"
                showInfo={false}
              />
            </div>
          </Col>
          <Col xs={24} md={12}>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <Tag color="default">todo {stats.todo}</Tag>
              <Tag color="processing">active {stats.in_progress}</Tag>
              <Tag color="warning">review {stats.review}</Tag>
              <Tag color="success">done {stats.done}</Tag>
            </div>
          </Col>
        </Row>
      </Card>

      <Card title="Agent Matrix" size="small" styles={{ body: { padding: '16px' } }}>
        {agents.length === 0 ? (
          <Empty description="No agent data" />
        ) : (
          <Row gutter={[12, 12]}>
            {agents.map((agent) => (
              <Col key={agent.id} xs={24} sm={12} md={8} lg={6} xl={4}>
                <AgentCard agent={agent} />
              </Col>
            ))}
          </Row>
        )}
      </Card>
    </div>
  )
}
