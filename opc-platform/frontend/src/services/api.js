const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

function joinPath(path) {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }

  if (path.startsWith('/')) {
    return `${API_BASE_URL}${path}`
  }

  return `${API_BASE_URL}/${path}`
}

function numberOrFallback(value, fallback = 0) {
  const numericValue = Number(value)
  return Number.isFinite(numericValue) ? numericValue : fallback
}

function toStartOfToday() {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return today
}

function pickFirstArray(payload) {
  const candidates = [
    payload?.data?.items,
    payload?.data?.list,
    payload?.data?.entrepreneurs,
    payload?.items,
    payload?.list,
    payload?.entrepreneurs,
    payload?.data,
    payload
  ]

  return candidates.find(Array.isArray) || []
}

function normalizeEntrepreneur(item = {}, index = 0) {
  const name = item.name || item.founder_name || item.nickname || `创业者 ${index + 1}`
  const city = item.city || item.location || '未知城市'
  const track = item.track || item.industry || item.category || '未分类'
  const province = item.province || item.region || ''

  return {
    ...item,
    id: item.id || item.registration_id || `${name}-${city}-${index}`,
    name,
    city,
    province,
    track,
    lat: item.lat ?? item.latitude,
    lng: item.lng ?? item.longitude,
    latitude: item.latitude ?? item.lat,
    longitude: item.longitude ?? item.lng,
    createdAt: item.createdAt || item.created_at || item.registered_at || null
  }
}

export function normalizeEntrepreneurPayload(payload) {
  return pickFirstArray(payload)
    .map((item, index) => normalizeEntrepreneur(item, index))
    .filter((item) => (item.latitude != null || item.lat != null) && (item.longitude != null || item.lng != null))
}

export function deriveStatsFromEntrepreneurs(entrepreneurs = []) {
  const today = toStartOfToday()
  const cities = new Set()
  const tracks = new Set()

  let todayNew = 0
  let totalMrr = 0

  entrepreneurs.forEach((item) => {
    if (item.city) {
      cities.add(item.city)
    }

    if (item.track) {
      tracks.add(item.track)
    }

    if (item.mrr != null) {
      totalMrr += numberOrFallback(item.mrr)
    }

    if (item.createdAt) {
      const createdAt = new Date(item.createdAt)
      if (!Number.isNaN(createdAt.getTime()) && createdAt >= today) {
        todayNew += 1
      }
    }
  })

  return {
    totalEntrepreneurs: entrepreneurs.length,
    todayNew,
    coveredCities: cities.size,
    activeTracks: tracks.size,
    totalMrr,
    lastUpdated: new Date().toISOString(),
    source: 'api'
  }
}

export function normalizeStatsPayload(payload, entrepreneurs = []) {
  const stats = payload?.data || payload?.stats || payload || {}
  const derivedStats = deriveStatsFromEntrepreneurs(entrepreneurs)

  return {
    totalEntrepreneurs: numberOrFallback(
      stats.totalEntrepreneurs ?? stats.entrepreneurs ?? stats.total ?? stats.total_count,
      derivedStats.totalEntrepreneurs
    ),
    todayNew: numberOrFallback(
      stats.todayNew ?? stats.today_new ?? stats.newToday ?? stats.new_registrations,
      derivedStats.todayNew
    ),
    coveredCities: numberOrFallback(
      stats.coveredCities ?? stats.cities ?? stats.cityCount,
      derivedStats.coveredCities
    ),
    activeTracks: numberOrFallback(
      stats.activeTracks ?? stats.tracks ?? stats.trackCount,
      derivedStats.activeTracks
    ),
    totalMrr: numberOrFallback(stats.totalMrr ?? stats.total_mrr, derivedStats.totalMrr),
    lastUpdated: stats.lastUpdated || stats.last_updated || derivedStats.lastUpdated,
    source: payload?.stats ? 'websocket' : 'api'
  }
}

// 获取认证头
function getAuthHeaders() {
  const token = localStorage.getItem('auth_token');
  const headers = {
    'Accept': 'application/json'
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
}

async function requestJson(paths, options = {}) {
  const errors = [];

  for (const path of paths) {
    const url = joinPath(path);

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...getAuthHeaders(),
          ...options.headers
        }
      });

      if (!response.ok) {
        // 如果是 401 错误，清除认证状态
        if (response.status === 401) {
          localStorage.removeItem('auth_token');
        }
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      errors.push(`${url} -> ${error.message}`);
    }
  }

  throw new Error(errors.join(' | '));
}

export async function fetchEntrepreneurs(filters = {}) {
  const params = new URLSearchParams();

  if (filters.search) {
    params.set('search', filters.search);
  }

  if (filters.track && filters.track !== 'ALL') {
    params.set('track', filters.track);
  }

  const suffix = params.toString() ? `?${params.toString()}` : '';
  const payload = await requestJson([
    `/entrepreneurs${suffix}`,
    `/registrations${suffix}`,
    `/dashboard/entrepreneurs${suffix}`
  ]);

  return normalizeEntrepreneurPayload(payload);
}

export async function fetchDashboardStats(entrepreneurs = []) {
  try {
    const payload = await requestJson([
      '/stats',
      '/stats/total',
      '/dashboard/stats'
    ]);

    return normalizeStatsPayload(payload, entrepreneurs);
  } catch (error) {
    return {
      ...deriveStatsFromEntrepreneurs(entrepreneurs),
      source: 'derived'
    };
  }
}

// 认证相关 API
export async function login(email, password) {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, password })
  });

  if (!response.ok) {
    throw new Error('登录失败');
  }

  const data = await response.json();

  // 存储 token
  localStorage.setItem('auth_token', data.token);

  return data;
}

export async function register(name, email, password) {
  const response = await fetch('/api/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ name, email, password })
  });

  if (!response.ok) {
    throw new Error('注册失败');
  }

  return await response.json();
}

export async function fetchProtectedEntrepreneurs(filters = {}) {
  const params = new URLSearchParams();

  if (filters.search) {
    params.set('search', filters.search);
  }

  if (filters.track && filters.track !== 'ALL') {
    params.set('track', filters.track);
  }

  const suffix = params.toString() ? `?${params.toString()}` : '';
  const payload = await requestJson([
    `/entrepreneurs/protected${suffix}`
  ]);

  return normalizeEntrepreneurPayload(payload);
}

export async function getCurrentUser() {
  try {
    const response = await fetch('/api/auth/me', {
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      localStorage.removeItem('auth_token');
      throw new Error('获取用户信息失败');
    }

    return await response.json();
  } catch (error) {
    localStorage.removeItem('auth_token');
    throw error;
  }
}

export function logout() {
  localStorage.removeItem('auth_token');
}

export function isAuthenticated() {
  return !!localStorage.getItem('auth_token');
}