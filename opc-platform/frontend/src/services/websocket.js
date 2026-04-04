/**
 * WebSocket 实时推送服务
 */
import { io } from 'socket.io-client'

function getDefaultSocketUrl() {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL
  }

  if (typeof window === 'undefined') {
    return 'ws://localhost:3001'
  }

  if (import.meta.env.DEV) {
    return 'ws://localhost:3001'
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}`
}

class WebSocketService {
  constructor() {
    this.socket = null
    this.listeners = {}
  }

  connect(url = getDefaultSocketUrl()) {
    if (this.socket) {
      return this.socket
    }

    this.socket = io(url, {
      path: import.meta.env.VITE_SOCKET_PATH || '/socket.io',
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 1000,
      timeout: 10000
    })

    this.socket.on('connect', () => {
      this.emit('connect', { id: this.socket.id })
      this.socket.emit('subscribe:registration')
      this.socket.emit('subscribe:investment')
    })

    this.socket.on('new_registration', (data) => {
      this.emit('new_registration', data)
    })

    this.socket.on('new_investment', (data) => {
      this.emit('new_investment', data)
    })

    this.socket.on('initial_data', (data) => {
      this.emit('initial_data', data)
    })

    this.socket.on('stats_update', (data) => {
      this.emit('stats_update', data)
    })

    this.socket.on('disconnect', (reason) => {
      this.emit('disconnect', { reason })
    })

    this.socket.on('connect_error', (error) => {
      this.emit('connect_error', error)
    })

    return this.socket
  }

  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = new Set()
    }

    this.listeners[event].add(callback)
    return () => this.off(event, callback)
  }

  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].delete(callback)
    }
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach((callback) => callback(data))
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }
}

export default new WebSocketService()
