import { Layout, Menu, Badge, Tooltip } from 'antd'
import {
  DashboardOutlined,
  ProjectOutlined,
  TeamOutlined,
  BarChartOutlined,
  SettingOutlined,
  BellOutlined,
  WifiOutlined,
  DisconnectOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useDashboardStore } from '../../stores/dashboardStore'
import type { ReactNode } from 'react'

const { Header, Sider, Content, Footer } = Layout

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '总览面板' },
  { key: '/tasks', icon: <ProjectOutlined />, label: '任务看板' },
  { key: '/agents', icon: <TeamOutlined />, label: 'Agent 管理', disabled: true },
  { key: '/analytics', icon: <BarChartOutlined />, label: '效能分析', disabled: true },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置', disabled: true },
]

interface Props {
  children: ReactNode
}

export default function AppLayout({ children }: Props) {
  const navigate = useNavigate()
  const location = useLocation()
  const { wsConnected, alerts, agents } = useDashboardStore()

  const onlineCount = agents.filter((a) => a.status !== 'offline').length
  const alertCount = alerts.filter((a) => !a.acknowledged).length

  return (
    <Layout style={{ height: '100vh' }}>
      {/* 侧边栏 */}
      <Sider
        width={220}
        theme="dark"
        style={{
          background: 'var(--color-bg-secondary)',
          borderRight: '1px solid var(--color-border)',
        }}
      >
        {/* Logo */}
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '1px solid var(--color-border)',
          }}
        >
          <span
            style={{
              fontSize: 18,
              fontWeight: 700,
              background: 'linear-gradient(135deg, #6366f1, #a78bfa)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              letterSpacing: '0.5px',
            }}
          >
            🎀 Dashboard v4
          </span>
        </div>

        {/* 导航菜单 */}
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{
            background: 'transparent',
            borderRight: 'none',
            padding: '8px 0',
          }}
        />

        {/* 底部状态 */}
        <div
          style={{
            position: 'absolute',
            bottom: 48,
            left: 0,
            right: 0,
            padding: '12px 20px',
            borderTop: '1px solid var(--color-border)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            {wsConnected ? (
              <WifiOutlined style={{ color: 'var(--status-active)', fontSize: 14 }} />
            ) : (
              <DisconnectOutlined style={{ color: 'var(--status-offline)', fontSize: 14 }} />
            )}
            <span style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
              {wsConnected ? '实时连接' : '离线模式'}
            </span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            {onlineCount}/{agents.length} Agent 在线
          </div>
        </div>
      </Sider>

      <Layout>
        {/* 顶栏 */}
        <Header
          style={{
            background: 'var(--color-bg-secondary)',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            padding: '0 24px',
            height: 56,
          }}
        >
          <Tooltip title={`${alertCount} 条未读告警`}>
            <Badge count={alertCount} size="small" offset={[-2, 2]}>
              <BellOutlined
                style={{ fontSize: 18, color: 'var(--color-text-secondary)', cursor: 'pointer' }}
              />
            </Badge>
          </Tooltip>
        </Header>

        {/* 主内容区 */}
        <Content
          style={{
            overflow: 'auto',
            padding: '24px',
            background: 'var(--color-bg-primary)',
          }}
        >
          {children}
        </Content>

        {/* 底栏 */}
        <Footer
          style={{
            background: 'var(--color-bg-secondary)',
            borderTop: '1px solid var(--color-border)',
            padding: '8px 24px',
            fontSize: 12,
            color: 'var(--color-text-muted)',
            display: 'flex',
            justifyContent: 'space-between',
            height: 36,
            lineHeight: '20px',
          }}
        >
          <span>Dashboard v4.0 · {agents.length} Agent · 最后同步 {new Date().toLocaleTimeString('zh-CN')}</span>
          <span>
            {wsConnected ? '🟢 已连接 ws://localhost:3456' : '🔴 后端未连接 · 使用本地数据'}
          </span>
        </Footer>
      </Layout>
    </Layout>
  )
}
