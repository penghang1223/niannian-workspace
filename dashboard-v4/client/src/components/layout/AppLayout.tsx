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
  { key: '/', icon: <DashboardOutlined />, label: 'Overview' },
  { key: '/tasks', icon: <ProjectOutlined />, label: 'Tasks' },
  { key: '/agents', icon: <TeamOutlined />, label: 'Agents', disabled: true },
  { key: '/analytics', icon: <BarChartOutlined />, label: 'Analytics', disabled: true },
  { key: '/settings', icon: <SettingOutlined />, label: 'Settings', disabled: true },
]

interface Props {
  children: ReactNode
}

export default function AppLayout({ children }: Props) {
  const navigate = useNavigate()
  const location = useLocation()
  const { wsConnected, alerts, agents, workspaceSummary } = useDashboardStore()

  const onlineCount = agents.filter((agent) => agent.status !== 'offline').length
  const alertCount = alerts.filter((alert) => !alert.acknowledged).length
  const lastSync = workspaceSummary
    ? new Date(workspaceSummary.generated_at).toLocaleTimeString()
    : new Date().toLocaleTimeString()

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider
        width={220}
        theme="dark"
        style={{
          background: 'var(--color-bg-secondary)',
          borderRight: '1px solid var(--color-border)',
        }}
      >
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
              color: 'var(--color-text-primary)',
              letterSpacing: 0,
            }}
          >
            Niannian OS
          </span>
        </div>

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
              {wsConnected ? 'Live connection' : 'Offline mode'}
            </span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            {onlineCount}/{agents.length} agents online
          </div>
        </div>
      </Sider>

      <Layout>
        <Header
          style={{
            background: 'var(--color-bg-secondary)',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 24px',
            height: 56,
          }}
        >
          <span style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
            Workspace control plane
          </span>
          <Tooltip title={`${alertCount} unread alerts`}>
            <Badge count={alertCount} size="small" offset={[-2, 2]}>
              <BellOutlined
                style={{ fontSize: 18, color: 'var(--color-text-secondary)', cursor: 'pointer' }}
              />
            </Badge>
          </Tooltip>
        </Header>

        <Content
          style={{
            overflow: 'auto',
            padding: '24px',
            background: 'var(--color-bg-primary)',
          }}
        >
          {children}
        </Content>

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
          <span>Dashboard v4.0 · {agents.length} agents · synced {lastSync}</span>
          <span>{wsConnected ? 'Connected to ws://localhost:3456' : 'Backend not connected'}</span>
        </Footer>
      </Layout>
    </Layout>
  )
}
