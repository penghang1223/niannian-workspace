import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import AppLayout from './components/layout/AppLayout'
import DashboardPage from './pages/Dashboard'
import TasksPage from './pages/Tasks'
import { useWebSocket } from './hooks/useWebSocket'
import { useDashboardStore } from './stores/dashboardStore'
import { api } from './api/client'
import { MOCK_AGENTS, MOCK_TASKS, MOCK_TASK_STATS, MOCK_OVERVIEW } from './api/mockData'

function App() {
  const {
    handleWSMessage,
    setAgents,
    setTasks,
    setTaskStats,
    setOverview,
    setWorkspaceSummary,
    setWsConnected,
  } = useDashboardStore()

  const { isConnected } = useWebSocket({ onMessage: handleWSMessage })

  useEffect(() => {
    setWsConnected(isConnected)
  }, [isConnected, setWsConnected])

  useEffect(() => {
    let cancelled = false

    async function loadDashboardData() {
      try {
        const [agents, tasks, taskStats, overview, workspaceSummary] = await Promise.all([
          api.getAgents(),
          api.getTasks(),
          api.getTaskStats(),
          api.getOverview(),
          api.getWorkspaceSummary(),
        ])

        if (cancelled) return
        setAgents(agents)
        setTasks(tasks)
        setTaskStats(taskStats)
        setOverview(overview)
        setWorkspaceSummary(workspaceSummary)
      } catch (error) {
        if (cancelled) return
        console.log('[Init] API error, using mock dashboard data:', error)
        setAgents(MOCK_AGENTS)
        setTasks(MOCK_TASKS)
        setTaskStats(MOCK_TASK_STATS)
        setOverview(MOCK_OVERVIEW)
        setWorkspaceSummary(null)
      }
    }

    loadDashboardData()
    return () => {
      cancelled = true
    }
  }, [setAgents, setTasks, setTaskStats, setOverview, setWorkspaceSummary])

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
