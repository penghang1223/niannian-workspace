import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import AppLayout from './components/layout/AppLayout'
import DashboardPage from './pages/Dashboard'
import TasksPage from './pages/Tasks'
import { useWebSocket } from './hooks/useWebSocket'
import { useDashboardStore } from './stores/dashboardStore'
import { MOCK_AGENTS, MOCK_TASKS, MOCK_TASK_STATS, MOCK_OVERVIEW } from './api/mockData'

function App() {
  const { handleWSMessage, setAgents, setTasks, setTaskStats, setOverview, setWsConnected } =
    useDashboardStore()

  // WebSocket 连接
  const { isConnected } = useWebSocket({
    onMessage: handleWSMessage,
  })

  // 同步 WS 连接状态到 store
  useEffect(() => {
    setWsConnected(isConnected)
  }, [isConnected, setWsConnected])

  // 初始化加载数据（尝试 API，失败用 mock）
  useEffect(() => {
    fetch('/api/agents')
      .then((r) => r.json())
      .then((res) => {
        setAgents(res.data || res)
        return fetch('/api/tasks')
      })
      .then((r) => r.json())
      .then((res) => {
        setTasks(res.data || res)
        return fetch('/api/tasks/stats')
      })
      .then((r) => r.json())
      .then((res) => {
        setTaskStats(res.data || res)
        return fetch('/api/metrics/overview')
      })
      .then((r) => r.json())
      .then((res) => {
        setOverview(res.data || res)
      })
      .catch((e) => {
        console.log('[Init] API error, using mock data:', e.message)
        setAgents(MOCK_AGENTS)
        setTasks(MOCK_TASKS)
        setTaskStats(MOCK_TASK_STATS)
        setOverview(MOCK_OVERVIEW)
      })
  }, [setAgents, setTasks, setTaskStats, setOverview])

  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  )
}

export default App
