/**
 * 合规工具模块
 * GCJ-02 坐标转换、数据脱敏
 */

const EARTH_A = 6378245.0
const EARTH_EE = 0.00669342162296594323
const PI = Math.PI

function transformLatitude(x, y) {
  let result = -100.0 + (2.0 * x) + (3.0 * y) + (0.2 * y * y) + (0.1 * x * y) + (0.2 * Math.sqrt(Math.abs(x)))
  result += ((20.0 * Math.sin(6.0 * x * PI)) + (20.0 * Math.sin(2.0 * x * PI))) * 2.0 / 3.0
  result += ((20.0 * Math.sin(y * PI)) + (40.0 * Math.sin((y / 3.0) * PI))) * 2.0 / 3.0
  result += ((160.0 * Math.sin((y / 12.0) * PI)) + (320.0 * Math.sin((y * PI) / 30.0))) * 2.0 / 3.0
  return result
}

function transformLongitude(x, y) {
  let result = 300.0 + x + (2.0 * y) + (0.1 * x * x) + (0.1 * x * y) + (0.1 * Math.sqrt(Math.abs(x)))
  result += ((20.0 * Math.sin(6.0 * x * PI)) + (20.0 * Math.sin(2.0 * x * PI))) * 2.0 / 3.0
  result += ((20.0 * Math.sin(x * PI)) + (40.0 * Math.sin((x / 3.0) * PI))) * 2.0 / 3.0
  result += ((150.0 * Math.sin((x / 12.0) * PI)) + (300.0 * Math.sin((x / 30.0) * PI))) * 2.0 / 3.0
  return result
}

export function isValidChinaCoordinate(lat, lng) {
  return lat >= 18 && lat <= 54 && lng >= 73 && lng <= 135
}

function normalizeCoordinateValue(value) {
  const numericValue = Number(value)
  return Number.isFinite(numericValue) ? numericValue : null
}

/**
 * WGS-84 转 GCJ-02
 */
export function wgs84ToGcj02(lat, lng) {
  const normalizedLat = normalizeCoordinateValue(lat)
  const normalizedLng = normalizeCoordinateValue(lng)

  if (normalizedLat === null || normalizedLng === null) {
    return { lat: null, lng: null }
  }

  if (!isValidChinaCoordinate(normalizedLat, normalizedLng)) {
    return { lat: normalizedLat, lng: normalizedLng }
  }

  const deltaLat = transformLatitude(normalizedLng - 105.0, normalizedLat - 35.0)
  const deltaLng = transformLongitude(normalizedLng - 105.0, normalizedLat - 35.0)
  const radLat = normalizedLat / 180.0 * PI
  const magic = Math.sin(radLat)
  const adjustedMagic = 1 - (EARTH_EE * magic * magic)
  const sqrtMagic = Math.sqrt(adjustedMagic)

  const latitudeOffset = (deltaLat * 180.0) / (((EARTH_A * (1 - EARTH_EE)) / (adjustedMagic * sqrtMagic)) * PI)
  const longitudeOffset = (deltaLng * 180.0) / ((EARTH_A / sqrtMagic) * Math.cos(radLat) * PI)

  return {
    lat: normalizedLat + latitudeOffset,
    lng: normalizedLng + longitudeOffset
  }
}

/**
 * 坐标脱敏（保留 2 位小数，城市级精度）
 */
export function desensitizeCoordinate(value, precision = 2) {
  const numericValue = normalizeCoordinateValue(value)

  if (numericValue === null) {
    return null
  }

  const scale = 10 ** precision
  return Math.round(numericValue * scale) / scale
}

export function toCompliantCoordinate(lat, lng, options = {}) {
  const { precision = 2, source = 'wgs84' } = options
  const normalizedLat = normalizeCoordinateValue(lat)
  const normalizedLng = normalizeCoordinateValue(lng)

  if (normalizedLat === null || normalizedLng === null) {
    return null
  }

  const gcj02Coordinate = source === 'gcj02'
    ? { lat: normalizedLat, lng: normalizedLng }
    : wgs84ToGcj02(normalizedLat, normalizedLng)

  return {
    lat: desensitizeCoordinate(gcj02Coordinate.lat, precision),
    lng: desensitizeCoordinate(gcj02Coordinate.lng, precision)
  }
}

/**
 * 数据脱敏处理
 */
export function desensitizeData(data, options = {}) {
  if (!data) {
    return null
  }

  const coordinate = toCompliantCoordinate(
    data.latitude ?? data.lat,
    data.longitude ?? data.lng,
    options
  )

  return {
    ...data,
    lat: coordinate?.lat ?? null,
    lng: coordinate?.lng ?? null,
    latitude: coordinate?.lat ?? null,
    longitude: coordinate?.lng ?? null,
    ip: undefined,
    ip_hash: undefined,
    phone: undefined,
    email: undefined
  }
}

export function sanitizeEntrepreneurLocation(data, options = {}) {
  const sanitizedData = desensitizeData(data, options)

  if (sanitizedData?.lat == null || sanitizedData?.lng == null) {
    return null
  }

  return sanitizedData
}

export function sanitizeEntrepreneurDataset(dataset = [], options = {}) {
  return dataset
    .map((item) => sanitizeEntrepreneurLocation(item, options))
    .filter(Boolean)
}

/**
 * 获取城市级定位（从 IP 或其他信息）
 */
export function getCityLocation() {
  return {
    province: '广东省',
    city: '深圳市',
    latitude: 22.54,
    longitude: 114.06
  }
}
