import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, Typography, Card, CardContent, CardActionArea, Chip, Skeleton,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
  alpha,
} from '@mui/material'
import GroupIcon from '@mui/icons-material/Group'
import PeopleAltIcon from '@mui/icons-material/PeopleAlt'
import PendingActionsIcon from '@mui/icons-material/PendingActions'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import TimerIcon from '@mui/icons-material/Timer'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import StorageIcon from '@mui/icons-material/Storage'
import PersonIcon from '@mui/icons-material/Person'
import BarChartIcon from '@mui/icons-material/BarChart'
import PolicyIcon from '@mui/icons-material/Policy'
import { api } from '@/services/api'
import { socTokens } from '@/theme/dark'

const REFRESH_INTERVAL_MS = 30_000

interface DashboardState {
  activeClients: number
  pendingApprovals: number
  totalAnalysts: number
  recentRuns: number
  avgDuration: string
  successRate: string
  auditEntries: Record<string, unknown>[]
}

const INITIAL: DashboardState = {
  activeClients: 0,
  pendingApprovals: 0,
  totalAnalysts: 0,
  recentRuns: 0,
  avgDuration: '--',
  successRate: '--',
  auditEntries: [],
}

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [state, setState] = useState<DashboardState>(INITIAL)
  const [loading, setLoading] = useState(true)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchAll = useCallback(async () => {
    try {
      const [dashboard, analysts, perf, audit] = await Promise.all([
        api.admin.dashboard(),
        api.admin.analysts.list(),
        api.admin.performance({ days: 1 }),
        api.admin.audit({ limit: 5 }),
      ])

      const clients = dashboard.clients as Record<string, number> | undefined
      const kpis = dashboard.kpis as Record<string, number> | undefined
      const metrics = perf.metrics as Record<string, unknown>[]

      const totalRuns = metrics.reduce((s, m) => s + Number(m.total_runs || 0), 0)
      const weightedDuration = metrics.reduce(
        (s, m) => s + Number(m.avg_duration_seconds || 0) * Number(m.total_runs || 0),
        0,
      )
      const totalCompleted = metrics.reduce((s, m) => s + Number(m.completed || 0), 0)

      setState({
        activeClients: clients?.enabled ?? 0,
        pendingApprovals: kpis?.pending_approvals ?? 0,
        totalAnalysts: analysts.analysts.length,
        recentRuns: totalRuns,
        avgDuration: totalRuns > 0 ? `${(weightedDuration / totalRuns).toFixed(1)}s` : '--',
        successRate: totalRuns > 0 ? `${((totalCompleted / totalRuns) * 100).toFixed(0)}%` : '--',
        auditEntries: audit.entries,
      })
    } catch {
      // Keep previous state on error
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAll()
    timerRef.current = setInterval(fetchAll, REFRESH_INTERVAL_MS)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [fetchAll])

  const kpis = [
    {
      label: 'Active Clients',
      value: state.activeClients,
      icon: <GroupIcon />,
      color: socTokens.severity.info,
    },
    {
      label: 'Pending Approvals',
      value: state.pendingApprovals,
      icon: <PendingActionsIcon />,
      color: state.pendingApprovals > 0 ? socTokens.severity.high : socTokens.severity.low,
      onClick: () => navigate('/cases?status=OPENED'),
    },
    {
      label: 'Total Analysts',
      value: state.totalAnalysts,
      icon: <PeopleAltIcon />,
      color: socTokens.severity.info,
    },
    {
      label: 'Pipeline Runs (24h)',
      value: state.recentRuns,
      icon: <PlayArrowIcon />,
      color: socTokens.severity.info,
    },
    {
      label: 'Avg Duration',
      value: state.avgDuration,
      icon: <TimerIcon />,
      color: socTokens.severity.medium,
    },
    {
      label: 'Success Rate',
      value: state.successRate,
      icon: <CheckCircleIcon />,
      color: socTokens.severity.low,
    },
  ]

  const quickLinks = [
    { label: 'Manage Clients', path: '/admin/clients', icon: <StorageIcon /> },
    { label: 'Manage Analysts', path: '/admin/analysts', icon: <PersonIcon /> },
    { label: 'Agent Performance', path: '/admin/performance', icon: <BarChartIcon /> },
    { label: 'Audit Log', path: '/admin/audit', icon: <PolicyIcon /> },
  ]

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Admin Dashboard</Typography>
        <Typography variant="caption" color="text.secondary">
          Auto-refresh every 30s
        </Typography>
      </Box>

      {/* KPI Cards */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr 1fr', md: 'repeat(3, 1fr)', lg: 'repeat(6, 1fr)' },
          gap: 2,
          mb: 4,
        }}
      >
        {kpis.map((kpi) => {
          const inner = (
            <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                <Box sx={{ color: kpi.color, display: 'flex' }}>{kpi.icon}</Box>
                <Typography variant="overline" color="text.secondary" sx={{ lineHeight: 1.2 }}>
                  {kpi.label}
                </Typography>
              </Box>
              {loading ? (
                <Skeleton variant="text" width={60} sx={{ fontSize: '2rem' }} />
              ) : (
                <Typography variant="h4" sx={{ fontWeight: 700, color: kpi.color }}>
                  {kpi.value}
                </Typography>
              )}
            </CardContent>
          )

          return kpi.onClick ? (
            <Card key={kpi.label}>
              <CardActionArea onClick={kpi.onClick}>{inner}</CardActionArea>
            </Card>
          ) : (
            <Card key={kpi.label}>{inner}</Card>
          )
        })}
      </Box>

      {/* Quick Links */}
      <Typography variant="subtitle1" sx={{ mb: 1.5 }}>
        Quick Links
      </Typography>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr 1fr', sm: 'repeat(4, 1fr)' },
          gap: 2,
          mb: 4,
        }}
      >
        {quickLinks.map((link) => (
          <Card key={link.path}>
            <CardActionArea
              onClick={() => navigate(link.path)}
              sx={{ py: 2, px: 2.5, display: 'flex', alignItems: 'center', gap: 1.5, justifyContent: 'flex-start' }}
            >
              <Box sx={{ color: 'primary.main', display: 'flex' }}>{link.icon}</Box>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {link.label}
              </Typography>
            </CardActionArea>
          </Card>
        ))}
      </Box>

      {/* Recent Activity */}
      <Typography variant="subtitle1" sx={{ mb: 1.5 }}>
        Recent Activity
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Timestamp</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Analyst</TableCell>
              <TableCell>Client</TableCell>
              <TableCell>Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 5 }).map((__, j) => (
                      <TableCell key={j}><Skeleton variant="text" /></TableCell>
                    ))}
                  </TableRow>
                ))
              : state.auditEntries.length === 0
                ? (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                          No recent activity
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )
                : state.auditEntries.map((e, i) => (
                    <TableRow key={i} hover>
                      <TableCell>
                        <Typography variant="caption">
                          {e.timestamp ? new Date(String(e.timestamp)).toLocaleString() : '--'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={String(e.action || '')}
                          size="small"
                          sx={{
                            bgcolor: alpha(socTokens.severity.info, 0.15),
                            color: socTokens.severity.info,
                          }}
                        />
                      </TableCell>
                      <TableCell>{String(e.analyst_email || '--')}</TableCell>
                      <TableCell>{String(e.client_id || '--')}</TableCell>
                      <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {String(e.details || '--')}
                      </TableCell>
                    </TableRow>
                  ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
