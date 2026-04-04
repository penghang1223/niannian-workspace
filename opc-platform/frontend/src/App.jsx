import { useEffect, useMemo, useRef, useState } from 'react'
import Dashboard from './components/Dashboard/Dashboard'
import GlobeComponent from './components/Globe/GlobeComponent'
import websocketService from './services/websocket'
import {
  deriveStatsFromEntrepreneurs,
  fetchDashboardStats,
  fetchEntrepreneurs,
  normalizeEntrepreneurPayload,
  normalizeStatsPayload
} from './services/api'

const EMPTY_STATS = {
  totalEntrepreneurs: 0,
  todayNew: 0,
  coveredCities: 0,
  activeTracks: 0,
  totalMrr: 0,
  lastUpdated: null,
  source: 'api'
}

function upsertEntrepreneur(collection, item) {
  const existingIndex = collection.findIndex((currentItem) => currentItem.id === item.id)

  if (existingIndex === -1) {
    return [item, ...collection]
  }

  const nextCollection = [...collection]
  nextCollection[existingIndex] = {
    ...nextCollection[existingIndex],
    ...item
  }

  return nextCollection
}

function formatCurrency(value) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    maximumFractionDigits: 0
  }).format(Number(value) || 0)
}

function formatCompactCurrency(value) {
  const numericValue = Number(value) || 0

  if (numericValue >= 1000000) {
    return `¥${(numericValue / 1000000).toFixed(2)}M`
  }

  if (numericValue >= 1000) {
    return `¥${(numericValue / 1000).toFixed(0)}K`
  }

  return `¥${numericValue}`
}

function formatRelativeTime(value) {
  if (!value) {
    return '刚刚更新'
  }

  const timestamp = new Date(value).getTime()
  if (Number.isNaN(timestamp)) {
    return '刚刚更新'
  }

  const diffMinutes = Math.max(0, Math.round((Date.now() - timestamp) / 60000))

  if (diffMinutes < 1) {
    return '刚刚更新'
  }

  if (diffMinutes < 60) {
    return `${diffMinutes} 分钟前`
  }

  const diffHours = Math.round(diffMinutes / 60)
  if (diffHours < 24) {
    return `${diffHours} 小时前`
  }

  const diffDays = Math.round(diffHours / 24)
  return `${diffDays} 天前`
}

function formatLocation(item) {
  const province = item?.province || ''
  const city = item?.city || '未知城市'

  if (!province || province === city) {
    return city
  }

  return `${province} · ${city}`
}

function App() {
  const [entrepreneurs, setEntrepreneurs] = useState([])
  const [stats, setStats] = useState(EMPTY_STATS)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [connectionStatus, setConnectionStatus] = useState('connecting')
  const [themeMode, setThemeMode] = useState(() => {
    if (typeof window === 'undefined') {
      return 'system'
    }

    return localStorage.getItem('opc-theme-mode') || 'system'
  })
  const [systemTheme, setSystemTheme] = useState(() => {
    if (typeof window === 'undefined') {
      return 'light'
    }

    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })
  const [heroStatsExpanded, setHeroStatsExpanded] = useState(false)
  const [heroSlideIndex, setHeroSlideIndex] = useState(0)
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [authMode, setAuthMode] = useState('login') // 'login' or 'register'
  const [authError, setAuthError] = useState('')
  const [authLoading, setAuthLoading] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const entrepreneursRef = useRef([])
  const resolvedTheme = themeMode === 'system' ? systemTheme : themeMode

  const refreshData = async () => {
    setLoading(true)
    setError('')

    const entrepreneursResult = await fetchEntrepreneurs()
      .then((value) => ({ status: 'fulfilled', value }))
      .catch((reason) => ({ status: 'rejected', reason }))

    const nextEntrepreneurs = entrepreneursResult.status === 'fulfilled' ? entrepreneursResult.value : []

    const statsResult = await fetchDashboardStats(nextEntrepreneurs)
      .then((value) => ({ status: 'fulfilled', value }))
      .catch((reason) => ({ status: 'rejected', reason }))

    const nextStats = statsResult.status === 'fulfilled'
      ? statsResult.value
      : deriveStatsFromEntrepreneurs(nextEntrepreneurs)

    entrepreneursRef.current = nextEntrepreneurs
    setEntrepreneurs(nextEntrepreneurs)
    setStats(nextStats)

    const errors = []
    if (entrepreneursResult.status === 'rejected') {
      errors.push(`创业者 API 不可用：${entrepreneursResult.reason.message}`)
    }

    if (statsResult.status === 'rejected') {
      errors.push(`统计 API 不可用：${statsResult.reason.message}`)
    }

    setError(errors.join('；'))
    setLoading(false)
  }

  const handleLogin = async (email, password) => {
    setAuthLoading(true)
    setAuthError('')

    try {
      const result = await login(email, password)
      setCurrentUser(result.user)
      setIsAuthenticated(true)
      setAuthModalOpen(false)
    } catch (error) {
      setAuthError(error.message)
    } finally {
      setAuthLoading(false)
    }
  }

  const handleRegister = async (name, email, password) => {
    setAuthLoading(true)
    setAuthError('')

    try {
      const result = await register(name, email, password)
      setCurrentUser(result.user)
      setIsAuthenticated(true)
      setAuthModalOpen(false)
    } catch (error) {
      setAuthError(error.message)
    } finally {
      setAuthLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
    setCurrentUser(null)
    setIsAuthenticated(false)
  }

  const checkAuth = async () => {
    try {
      const user = await getCurrentUser()
      if (user) {
        setCurrentUser(user)
        setIsAuthenticated(true)
      }
    } catch (error) {
      console.log('认证检查失败:', error)
    }
  }

  useEffect(() => {
    refreshData()
    checkAuth()
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const syncTheme = (event) => setSystemTheme(event.matches ? 'dark' : 'light')

    mediaQuery.addEventListener('change', syncTheme)

    return () => {
      mediaQuery.removeEventListener('change', syncTheme)
    }
  }, [])

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('opc-theme-mode', themeMode)
    }
  }, [themeMode])

  useEffect(() => {
    document.documentElement.dataset.theme = resolvedTheme
    document.documentElement.style.colorScheme = resolvedTheme
  }, [resolvedTheme])

  useEffect(() => {
    const handleRegistration = (payload) => {
      const [incomingRegistration] = normalizeEntrepreneurPayload({ entrepreneurs: [payload] })

      if (!incomingRegistration) {
        return
      }

      setEntrepreneurs((currentValue) => {
        const nextEntrepreneurs = upsertEntrepreneur(currentValue, incomingRegistration)
        entrepreneursRef.current = nextEntrepreneurs

        setStats((currentStats) => (
          payload?.stats
            ? normalizeStatsPayload(payload.stats, nextEntrepreneurs)
            : {
                ...deriveStatsFromEntrepreneurs(nextEntrepreneurs),
                source: currentStats.source === 'websocket' ? 'websocket' : 'derived'
              }
        ))

        return nextEntrepreneurs
      })
    }

    const handleInitialData = (payload) => {
      const nextEntrepreneurs = normalizeEntrepreneurPayload(payload)

      if (nextEntrepreneurs.length > 0) {
        entrepreneursRef.current = nextEntrepreneurs
        setEntrepreneurs(nextEntrepreneurs)
        setStats(normalizeStatsPayload(payload, nextEntrepreneurs))
      }
    }

    const handleStatsUpdate = (payload) => {
      const nextEntrepreneurs = payload?.entrepreneurs
        ? normalizeEntrepreneurPayload(payload)
        : entrepreneursRef.current

      if (payload?.entrepreneurs) {
        entrepreneursRef.current = nextEntrepreneurs
        setEntrepreneurs(nextEntrepreneurs)
      }

      setStats(normalizeStatsPayload(payload, nextEntrepreneurs))
    }

    const handleConnect = () => setConnectionStatus('connected')
    const handleDisconnect = () => setConnectionStatus('disconnected')
    const handleConnectError = () => setConnectionStatus('error')

    websocketService.connect()

    const unsubscribers = [
      websocketService.on('connect', handleConnect),
      websocketService.on('disconnect', handleDisconnect),
      websocketService.on('connect_error', handleConnectError),
      websocketService.on('new_registration', handleRegistration),
      websocketService.on('initial_data', handleInitialData),
      websocketService.on('stats_update', handleStatsUpdate)
    ]

    return () => {
      unsubscribers.forEach((unsubscribe) => unsubscribe())
      websocketService.disconnect()
    }
  }, [])

  const recentEntrepreneurs = useMemo(() => (
    [...entrepreneurs]
      .sort((left, right) => new Date(right.createdAt || 0).getTime() - new Date(left.createdAt || 0).getTime())
      .slice(0, 6)
  ), [entrepreneurs])

  const featuredEntrepreneur = recentEntrepreneurs[0] || null
  const remainingEntrepreneurs = recentEntrepreneurs.slice(1)

  const leaderboard = useMemo(() => (
    [...entrepreneurs]
      .sort((left, right) => (Number(right.mrr) || 0) - (Number(left.mrr) || 0))
      .slice(0, 5)
  ), [entrepreneurs])

  const trackSummary = useMemo(() => {
    const summaryMap = new Map()

    entrepreneurs.forEach((item) => {
      const current = summaryMap.get(item.track) || {
        track: item.track || '未分类',
        count: 0,
        totalMrr: 0,
        cities: new Set()
      }

      current.count += 1
      current.totalMrr += Number(item.mrr) || 0
      if (item.city) {
        current.cities.add(item.city)
      }

      summaryMap.set(current.track, current)
    })

    return [...summaryMap.values()]
      .map((item) => ({
        ...item,
        cityCount: item.cities.size
      }))
      .sort((left, right) => right.totalMrr - left.totalMrr)
  }, [entrepreneurs])

  const cityHighlights = useMemo(() => {
    const cityMap = new Map()

    entrepreneurs.forEach((item) => {
      const key = formatLocation(item)
      const current = cityMap.get(key) || {
        name: key,
        founders: 0,
        totalMrr: 0
      }

      current.founders += 1
      current.totalMrr += Number(item.mrr) || 0
      cityMap.set(key, current)
    })

    return [...cityMap.values()]
      .sort((left, right) => right.totalMrr - left.totalMrr)
      .slice(0, 4)
  }, [entrepreneurs])

  const trackChart = useMemo(() => {
    const topTracks = trackSummary.slice(0, 5)
    const maxTrackMrr = Math.max(...topTracks.map((item) => item.totalMrr), 1)

    return topTracks.map((item) => ({
      ...item,
      heightRatio: Math.max(18, Math.round((item.totalMrr / maxTrackMrr) * 100))
    }))
  }, [trackSummary])

  const marketPulse = useMemo(() => {
    const averageMrr = entrepreneurs.length > 0 ? stats.totalMrr / entrepreneurs.length : 0
    const leadingTrack = trackSummary[0]
    const leadingCity = cityHighlights[0]
    const recentWindowCount = entrepreneurs.filter((item) => {
      const timestamp = new Date(item.createdAt || 0).getTime()
      return timestamp > Date.now() - (24 * 60 * 60 * 1000)
    }).length

    return [
      {
        label: '平均 MRR',
        value: formatCompactCurrency(averageMrr),
        note: '当前样本中的单体经营均值'
      },
      {
        label: '头部赛道',
        value: leadingTrack?.track || '未分类',
        note: leadingTrack ? `${formatCompactCurrency(leadingTrack.totalMrr)} 总 MRR` : '等待更多样本'
      },
      {
        label: '热点城市',
        value: leadingCity?.name || '暂无',
        note: leadingCity ? `${leadingCity.founders} 位创业者` : '等待更多样本'
      },
      {
        label: '24h 入场',
        value: `${recentWindowCount}`,
        note: '近 24 小时内进入地图的样本'
      }
    ]
  }, [cityHighlights, entrepreneurs, stats.totalMrr, trackSummary])

  const trendCards = useMemo(() => {
    const last7Days = entrepreneurs.filter((item) => {
      const timestamp = new Date(item.createdAt || 0).getTime()
      return timestamp > Date.now() - (7 * 24 * 60 * 60 * 1000)
    }).length

    const topTrack = trackSummary[0]
    const secondTrack = trackSummary[1]
    const topCity = cityHighlights[0]

    return [
      {
        title: '7 天入场节奏',
        value: `${last7Days}`,
        description: '最近一周进入地图的创业者样本数量。'
      },
      {
        title: '赛道领先差',
        value: topTrack && secondTrack
          ? formatCompactCurrency(Math.max(0, topTrack.totalMrr - secondTrack.totalMrr))
          : '—',
        description: '头部赛道与第二名之间的 MRR 差值。'
      },
      {
        title: '核心聚集城市',
        value: topCity?.name || '暂无',
        description: topCity ? `${topCity.founders} 位创业者正在聚集。` : '等待更多样本。'
      }
    ]
  }, [cityHighlights, entrepreneurs, trackSummary])

  const footerLinks = [
    {
      title: '探索',
      items: ['实时地图', '最新上线', '排行榜']
    },
    {
      title: '洞察',
      items: ['经营洞察', '城市分布', '赛道规模']
    },
    {
      title: '入口',
      items: ['加入样本', '能力服务', '数据追踪']
    }
  ]

  const serviceCards = [
    {
      title: '地图追踪',
      description: '在真实地球里查看城市、赛道与创业者分布，适合做第一层筛选。'
    },
    {
      title: '经营洞察',
      description: '把 MRR、赛道规模和城市密度放到同一页里，直接判断当前机会面。'
    },
    {
      title: '加入样本',
      description: '让新的创业者持续进入地图与排行榜，补齐实时性和后续分析。'
    }
  ]

  const heroHighlights = useMemo(() => {
    const topTrack = trackSummary[0]
    const topCity = cityHighlights[0]
    const leadFounder = leaderboard[0]

    return [
      {
        kicker: '实时焦点',
        title: leadFounder?.name || '等待样本同步',
        value: leadFounder ? formatCurrency(leadFounder.mrr) : '--',
        description: leadFounder
          ? `${formatLocation(leadFounder)} · ${leadFounder.track}`
          : '头部创业者会在这里展示。'
      },
      {
        kicker: '头部赛道',
        title: topTrack?.track || '未分类',
        value: topTrack ? formatCompactCurrency(topTrack.totalMrr) : '--',
        description: topTrack
          ? `${topTrack.count} 位创业者，覆盖 ${topTrack.cityCount} 座城市`
          : '等待更多赛道样本。'
      },
      {
        kicker: '热点城市',
        title: topCity?.name || '暂无城市',
        value: topCity ? `${topCity.founders} 位` : '--',
        description: topCity
          ? `${formatCompactCurrency(topCity.totalMrr)} 总 MRR`
          : '等待更多城市数据。'
      }
    ]
  }, [cityHighlights, leaderboard, trackSummary])

  useEffect(() => {
    if (heroHighlights.length <= 1) {
      return undefined
    }

    const timer = window.setInterval(() => {
      setHeroSlideIndex((currentValue) => (currentValue + 1) % heroHighlights.length)
    }, 3600)

    return () => window.clearInterval(timer)
  }, [heroHighlights.length])

  return (
    <div className="page-shell">
      <div className="page-gradient" />
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark">OPC</div>
          <div>
            <p className="brand-kicker">中国创业者情报门户</p>
            <h1 className="brand-title">创业者市场情报台</h1>
          </div>
        </div>
        <nav className="topnav">
          <a href="#map">地图</a>
          <a href="#new">最新上线</a>
          <a href="#leaderboard">排行榜</a>
          <a href="#insights">洞察</a>
          <a href="#services">服务</a>
        </nav>
        <div className="auth-section">
          {isAuthenticated ? (
            <div className="user-menu">
              <span className="user-name">{currentUser?.name}</span>
              <button
                className="logout-button"
                onClick={handleLogout}
              >
                登出
              </button>
            </div>
          ) : (
            <button
              className="login-button"
              onClick={() => setAuthModalOpen(true)}
            >
              登录 / 注册
            </button>
          )}
        </div>
        <div className="theme-switch" role="tablist" aria-label="主题模式">
          {[
            ['light', '白天'],
            ['dark', '黑夜'],
            ['system', '系统']
          ].map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={`theme-switch__option${themeMode === value ? ' theme-switch__option--active' : ''}`}
              onClick={() => setThemeMode(value)}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      <main className="portal-layout">
        <section className="hero-panel">
          <div className="hero-topline">
            <div className="hero-copy">
              <p className="eyebrow">中国创业者情报台 / 实时地图</p>
              <h2 className="hero-headline">
                <span>看见中国</span>
                <span className="hero-headline__accent">创业者流动</span>
                <span>与聚集。</span>
              </h2>
              <p className="hero-description">
                用一张真实地球承接样本、赛道、城市与榜单。
                先看空间，再看经营。
              </p>
              <div className="hero-actions">
                <a className="primary-action" href="#map">进入实时地图</a>
                <a className="secondary-action" href="#new">查看最新项目</a>
              </div>
            </div>
            <div className="hero-spotlight">
              <div className="hero-spotlight__card">
                <span className="section-kicker">{heroHighlights[heroSlideIndex]?.kicker}</span>
                <h3>{heroHighlights[heroSlideIndex]?.title}</h3>
                <strong>{heroHighlights[heroSlideIndex]?.value}</strong>
                <p>{heroHighlights[heroSlideIndex]?.description}</p>
                <div className="hero-spotlight__meta">
                  <span>实时轮播</span>
                  <span>{heroSlideIndex + 1} / {heroHighlights.length}</span>
                </div>
                <div className="hero-spotlight__rail">
                  {heroHighlights.map((item, index) => (
                    <button
                      key={item.kicker}
                      type="button"
                      className={`hero-spotlight__rail-item${heroSlideIndex === index ? ' hero-spotlight__rail-item--active' : ''}`}
                      onClick={() => setHeroSlideIndex(index)}
                    >
                      <span>{item.kicker}</span>
                      <strong>{item.title}</strong>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <section className="hero-map-panel" id="map">
            <div className="section-heading">
              <div>
                <p className="section-kicker">可视化总览</p>
                <h3>实时地图总览</h3>
              </div>
              <p>把筛选、焦点与地球收进同一屏，不再把地图放在第二层。</p>
            </div>
            <div className="hero-map-shell">
              <div className={`hero-sidecard hero-sidecard--floating${heroStatsExpanded ? ' hero-sidecard--expanded' : ' hero-sidecard--collapsed'}`}>
                <button
                  type="button"
                  className="hero-sidecard__toggle"
                  onClick={() => setHeroStatsExpanded((currentValue) => !currentValue)}
                >
                  <div>
                    <span className="sidecard-label">实时样本</span>
                    <strong className="hero-sidecard__toggle-value">{loading ? '--' : stats.totalEntrepreneurs}</strong>
                  </div>
                  <span className="hero-sidecard__toggle-icon">{heroStatsExpanded ? '收起' : '展开'}</span>
                </button>
                {heroStatsExpanded ? (
                  <>
                    <div className="sidecard-value">{loading ? '--' : stats.totalEntrepreneurs}</div>
                    <div className="sidecard-caption">当前正在追踪的中国区创业者样本</div>
                    <div className="sidecard-grid">
                      <div>
                        <span>今日新增</span>
                        <strong>{loading ? '--' : stats.todayNew}</strong>
                      </div>
                      <div>
                        <span>MRR</span>
                        <strong>{loading ? '--' : formatCompactCurrency(stats.totalMrr)}</strong>
                      </div>
                    </div>
                  </>
                ) : null}
              </div>
              <GlobeComponent
                entrepreneurs={entrepreneurs}
                loading={loading}
                error={error}
                variant="hero"
              />
            </div>
          </section>
        </section>

        <Dashboard
          stats={stats}
          loading={loading}
          error={error}
          connectionStatus={connectionStatus}
        />

        <section className="pulse-strip">
          {marketPulse.map((item) => (
            <article className="pulse-card" key={item.label}>
              <span>{item.label}</span>
              <strong>{loading ? '--' : item.value}</strong>
              <p>{item.note}</p>
            </article>
          ))}
        </section>

        <section className="content-panel" id="new">
          <div className="section-heading">
            <div>
              <p className="section-kicker">最新上线</p>
              <h3>刚进入地图的创业者</h3>
            </div>
            <p>参考 stitch 的首页顺序，把最新样本作为首个内容区，而不是塞进侧栏。</p>
          </div>

          <div className="listing-grid">
            {featuredEntrepreneur ? (
              <article className="listing-card listing-card--featured" key={featuredEntrepreneur.id}>
                <div className="listing-topline">
                  <span className="tag">{featuredEntrepreneur.track}</span>
                  <span>{formatRelativeTime(featuredEntrepreneur.createdAt)}</span>
                </div>
                <div className="listing-featured-body">
                  <div>
                    <h4>{featuredEntrepreneur.name}</h4>
                    <p>{formatLocation(featuredEntrepreneur)}</p>
                  </div>
                  <div className="listing-featured-mrr">
                    <span>本月经常性收入</span>
                    <strong>{formatCurrency(featuredEntrepreneur.mrr)}</strong>
                  </div>
                </div>
                <div className="listing-metrics">
                  <div>
                    <span>坐标</span>
                    <strong>{featuredEntrepreneur.lat}, {featuredEntrepreneur.lng}</strong>
                  </div>
                  <div>
                    <span>状态</span>
                    <strong>进入实时追踪</strong>
                  </div>
                </div>
              </article>
            ) : null}

            {remainingEntrepreneurs.map((item) => (
              <article className="listing-card" key={item.id}>
                <div className="listing-topline">
                  <span className="tag">{item.track}</span>
                  <span>{formatRelativeTime(item.createdAt)}</span>
                </div>
                <h4>{item.name}</h4>
                <p>{formatLocation(item)}</p>
                <div className="listing-metrics">
                  <div>
                    <span>MRR</span>
                    <strong>{formatCurrency(item.mrr)}</strong>
                  </div>
                  <div>
                    <span>坐标</span>
                    <strong>{item.lat}, {item.lng}</strong>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="content-panel leaderboard-panel" id="leaderboard">
          <div className="section-heading">
            <div>
              <p className="section-kicker">排行榜</p>
              <h3>按月经常性收入排列的头部创业者</h3>
            </div>
            <p>沿用 stitch 的榜单节奏，用表格把排名、城市、赛道和 MRR 摆到同一层读取。</p>
          </div>

          <div className="leaderboard-table-wrap">
            <table className="leaderboard-table">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>创业者</th>
                  <th>城市</th>
                  <th>赛道</th>
                  <th>月经常性收入</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((item, index) => (
                  <tr key={item.id}>
                    <td>
                      <span className="leaderboard-rank-badge">#{index + 1}</span>
                    </td>
                    <td>
                      <div className="leaderboard-person">
                        <strong>{item.name}</strong>
                        <span>{formatRelativeTime(item.createdAt)}</span>
                      </div>
                    </td>
                    <td>{formatLocation(item)}</td>
                    <td>{item.track}</td>
                    <td>{formatCurrency(item.mrr)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="insight-grid" id="insights">
          <section className="content-panel insight-panel">
            <div className="section-heading">
              <div>
                <p className="section-kicker">经营洞察</p>
                <h3>正在形成规模的方向</h3>
              </div>
              <p>用赛道规模、样本数量和城市覆盖度构成一组可比较的经营信号。</p>
            </div>
            <div className="track-chart-panel">
              <div className="track-chart-head">
                <div>
                  <span>赛道规模图</span>
                  <strong>按总 MRR 查看当前最强方向</strong>
                </div>
                <p>当前仅使用实时样本数据生成。</p>
              </div>
              <div className="track-chart">
                {trackChart.map((item) => (
                  <div className="track-chart__item" key={item.track}>
                    <div className="track-chart__value">{formatCompactCurrency(item.totalMrr)}</div>
                    <div className="track-chart__bar-wrap">
                      <div className="track-chart__bar" style={{ height: `${item.heightRatio}%` }} />
                    </div>
                    <div className="track-chart__label">{item.track}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="signal-list">
              {trackSummary.map((item) => (
                <article className="signal-card" key={item.track}>
                  <div className="signal-card__topline">
                    <strong>{item.track}</strong>
                    <span>{formatCompactCurrency(item.totalMrr)}</span>
                  </div>
                  <p>{item.count} 位创业者，覆盖 {item.cityCount} 座城市。</p>
                  <div className="signal-meter">
                    <span style={{ width: `${Math.min(100, (item.totalMrr / Math.max(stats.totalMrr || 1, 1)) * 100)}%` }} />
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="content-panel insight-panel">
            <div className="section-heading">
              <div>
                <p className="section-kicker">地区分布</p>
                <h3>高热城市</h3>
              </div>
              <p>把热点城市单独拿出来，方便和地球视图里的空间分布互相印证。</p>
            </div>
            <div className="city-spotlight-grid">
              {cityHighlights.map((city) => (
                <article className="city-spotlight-card" key={city.name}>
                  <span>{city.name}</span>
                  <strong>{city.founders} 位创业者</strong>
                  <p>{formatCompactCurrency(city.totalMrr)} 总 MRR</p>
                </article>
              ))}
            </div>
            <div className="insight-note">
              <strong>当前观察：</strong>
              高热城市与头部赛道正在形成更明显的聚集效应，地图、榜单和城市卡应当相互验证，而不是各自孤立。
            </div>
          </section>
        </section>

        <section className="content-panel service-panel" id="services">
          <div className="section-heading">
            <div>
              <p className="section-kicker">能力服务</p>
              <h3>把地图、榜单与加入入口接成一个完整工作流</h3>
            </div>
            <p>参考 stitch 的收尾方式，用一组能力卡总结这个首页到底能做什么。</p>
          </div>
          <div className="service-grid">
            {serviceCards.map((item) => (
              <article className="service-card" key={item.title}>
                <h4>{item.title}</h4>
                <p>{item.description}</p>
                <a href={item.title === '地图追踪' ? '#map' : item.title === '经营洞察' ? '#insights' : '#new'}>
                  进入模块
                </a>
              </article>
            ))}
          </div>
        </section>

        <section className="bottom-grid">
          <section className="content-panel trend-panel">
            <div className="section-heading">
              <div>
                <p className="section-kicker">趋势总览</p>
                <h3>把底部数据补成真正的收束区</h3>
              </div>
              <p>这一段专门承接参考项目最下面的补充信息密度，让首页不是在服务卡就结束。</p>
            </div>
            <div className="trend-grid">
              {trendCards.map((item) => (
                <article className="trend-card" key={item.title}>
                  <span>{item.title}</span>
                  <strong>{item.value}</strong>
                  <p>{item.description}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="content-panel cta-panel">
            <p className="section-kicker">继续进入</p>
            <h3>把创业者、赛道与城市放进同一个持续更新的情报界面。</h3>
            <p>如果你是创业者，进入地图；如果你在看市场，先从榜单和洞察开始。</p>
            <div className="cta-actions">
              <a className="primary-action" href="#map">继续看地图</a>
              <a className="secondary-action" href="#services">查看能力服务</a>
            </div>
          </section>
        </section>

        <footer className="site-footer">
          <div className="site-footer__brand">
            <div className="brand-mark">OPC</div>
            <div>
              <strong>中国创业者市场情报台</strong>
              <p>把地图、样本、排行和洞察收进一个持续更新的首页。</p>
            </div>
          </div>
          <div className="site-footer__links">
            {footerLinks.map((group) => (
              <div key={group.title}>
                <span>{group.title}</span>
                {group.items.map((item) => (
                  <p key={item}>{item}</p>
                ))}
              </div>
            ))}
          </div>
        </footer>
      </main>
    </div>
  )
}

export default App
