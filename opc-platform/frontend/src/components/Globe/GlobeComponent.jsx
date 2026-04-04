import { useEffect, useMemo, useRef, useState } from 'react'
import * as THREE from 'three'
import Globe from 'globe.gl'
import { sanitizeEntrepreneurDataset } from '../../utils/compliance'

const TRACK_COLORS = {
  AI: '#ff6b6b',
  电商: '#51cf66',
  内容: '#4dabf7',
  跨境: '#ffd43b',
  教育: '#da77f2'
}

function getTrackColor(track) {
  return TRACK_COLORS[track] || '#91a7ff'
}

function hexToRgba(hex, alpha) {
  const normalized = hex.replace('#', '')
  const safeHex = normalized.length === 3
    ? normalized.split('').map((char) => char + char).join('')
    : normalized

  const value = Number.parseInt(safeHex, 16)
  const red = (value >> 16) & 255
  const green = (value >> 8) & 255
  const blue = value & 255

  return `rgba(${red}, ${green}, ${blue}, ${alpha})`
}

const DEFAULT_GLOBE_TEXTURE_URL = 'https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-blue-marble.jpg'
const DEFAULT_GLOBE_NIGHT_URL = 'https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg'
const DEFAULT_GLOBE_BUMP_URL = 'https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-topology.png'
const DEFAULT_GLOBE_BACKGROUND_URL = 'https://cdn.jsdelivr.net/npm/three-globe/example/img/night-sky.png'
const DEFAULT_GLOBE_CLOUDS_URL = 'https://cdn.jsdelivr.net/npm/globe.gl/example/clouds/clouds.png'

const globeTextureUrl = import.meta.env.VITE_GLOBE_IMAGE_URL || DEFAULT_GLOBE_TEXTURE_URL
const globeNightTextureUrl = import.meta.env.VITE_GLOBE_NIGHT_IMAGE_URL || DEFAULT_GLOBE_NIGHT_URL
const globeBumpUrl = import.meta.env.VITE_GLOBE_BUMP_URL || DEFAULT_GLOBE_BUMP_URL
const globeBackgroundUrl = import.meta.env.VITE_GLOBE_BG_IMAGE_URL || DEFAULT_GLOBE_BACKGROUND_URL
const globeCloudsTextureUrl = import.meta.env.VITE_GLOBE_CLOUDS_IMAGE_URL || DEFAULT_GLOBE_CLOUDS_URL

const DAY_NIGHT_SHADER = {
  vertexShader: `
    varying vec3 vNormal;
    varying vec2 vUv;

    void main() {
      vNormal = normalize(normalMatrix * normal);
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: `
    uniform sampler2D dayTexture;
    uniform sampler2D nightTexture;
    uniform vec3 sunDirection;
    varying vec3 vNormal;
    varying vec2 vUv;

    void main() {
      float intensity = dot(normalize(vNormal), normalize(sunDirection));
      vec4 dayColor = texture2D(dayTexture, vUv);
      vec4 nightColor = texture2D(nightTexture, vUv);
      float blendFactor = smoothstep(-0.18, 0.12, intensity);
      vec3 twilightTint = vec3(1.02, 0.58, 0.24) * pow(1.0 - abs(intensity), 3.0) * 0.22;
      vec3 mixedColor = mix(nightColor.rgb, dayColor.rgb, blendFactor) + twilightTint;
      gl_FragColor = vec4(mixedColor, 1.0);
    }
  `
}

function formatCurrency(value) {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    maximumFractionDigits: 0
  }).format(Number(value) || 0)
}

function formatLocation(item) {
  const province = item?.province || ''
  const city = item?.city || '未知城市'

  if (!province || province === city) {
    return city
  }

  return `${province} · ${city}`
}

function formatRelativeTime(value) {
  if (!value) {
    return '刚刚进入追踪'
  }

  const timestamp = new Date(value).getTime()
  if (Number.isNaN(timestamp)) {
    return '刚刚进入追踪'
  }

  const diffMinutes = Math.max(0, Math.round((Date.now() - timestamp) / 60000))

  if (diffMinutes < 1) {
    return '刚刚进入追踪'
  }

  if (diffMinutes < 60) {
    return `${diffMinutes} 分钟前进入追踪`
  }

  const diffHours = Math.round(diffMinutes / 60)
  if (diffHours < 24) {
    return `${diffHours} 小时前进入追踪`
  }

  const diffDays = Math.round(diffHours / 24)
  return `${diffDays} 天前进入追踪`
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function deriveCharacterProfile(item) {
  if (!item) {
    return null
  }

  const mrr = Number(item.mrr) || 0
  const ageHours = item.createdAt
    ? Math.max(1, (Date.now() - new Date(item.createdAt).getTime()) / 3600000)
    : 1

  let tier = '观察中'
  if (mrr >= 150000) {
    tier = '传奇档'
  } else if (mrr >= 90000) {
    tier = '史诗档'
  } else if (mrr >= 40000) {
    tier = '稀有档'
  }

  const momentum = clamp(Math.round(42 + (mrr / 5000) + (24 / ageHours)), 18, 98)
  const execution = clamp(Math.round(34 + (mrr / 3500) + ((item.track?.length || 2) * 4)), 20, 97)
  const expansion = clamp(Math.round(28 + ((item.city?.length || 2) * 7) + (mrr / 8000)), 16, 96)

  const keywords = [
    `${item.track || '综合'}主线`,
    ageHours < 24 ? '新近活跃' : '持续追踪',
    mrr >= 100000 ? '高收入密度' : '增长窗口',
    item.city ? `${item.city}据点` : '城市待补全'
  ]

  return {
    tier,
    title: `${item.track || '综合'} 创业者`,
    mission: ageHours < 24 ? '处于新近抬升期，适合优先观察。' : '已进入稳定追踪，可持续比对走势。',
    stats: [
      { label: '动能', value: momentum },
      { label: '执行', value: execution },
      { label: '扩张', value: expansion }
    ],
    keywords
  }
}

function getTrackPalette(track) {
  const color = getTrackColor(track)

  return {
    accent: color,
    soft: hexToRgba(color, 0.2),
    glow: hexToRgba(color, 0.36)
  }
}

function getSunCoordinates(date = new Date()) {
  const year = date.getUTCFullYear()
  const month = date.getUTCMonth()
  const day = date.getUTCDate()
  const dayOfYear = Math.floor((Date.UTC(year, month, day) - Date.UTC(year, 0, 0)) / 86400000)
  const utcHours = date.getUTCHours() + (date.getUTCMinutes() / 60) + (date.getUTCSeconds() / 3600)
  const latitude = -23.44 * Math.cos((2 * Math.PI / 365) * (dayOfYear + 10))
  const longitude = (12 - utcHours) * 15

  return { latitude, longitude }
}

function solarVector(date = new Date()) {
  const { latitude, longitude } = getSunCoordinates(date)
  const latRad = latitude * Math.PI / 180
  const lngRad = longitude * Math.PI / 180

  return new THREE.Vector3(
    Math.cos(latRad) * Math.cos(lngRad),
    Math.sin(latRad),
    Math.cos(latRad) * Math.sin(lngRad)
  )
}

function GlobeComponent({ entrepreneurs = [], loading, error, variant = 'default' }) {
  const stageRef = useRef(null)
  const cardRef = useRef(null)
  const globeContainerRef = useRef(null)
  const globeInstanceRef = useRef(null)
  const resizeObserverRef = useRef(null)
  const cloudMeshRef = useRef(null)
  const cloudAnimationRef = useRef(0)
  const globeMaterialRef = useRef(null)
  const controlsRef = useRef(null)
  const connectorFrameRef = useRef(0)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [selectedTrack, setSelectedTrack] = useState('ALL')
  const [selectedPoint, setSelectedPoint] = useState(null)
  const [hoveredPoint, setHoveredPoint] = useState(null)
  const [cardLink, setCardLink] = useState(null)

  const compliantEntrepreneurs = useMemo(
    () => sanitizeEntrepreneurDataset(entrepreneurs, { source: 'wgs84', precision: 2 }),
    [entrepreneurs]
  )

  const trackOptions = useMemo(
    () => ['ALL', ...new Set(compliantEntrepreneurs.map((item) => item.track).filter(Boolean))],
    [compliantEntrepreneurs]
  )

  const filteredEntrepreneurs = useMemo(() => {
    const normalizedKeyword = searchKeyword.trim().toLowerCase()

    return compliantEntrepreneurs.filter((item) => {
      const matchesTrack = selectedTrack === 'ALL' || item.track === selectedTrack
      const matchesKeyword = !normalizedKeyword || [
        item.name,
        item.city,
        item.province,
        item.track
      ].filter(Boolean).some((value) => value.toLowerCase().includes(normalizedKeyword))

      return matchesTrack && matchesKeyword
    })
  }, [compliantEntrepreneurs, searchKeyword, selectedTrack])

  const spotlightEntrepreneurs = useMemo(() => (
    [...filteredEntrepreneurs]
      .sort((left, right) => (Number(right.mrr) || 0) - (Number(left.mrr) || 0))
      .slice(0, 4)
  ), [filteredEntrepreneurs])
  const selectedProfile = useMemo(() => deriveCharacterProfile(selectedPoint), [selectedPoint])

  useEffect(() => {
    if (!filteredEntrepreneurs.length) {
      setSelectedPoint(null)
      setHoveredPoint(null)
      return
    }

    setSelectedPoint((currentValue) => (
      filteredEntrepreneurs.find((item) => item.id === currentValue?.id) || null
    ))
  }, [filteredEntrepreneurs])

  const activePoint = hoveredPoint || selectedPoint || null

  const focusOnPoint = (point, duration = 900) => {
    if (!point || !globeInstanceRef.current) {
      return
    }

    globeInstanceRef.current.pointOfView({ lat: point.lat, lng: point.lng, altitude: 1.15 }, duration)

    if (controlsRef.current) {
      controlsRef.current.autoRotate = false
    }
  }

  const selectPoint = (point, duration = 900) => {
    if (!point) {
      return
    }

    setSelectedPoint(point)
    setHoveredPoint(null)
    focusOnPoint(point, duration)
  }

  useEffect(() => {
    if (!globeContainerRef.current || globeInstanceRef.current) {
      return undefined
    }

    const globe = new Globe(globeContainerRef.current, { waitForGlobeReady: false })
    globeInstanceRef.current = globe

    globe
      .backgroundColor('#040816')
      .showGraticules(false)
      .showAtmosphere(true)
      .atmosphereColor('#7ec8ff')
      .atmosphereAltitude(0.13)
      .globeImageUrl(globeTextureUrl)
      .bumpImageUrl(globeBumpUrl)
      .backgroundImageUrl(globeBackgroundUrl)

    const textureLoader = new THREE.TextureLoader()
    Promise.all([
      textureLoader.loadAsync(globeTextureUrl),
      textureLoader.loadAsync(globeNightTextureUrl)
    ]).then(([dayTexture, nightTexture]) => {
      if (!globeInstanceRef.current) {
        return
      }

      const material = new THREE.ShaderMaterial({
        uniforms: {
          dayTexture: { value: dayTexture },
          nightTexture: { value: nightTexture },
          sunDirection: { value: new THREE.Vector3(1, 0, 0) }
        },
        vertexShader: DAY_NIGHT_SHADER.vertexShader,
        fragmentShader: DAY_NIGHT_SHADER.fragmentShader
      })

      globeMaterialRef.current = material
      globe.globeMaterial(material)
    }).catch(() => {
      const fallbackMaterial = globe.globeMaterial()
      if (fallbackMaterial?.color?.set) {
        fallbackMaterial.color.set('#ffffff')
      }
      if (fallbackMaterial?.emissive?.set) {
        fallbackMaterial.emissive.set('#0a1428')
        fallbackMaterial.emissiveIntensity = 0.28
      }
      if ('shininess' in fallbackMaterial) {
        fallbackMaterial.shininess = 12
      }
    })

    textureLoader.load(globeCloudsTextureUrl, (cloudTexture) => {
      if (!globeInstanceRef.current) {
        return
      }

      const clouds = new THREE.Mesh(
        new THREE.SphereGeometry(globe.getGlobeRadius() * 1.007, 72, 72),
        new THREE.MeshPhongMaterial({
          map: cloudTexture,
          transparent: true,
          opacity: 0.32,
          depthWrite: false
        })
      )

      cloudMeshRef.current = clouds
      globe.scene().add(clouds)

      const animateScene = () => {
        if (!cloudMeshRef.current) {
          return
        }

        cloudMeshRef.current.rotation.y += -0.0009
        if (globeMaterialRef.current) {
          const camera = globe.camera()
          const viewSunDirection = solarVector().transformDirection(camera.matrixWorldInverse)
          globeMaterialRef.current.uniforms.sunDirection.value.copy(viewSunDirection)
        }
        cloudAnimationRef.current = requestAnimationFrame(animateScene)
      }

      animateScene()
    })

    const syncGlobeSize = () => {
      const width = globeContainerRef.current?.clientWidth || 0
      const height = globeContainerRef.current?.clientHeight || 0

      if (width > 0 && height > 0) {
        globe.width(width)
        globe.height(height)
      }
    }

    syncGlobeSize()
    resizeObserverRef.current = new ResizeObserver(syncGlobeSize)
    resizeObserverRef.current.observe(globeContainerRef.current)

    globe.pointOfView({ lat: 35.8617, lng: 104.1954, altitude: 1.95 })

    const controls = globe.controls()
    controlsRef.current = controls
    controls.autoRotate = true
    controls.autoRotateSpeed = 0.35
    controls.enablePan = false

    controls.addEventListener('start', () => {
      controls.autoRotate = false
    })

    return () => {
      if (cloudAnimationRef.current) {
        cancelAnimationFrame(cloudAnimationRef.current)
        cloudAnimationRef.current = 0
      }
      if (cloudMeshRef.current) {
        globe.scene().remove(cloudMeshRef.current)
        cloudMeshRef.current.geometry.dispose()
        cloudMeshRef.current.material.dispose()
        cloudMeshRef.current = null
      }
      if (globeMaterialRef.current) {
        globeMaterialRef.current.dispose()
        globeMaterialRef.current = null
      }
      resizeObserverRef.current?.disconnect()
      resizeObserverRef.current = null
      if (globeContainerRef.current) {
        globeContainerRef.current.innerHTML = ''
      }
      controlsRef.current = null
      globeInstanceRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!globeInstanceRef.current) {
      return
    }

    const ringsData = filteredEntrepreneurs.slice(0, 10)

    globeInstanceRef.current
      .pointsData([])
      .htmlElementsData(filteredEntrepreneurs)
      .htmlLat((item) => item.lat)
      .htmlLng((item) => item.lng)
      .htmlAltitude((item) => item.id === activePoint?.id ? 0.014 : 0.008)
      .htmlElement((item) => {
        const marker = document.createElement('button')
        const palette = getTrackPalette(item.track)
        const isActive = item.id === activePoint?.id

        marker.type = 'button'
        marker.className = `globe-marker${isActive ? ' globe-marker--active' : ''}`
        marker.dataset.pointId = String(item.id)
        marker.setAttribute('aria-label', `${item.name}，${item.track}，${formatLocation(item)}`)
        marker.style.setProperty('--marker-color', palette.accent)
        marker.style.setProperty('--marker-glow', palette.glow)

        marker.innerHTML = '<span></span>'
        marker.onmouseenter = () => setHoveredPoint(item)
        marker.onmouseleave = () => setHoveredPoint((current) => (current?.id === item.id ? null : current))
        marker.onpointerdown = (event) => {
          event.preventDefault()
          event.stopPropagation()
          selectPoint(item, 650)
        }
        marker.onclick = (event) => {
          event.preventDefault()
          event.stopPropagation()
          selectPoint(item, 650)
        }

        return marker
      })
      .htmlTransitionDuration(250)
      .ringsData(ringsData)
      .ringLat((item) => item.lat)
      .ringLng((item) => item.lng)
      .ringColor((item) => [hexToRgba(getTrackColor(item.track), 0.9), 'rgba(255,255,255,0.06)'])
      .ringMaxRadius((item) => item.id === activePoint?.id ? 3.6 : 2.2)
      .ringPropagationSpeed(1.25)
      .ringRepeatPeriod((item) => item.id === activePoint?.id ? 880 : 1350)

    if (activePoint) {
      focusOnPoint(activePoint, 700)
    }
  }, [activePoint, filteredEntrepreneurs])

  useEffect(() => {
    if (!selectedPoint || !stageRef.current || !cardRef.current) {
      setCardLink(null)
      return undefined
    }

    let isMounted = true

    const updateCardLink = () => {
      const stage = stageRef.current
      const card = cardRef.current
      const marker = stage?.querySelector(`[data-point-id="${selectedPoint.id}"]`)

      if (!stage || !card || !marker) {
        if (isMounted) {
          setCardLink(null)
        }
        connectorFrameRef.current = requestAnimationFrame(updateCardLink)
        return
      }

      const stageRect = stage.getBoundingClientRect()
      const markerRect = marker.getBoundingClientRect()
      const cardRect = card.getBoundingClientRect()
      const startX = markerRect.left - stageRect.left + (markerRect.width / 2)
      const startY = markerRect.top - stageRect.top + (markerRect.height / 2)
      const endX = cardRect.right - stageRect.left - 26
      const endY = cardRect.top - stageRect.top + 36
      const deltaX = endX - startX
      const deltaY = endY - startY

      if (isMounted) {
        setCardLink({
          x: startX,
          y: startY,
          length: Math.sqrt((deltaX ** 2) + (deltaY ** 2)),
          angle: Math.atan2(deltaY, deltaX) * (180 / Math.PI)
        })
      }

      connectorFrameRef.current = requestAnimationFrame(updateCardLink)
    }

    updateCardLink()

    return () => {
      isMounted = false
      if (connectorFrameRef.current) {
        cancelAnimationFrame(connectorFrameRef.current)
        connectorFrameRef.current = 0
      }
    }
  }, [selectedPoint])

  return (
    <div className={`globe-module${variant === 'hero' ? ' globe-module--hero' : ''}`}>
      <div className="globe-sidebar">
        <div className="globe-sidebar-head">
          <div>
            <p className="section-kicker">地理图层</p>
            <h4>创业者分布</h4>
          </div>
          <span className="status-chip">点位 · {loading ? '--' : filteredEntrepreneurs.length}</span>
        </div>

        <div className="globe-toolbar">
          <input
            value={searchKeyword}
            onChange={(event) => setSearchKeyword(event.target.value)}
            placeholder="搜索姓名 / 城市 / 赛道"
            className="globe-input"
          />
          <select
            value={selectedTrack}
            onChange={(event) => setSelectedTrack(event.target.value)}
            className="globe-select"
          >
          {trackOptions.map((track) => (
            <option key={track} value={track}>{track === 'ALL' ? '全部赛道' : track}</option>
          ))}
          </select>
        </div>

        <div className="globe-notes">
          <div>坐标策略：<strong>统一转为 GCJ-02 + 2 位小数</strong></div>
          <div>渲染模式：<strong>即使贴图缺失也先渲染球体</strong></div>
          {error ? <div className="dashboard-error">接口提示：{error}</div> : null}
        </div>

        <div className="globe-legend">
          {trackOptions.filter((item) => item !== 'ALL').map((track) => (
            <button
              key={track}
              type="button"
              className={`legend-chip${selectedTrack === track ? ' legend-chip--active' : ''}`}
              onClick={() => setSelectedTrack((currentValue) => (currentValue === track ? 'ALL' : track))}
            >
              <span className="legend-dot" style={{ backgroundColor: getTrackColor(track) }} />
              {track}
            </button>
          ))}
        </div>

        <div className="globe-focus-card">
          <p className="section-kicker">当前焦点</p>
          {activePoint ? (
            <>
          <div className="globe-focus-topline">
            <strong>{activePoint.name}</strong>
            <span className="tag">{activePoint.track}</span>
          </div>
              <p>{formatLocation(activePoint)}</p>
              <div className="globe-focus-metrics">
                <div>
                  <span>MRR</span>
                  <strong>{formatCurrency(activePoint.mrr)}</strong>
                </div>
                <div>
                  <span>坐标</span>
                  <strong>{activePoint.lat}, {activePoint.lng}</strong>
                </div>
              </div>
            </>
          ) : (
            <p>当前筛选下没有可展示的创业者。</p>
          )}
        </div>

        <div className="globe-list">
          <div className="globe-list-head">
            <p className="section-kicker">精选名单</p>
            <span>{spotlightEntrepreneurs.length} 条</span>
          </div>
          {spotlightEntrepreneurs.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`globe-list-item${activePoint?.id === item.id ? ' globe-list-item--active' : ''}`}
              onClick={() => selectPoint(item, 650)}
            >
              <div>
                <strong>{item.name}</strong>
                <p>{formatLocation(item)} · {item.track}</p>
              </div>
              <span>{formatCurrency(item.mrr)}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="globe-stage" ref={stageRef}>
        <div className="globe-canvas" ref={globeContainerRef} />
        {selectedPoint && cardLink ? (
          <div
            className="globe-character-link"
            style={{
              left: `${cardLink.x}px`,
              top: `${cardLink.y}px`,
              width: `${cardLink.length}px`,
              transform: `rotate(${cardLink.angle}deg)`,
              '--link-color': getTrackPalette(selectedPoint.track).accent
            }}
          >
            <span />
          </div>
        ) : null}
        {selectedPoint ? (
          <div
            className="globe-character-card"
            ref={cardRef}
            style={{
              '--card-accent': getTrackPalette(selectedPoint.track).accent,
              '--card-accent-soft': getTrackPalette(selectedPoint.track).soft,
              '--card-accent-glow': getTrackPalette(selectedPoint.track).glow
            }}
          >
            <div className="globe-character-card__topline">
              <span className="globe-character-card__eyebrow">创业者档案</span>
              <div className="globe-character-card__badges">
                <span className="globe-character-card__rarity">{selectedProfile?.tier}</span>
                <span className="globe-character-card__status">实时追踪中</span>
              </div>
            </div>
            <div className="globe-character-card__identity">
              <div className="globe-character-card__crest" style={{ '--track-color': getTrackColor(selectedPoint.track) }}>
                {selectedPoint.name?.slice(0, 1) || '创'}
              </div>
              <div>
                <h5>{selectedPoint.name}</h5>
                <p>{formatLocation(selectedPoint)} · {selectedProfile?.title}</p>
              </div>
            </div>
            <p className="globe-character-card__summary">{formatRelativeTime(selectedPoint.createdAt)}</p>
            <div className="globe-character-card__signals">
              {selectedProfile?.stats.slice(0, 2).map((item) => (
                <div className="globe-character-card__signal" key={item.label}>
                  <div className="globe-character-card__signal-head">
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                  </div>
                  <div className="globe-character-card__signal-bar">
                    <i style={{ width: `${item.value}%`, backgroundColor: getTrackColor(selectedPoint.track) }} />
                  </div>
                </div>
              ))}
            </div>
            <div className="globe-character-card__meta">
              <div>
                <span>经营与地图关联</span>
                <strong>{formatCurrency(selectedPoint.mrr)} · {selectedPoint.track} · {selectedPoint.lat}, {selectedPoint.lng}</strong>
              </div>
            </div>
            <div className="globe-character-card__details">
              <div>
                <span>赛道</span>
                <strong>{selectedPoint.track}</strong>
              </div>
              <div>
                <span>城市</span>
                <strong>{formatLocation(selectedPoint)}</strong>
              </div>
              <div>
                <span>坐标</span>
                <strong>{selectedPoint.lat}, {selectedPoint.lng}</strong>
              </div>
              <div>
                <span>编号</span>
                <strong>#{String(selectedPoint.id).slice(-6)}</strong>
              </div>
            </div>
            <div className="globe-character-card__footer">
              <button
                type="button"
                className="globe-character-card__close"
                onClick={() => setSelectedPoint(null)}
              >
                收起卡片
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}

export default GlobeComponent
