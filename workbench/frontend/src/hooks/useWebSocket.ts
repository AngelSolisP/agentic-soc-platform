import { useEffect, useRef, useState, useCallback, useLayoutEffect } from 'react'

interface UseWebSocketOptions {
  url: string
  /** Query params appended to the WS URL (e.g. client_id, token) */
  params?: Record<string, string>
  onMessage?: (data: unknown) => void
  maxRetries?: number
  /** Skip connecting when false (e.g. before auth completes) */
  enabled?: boolean
}

const BASE_DELAY_MS = 1000
const MAX_DELAY_MS = 30_000
const MAX_JITTER_MS = 1000

/** Check if a JWT token is expired (with 60s buffer). */
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp * 1000 < Date.now() - 60_000
  } catch {
    return true
  }
}

function getBackoffDelay(attempt: number): number {
  const exponential = Math.min(BASE_DELAY_MS * Math.pow(2, attempt), MAX_DELAY_MS)
  const jitter = Math.random() * MAX_JITTER_MS
  return exponential + jitter
}

export function useWebSocket({ url, params, onMessage, maxRetries = 12, enabled = true }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()
  const attemptRef = useRef(0)
  const mountedRef = useRef(true)

  // Latest Ref pattern: store onMessage in a ref to avoid reconnection loops.
  // Without this, a new onMessage function on every render would trigger
  // useCallback → useEffect cleanup → WebSocket disconnect/reconnect storm.
  const onMessageRef = useRef(onMessage)
  useLayoutEffect(() => {
    onMessageRef.current = onMessage
  })

  // Serialize params to a stable string for the dependency array
  const paramsKey = params ? new URLSearchParams(params).toString() : ''

  const connect = useCallback(() => {
    if (!mountedRef.current) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const qs = paramsKey ? '?' + paramsKey : ''
    const wsUrl = `${protocol}//${window.location.host}${url}${qs}`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      attemptRef.current = 0
      setConnected(true)
    }
    ws.onclose = (event) => {
      setConnected(false)
      // Don't reconnect on normal closure or auth failures (4001-4003)
      if (event.code === 1000 || (event.code >= 4001 && event.code <= 4003)) return
      // Don't reconnect if token is expired — avoids infinite 403 loop
      const token = params?.token
      if (token && isTokenExpired(token)) return
      if (!mountedRef.current) return
      if (attemptRef.current >= maxRetries) return

      const delay = getBackoffDelay(attemptRef.current)
      attemptRef.current += 1
      reconnectTimer.current = setTimeout(connect, delay)
    }
    ws.onerror = () => {
      // Will trigger onclose → reconnect
    }
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'error') return
        onMessageRef.current?.(data)
      } catch {
        // Ignore non-JSON messages
      }
    }

    wsRef.current = ws
  }, [url, paramsKey, maxRetries])

  useEffect(() => {
    if (!enabled) return
    mountedRef.current = true
    connect()
    return () => {
      mountedRef.current = false
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close(1000, 'Component unmounted')
    }
  }, [connect, enabled])

  return { connected }
}
