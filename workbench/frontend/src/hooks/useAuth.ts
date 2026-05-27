import { createContext, useContext, useState, useEffect, useCallback, ReactNode, createElement } from 'react'
import { api, AnalystMe, setAuthToken, getAuthToken } from '@/services/api'

export interface AnalystProfile {
  email: string
  role: 'analyst' | 'admin'
  allowed_clients: string[]
}

interface AuthContextType {
  analyst: AnalystProfile | null
  isAdmin: boolean
  loading: boolean
  login: (credential: string) => void
  logout: () => void
}

export const AuthContext = createContext<AuthContextType>({
  analyst: null,
  isAdmin: false,
  loading: true,
  login: () => {},
  logout: () => {},
})

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [analyst, setAnalyst] = useState<AnalystProfile | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchMe = useCallback(async () => {
    try {
      const data: AnalystMe = await api.me()
      setAnalyst({ email: data.email, role: data.role, allowed_clients: data.allowed_clients })
    } catch {
      setAnalyst(null)
      setAuthToken(null)
    } finally {
      setLoading(false)
    }
  }, [])

  // On mount, try stored token
  useEffect(() => {
    const stored = getAuthToken()
    if (stored) {
      fetchMe()
    } else {
      setLoading(false)
    }
  }, [fetchMe])

  const login = useCallback((credential: string) => {
    setAuthToken(credential)
    setLoading(true)
    fetchMe()
  }, [fetchMe])

  const logout = useCallback(() => {
    setAuthToken(null)
    setAnalyst(null)
  }, [])

  const value: AuthContextType = {
    analyst,
    isAdmin: analyst?.role === 'admin',
    loading,
    login,
    logout,
  }

  return createElement(AuthContext.Provider, { value }, children)
}
