function formatCurrency(value) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    maximumFractionDigits: 0
  }).format(value || 0)
}

function formatDateTime(value) {
  if (!value) {
    return '未同步'
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '未同步'
  }

  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(date)
}

function getConnectionLabel(connectionStatus) {
  const labelMap = {
    connecting: '连接中',
    connected: '已连接',
    disconnected: '已断开',
    error: '连接异常'
  }

  return labelMap[connectionStatus] || '未知'
}

function Dashboard({ stats, loading, error, connectionStatus }) {
  return (
    <section className="dashboard-panel">
      <div className="dashboard-header">
        <div>
          <p className="section-kicker">市场看板</p>
          <h3>实时统计</h3>
        </div>
        <div className="dashboard-status">
          <span className="status-chip">数据源 · {stats.source === 'websocket' ? 'WebSocket' : 'API / 聚合计算'}</span>
          <span className="status-chip">连接 · {getConnectionLabel(connectionStatus)}</span>
          <span className="status-chip">刷新 · {formatDateTime(stats.lastUpdated)}</span>
        </div>
      </div>

      <div className="metric-grid">
        <article className="metric-card">
          <span>总创业者</span>
          <strong>{loading ? '--' : stats.totalEntrepreneurs}</strong>
          <p>正在被追踪的实时样本</p>
        </article>
        <article className="metric-card">
          <span>今日新增</span>
          <strong>{loading ? '--' : stats.todayNew}</strong>
          <p>今日进入视野的新注册</p>
        </article>
        <article className="metric-card">
          <span>覆盖城市</span>
          <strong>{loading ? '--' : stats.coveredCities}</strong>
          <p>当前地图覆盖的城市范围</p>
        </article>
        <article className="metric-card">
          <span>活跃赛道</span>
          <strong>{loading ? '--' : stats.activeTracks}</strong>
          <p>横向比较的细分方向</p>
        </article>
        <article className="metric-card metric-card--accent">
          <span>总 MRR</span>
          <strong>{loading ? '--' : formatCurrency(stats.totalMrr)}</strong>
          <p>用于排序和优先级判断</p>
        </article>
      </div>

      {error ? <div className="dashboard-error">接口提示：{error}</div> : null}
    </section>
  )
}

export default Dashboard
