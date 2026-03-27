import { Card, Row, Col, Statistic, Tag, Tooltip, Progress, Empty, Spin } from 'antd'
import {
  TeamOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { useDashboardStore } from '../stores/dashboardStore'
import type { Agent, AgentStatus } from '../types'

// Agent 状态 → 颜色映射
const STATUS_CONFIG: Record<string, { color: string; label: string; glow: string }> = {
  online: { color: '#10b981', label: '在线', glow: '0 0 12px rgba(16,185,129,0.3)' },
  busy: { color: '#f59e0b', label: '忙碌', glow: '0 0 12px rgba(245,158,11,0.3)' },
  idle: { color: '#6b7280', label: '空闲', glow: 'none' },
  offline: { color: '#ef4444', label: '离线', glow: '0 0 12px rgba(239,68,68,0.2)' },
  error: { color: '#dc2626', label: '异常', glow: '0 0 12px rgba(220,38,38,0.4)' },
}

// Agent 状态卡片
function AgentCard({ agent }: { agent: Agent }) {
  const cfg = STATUS_CONFIG[agent.status] ?? STATUS_CONFIG.idle
  const isOnline = agent.status !== 'offline'

  // 计算最后活跃时间
  let lastActive = '未知'
  if (agent.last_active) {
    const diff = Date.now() - new Date(agent.last_active).getTime()
    if (diff < 60000) lastActive = '刚刚'
    else if (diff < 3600000) lastActive = `${Math.floor(diff / 60000)} 分钟前`
    else lastActive = `${Math.floor(diff / 3600000)} 小时前`
  }

  return (
    <Card
      size="small"
      className="animate-in"
      style={{
        borderColor: isOnline ? cfg.color + '40' : undefined,
        boxShadow: cfg.glow,
        cursor: 'pointer',
        transition: 'all 0.2s ease',
      }}
      styles={{ body: { padding: '16px' } }}
    >
      {/* 头部：头像 + 状态 */}
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
          {agent.emoji || '🤖'}
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

      {/* 状态标签 */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
        <Tag
          color={cfg.color}
          style={{ margin: 0, borderRadius: 4, fontSize: 11, border: 'none' }}
        >
          {cfg.label}
        </Tag>
        {agent.tasks_in_progress > 0 && (
          <Tag
            color="purple"
            style={{ margin: 0, borderRadius: 4, fontSize: 11, border: 'none' }}
          >
            🔧 {agent.tasks_in_progress} 个任务进行中
          </Tag>
        )}
      </div>

      {/* 底部信息 */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: 11,
          color: 'var(--color-text-muted)',
        }}
      >
        <Tooltip title={`完成 ${agent.tasks_completed} 个任务，成功率 ${agent.success_rate}%`}>
          <span>✅ {agent.tasks_completed} 完成</span>
        </Tooltip>
        <span>🕐 {lastActive}</span>
      </div>
    </Card>
  )
}

// ===== 总览页 =====
export default function DashboardPage() {
  const { agents, tasks, taskStats, overview } = useDashboardStore()

  // 计算统计数据
  const rawStats = taskStats ?? {
    total: tasks.length,
    todo: tasks.filter((t) => t.status === 'todo').length,
    in_progress: tasks.filter((t) => t.status === 'in_progress').length,
    review: tasks.filter((t) => t.status === 'review').length,
    done: tasks.filter((t) => t.status === 'done').length,
    cancelled: 0,
  }
  const completionRate = rawStats.total
    ? Math.round((rawStats.done / rawStats.total) * 100)
    : 0
  const stats = { ...rawStats, completion_rate: completionRate }

  const overviewData = overview ?? {
    agents_online: agents.filter((a) => a.status !== 'offline').length,
    agents_total: agents.length,
    tasks_today: tasks.length,
    tasks_completed_today: stats.done,
    completion_rate: stats.completion_rate,
    avg_response_time_ms: 1250,
    alerts_count: agents.filter((a) => a.status === 'offline' || a.status === 'error').length,
  }

  if (agents.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <Spin size="large" tip="加载中..." />
      </div>
    )
  }

  return (
    <div>
      {/* 关键指标卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card size="small" styles={{ body: { padding: '20px' } }}>
            <Statistic
              title={<span style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>Agent 在线</span>}
              value={overviewData.agents_online}
              suffix={
                <span style={{ fontSize: 14, color: 'var(--color-text-muted)' }}>
                  /{overviewData.agents_total}
                </span>
              }
              valueStyle={{ color: '#10b981', fontSize: 28, fontWeight: 700 }}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small" styles={{ body: { padding: '20px' } }}>
            <Statistic
              title={<span style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>今日任务</span>}
              value={overviewData.tasks_today}
              valueStyle={{ color: '#6366f1', fontSize: 28, fontWeight: 700 }}
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small" styles={{ body: { padding: '20px' } }}>
            <Statistic
              title={<span style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>完成率</span>}
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
              title={<span style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>告警</span>}
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

      {/* 任务分布 */}
      <Card
        title="📊 任务分布"
        size="small"
        style={{ marginBottom: 24 }}
        styles={{ body: { padding: '16px 20px' } }}
      >
        <Row gutter={24}>
          <Col span={12}>
            <div style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>整体完成度</span>
                <span style={{ fontSize: 13, color: 'var(--color-text-primary)', fontWeight: 600 }}>
                  {stats.completion_rate}%
                </span>
              </div>
              <Progress
                percent={stats.completion_rate}
                strokeColor={{ '0%': '#6366f1', '100%': '#10b981' }}
                trailColor="#2a2a3e"
                showInfo={false}
                size="default"
              />
            </div>
          </Col>
          <Col span={12}>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <div>
                <Tag color="default" style={{ borderRadius: 4 }}>
                  待办 {stats.todo}
                </Tag>
              </div>
              <div>
                <Tag color="processing" style={{ borderRadius: 4 }}>
                  进行中 {stats.in_progress}
                </Tag>
              </div>
              <div>
                <Tag color="success" style={{ borderRadius: 4 }}>
                  完成 {stats.done}
                </Tag>
              </div>
              <div>
                <Tag color="error" style={{ borderRadius: 4 }}>
                  审查 {stats.review}
                </Tag>
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Agent 状态矩阵 */}
      <Card
        title={
          <span>
            🤖 Agent 状态矩阵
            <span style={{ fontSize: 12, color: 'var(--color-text-muted)', marginLeft: 12 }}>
              {agents.filter((a) => a.status !== 'offline').length}/{agents.length} 在线
            </span>
          </span>
        }
        size="small"
        styles={{ body: { padding: '16px' } }}
      >
        {agents.length === 0 ? (
          <Empty description="暂无 Agent 数据" />
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
