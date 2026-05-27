import { lazy, Suspense, useState, useCallback, useEffect, useRef } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Box, AppBar, Toolbar, Typography, Button, Tabs, Tab, CircularProgress, Chip, Snackbar, Alert, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions } from '@mui/material'
import { useNavigate, useLocation } from 'react-router-dom'
import { GoogleLogin } from '@react-oauth/google'
import Dashboard from '@/pages/Dashboard'
import CaseDetail from '@/pages/CaseDetail'
import Watchlists from '@/pages/Watchlists'
import { useAuth } from '@/hooks/useAuth'
import { useWebSocket } from '@/hooks/useWebSocket'
import { getAuthToken } from '@/services/api'
import { socTokens } from '@/theme/dark'

const AdminDashboard = lazy(() => import('@/pages/admin/AdminDashboard'))
const ClientManagement = lazy(() => import('@/pages/admin/ClientManagement'))
const AnalystAssignment = lazy(() => import('@/pages/admin/AnalystAssignment'))
const AgentPerformance = lazy(() => import('@/pages/admin/AgentPerformance'))
const AuditLog = lazy(() => import('@/pages/admin/AuditLog'))

const MAX_TOASTS = 3

interface ToastNotification {
  id: number
  message: string
  severity: 'info' | 'warning' | 'success' | 'error'
}

interface WsNotificationEvent {
  type: string
  client_id?: string
  case_id?: string
  alert_type?: string
  stage_name?: string
  status?: string
}

function formatNotification(event: WsNotificationEvent): { message: string; severity: ToastNotification['severity'] } {
  switch (event.type) {
    case 'new_case':
      return {
        message: `New case ${event.case_id ?? 'unknown'} (${event.alert_type ?? 'ALERT'}) for ${event.client_id ?? 'unknown client'}`,
        severity: 'info',
      }
    case 'stage_complete':
      return {
        message: `Stage "${event.stage_name ?? ''}" completed for case ${event.case_id ?? ''}`,
        severity: 'success',
      }
    case 'stage_error':
      return {
        message: `Stage "${event.stage_name ?? ''}" failed for case ${event.case_id ?? ''}`,
        severity: 'error',
      }
    case 'escalation':
      return {
        message: `Case ${event.case_id ?? ''} escalated for ${event.client_id ?? ''}`,
        severity: 'warning',
      }
    default:
      return {
        message: `Notification: ${event.type}`,
        severity: 'info',
      }
  }
}

function getAdminTab(pathname: string): string {
  if (pathname.startsWith('/admin/clients')) return '/admin/clients'
  if (pathname.startsWith('/admin/analysts')) return '/admin/analysts'
  if (pathname.startsWith('/admin/performance')) return '/admin/performance'
  if (pathname.startsWith('/admin/audit')) return '/admin/audit'
  return '/admin'
}

export default function App() {
  const navigate = useNavigate()
  const location = useLocation()
  const { analyst, isAdmin, loading, login, logout } = useAuth()

  // Session expiry state
  const [sessionExpired, setSessionExpired] = useState(false)

  useEffect(() => {
    const handler = () => setSessionExpired(true)
    window.addEventListener('auth:expired', handler)
    return () => window.removeEventListener('auth:expired', handler)
  }, [])

  // Notification toast state
  const [toasts, setToasts] = useState<ToastNotification[]>([])
  const nextId = useRef(0)

  const handleNotification = useCallback((data: unknown) => {
    const event = data as WsNotificationEvent
    if (!event.type) return
    const { message, severity } = formatNotification(event)
    const id = nextId.current++
    setToasts((prev) => [...prev.slice(-(MAX_TOASTS - 1)), { id, message, severity }])
  }, [])

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  // Connect to notification WebSocket (only when authenticated)
  const wsToken = analyst ? getAuthToken() : null
  useWebSocket({
    url: '/ws/notifications',
    params: wsToken ? { token: wsToken } : undefined,
    onMessage: handleNotification,
    maxRetries: 15,
    enabled: !!analyst,
  })

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  if (!analyst) {
    return (
      <Box sx={{
        display: 'flex', justifyContent: 'center', alignItems: 'center',
        minHeight: '100vh', flexDirection: 'column', gap: 3,
        background: `
          radial-gradient(circle at 50% 30%, rgba(44,113,201,0.18), transparent 40%),
          radial-gradient(circle at 80% 10%, rgba(201,178,126,0.10), transparent 30%),
          linear-gradient(180deg, #061427 0%, #04101f 100%)`,
      }}>
        <Box
          component="img"
          src="/logo.png"
          alt="SOC Workbench"
          sx={{ height: 80, mb: 1 }}
        />
        <Typography variant="h4" fontWeight={700}>SOC Workbench</Typography>
        <Typography color="text.secondary">Sign in with your organization account</Typography>
        <GoogleLogin
          onSuccess={(response) => {
            if (response.credential) login(response.credential)
          }}
          onError={() => {}}
          theme="filled_blue"
          size="large"
          shape="rectangular"
        />
      </Box>
    )
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static" color="transparent" elevation={0}
        sx={{
          borderBottom: 1,
          borderColor: 'rgba(255,255,255,0.08)',
          background: 'rgba(4,12,22,0.72)',
          backdropFilter: 'blur(14px)',
        }}>
        <Toolbar>
          <Box
            component="img"
            src="/logo.png"
            alt="SOC Workbench"
            sx={{ height: 38, cursor: 'pointer', mr: 2 }}
            onClick={() => navigate('/dashboard')}
          />
          <Typography
            variant="h6"
            sx={{
              fontWeight: 700, cursor: 'pointer', mr: 4,
              color: socTokens.brand.text,
              letterSpacing: '-0.02em',
            }}
            onClick={() => navigate('/dashboard')}
          >
            SOC Workbench
          </Typography>
          <Button
            sx={{
              color: location.pathname === '/dashboard' ? socTokens.brand.gold : 'inherit',
              borderBottom: location.pathname === '/dashboard' ? `2px solid ${socTokens.brand.gold}` : '2px solid transparent',
              borderRadius: 0,
              pb: 0.5,
              '&:hover': { color: socTokens.brand.gold2 },
            }}
            onClick={() => navigate('/dashboard')}
          >
            Dashboard
          </Button>
          <Button
            sx={{
              color: location.pathname === '/watchlists' ? socTokens.brand.gold : 'inherit',
              borderBottom: location.pathname === '/watchlists' ? `2px solid ${socTokens.brand.gold}` : '2px solid transparent',
              borderRadius: 0,
              pb: 0.5,
              '&:hover': { color: socTokens.brand.gold2 },
            }}
            onClick={() => navigate('/watchlists')}
          >
            Watchlists
          </Button>
          {isAdmin && (
            <Button
              sx={{
                color: location.pathname.startsWith('/admin') ? socTokens.brand.gold : 'inherit',
                borderBottom: location.pathname.startsWith('/admin') ? `2px solid ${socTokens.brand.gold}` : '2px solid transparent',
                borderRadius: 0,
                pb: 0.5,
                '&:hover': { color: socTokens.brand.gold2 },
              }}
              onClick={() => navigate('/admin')}
            >
              Admin
            </Button>
          )}
          <Box sx={{ flex: 1 }} />
          <Chip
            label={analyst.email}
            size="small"
            variant="outlined"
            sx={{ mr: 1 }}
          />
          <Chip
            label={analyst.role.toUpperCase()}
            size="small"
            color={isAdmin ? 'primary' : 'default'}
          />
          <Button size="small" color="inherit" onClick={logout} sx={{ ml: 1 }}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>
      <Box component="main" sx={{ flex: 1, p: 0 }}>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/watchlists" element={<Watchlists />} />
          <Route path="/cases/:id" element={<CaseDetail />} />
          {isAdmin ? (
            <Route path="/admin/*" element={
              <Suspense fallback={<CircularProgress sx={{ m: 4 }} />}>
                <Box>
                  <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 3 }}>
                    <Tabs value={getAdminTab(location.pathname)} onChange={(_, v) => navigate(v)}>
                      <Tab label="Overview" value="/admin" />
                      <Tab label="Clients" value="/admin/clients" />
                      <Tab label="Analysts" value="/admin/analysts" />
                      <Tab label="Performance" value="/admin/performance" />
                      <Tab label="Audit Log" value="/admin/audit" />
                    </Tabs>
                  </Box>
                  <Routes>
                    <Route index element={<AdminDashboard />} />
                    <Route path="clients" element={<ClientManagement />} />
                    <Route path="analysts" element={<AnalystAssignment />} />
                    <Route path="performance" element={<AgentPerformance />} />
                    <Route path="audit" element={<AuditLog />} />
                  </Routes>
                </Box>
              </Suspense>
            } />
          ) : (
            <Route path="/admin/*" element={
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <Box component="img" src="/logo.png" alt="SOC Workbench" sx={{ height: 48, mb: 2, opacity: 0.5 }} />
                <Typography variant="h6">Admin Access Required</Typography>
                <Typography color="text.secondary">Your role does not have access to this section</Typography>
              </Box>
            } />
          )}
        </Routes>
      </Box>

      {/* Stacked notification toasts */}
      {toasts.map((toast, index) => (
        <Snackbar
          key={toast.id}
          open
          autoHideDuration={5000}
          onClose={(_event, reason) => {
            if (reason !== 'clickaway') dismissToast(toast.id)
          }}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          sx={{ bottom: { xs: `${24 + index * 64}px !important` } }}
        >
          <Alert
            onClose={() => dismissToast(toast.id)}
            severity={toast.severity}
            variant="filled"
            sx={{ width: '100%', minWidth: 300 }}
          >
            {toast.message}
          </Alert>
        </Snackbar>
      ))}

      {/* Session expired dialog */}
      <Dialog open={sessionExpired}>
        <DialogTitle>Session Expired</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Your session has expired. Please refresh to re-authenticate.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button variant="contained" onClick={() => window.location.reload()}>
            Refresh
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
