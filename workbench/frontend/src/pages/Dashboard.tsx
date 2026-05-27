import { useState, useEffect } from 'react'
import { Box, Typography, TextField, MenuItem, Button, Alert } from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import { useAuth } from '@/hooks/useAuth'
import { useCaseList } from '@/hooks/useCases'
import { api } from '@/services/api'
import { KPICards, buildCaseKPIs } from '@/components/KPICards'
import { CaseInbox } from '@/components/CaseInbox'

export default function Dashboard() {
  const { analyst, isAdmin } = useAuth()
  const [clientId, setClientId] = useState('')
  const [status, setStatus] = useState('OPENED')
  const [clientOptions, setClientOptions] = useState<string[]>([])

  // Populate client dropdown: admin fetches from API, analysts use allowed_clients
  useEffect(() => {
    if (isAdmin) {
      api.admin.clients.list()
        .then(({ clients }) => {
          const ids = clients
            .map((c) => (c.client_id ?? c.id ?? '') as string)
            .filter(Boolean)
          setClientOptions(ids.sort())
        })
        .catch(() => setClientOptions([]))
    } else if (analyst?.allowed_clients.length) {
      setClientOptions([...analyst.allowed_clients].sort())
    }
  }, [analyst, isAdmin])

  const { cases, isLoading, error, refresh } = useCaseList({
    client_id: clientId || undefined,
    status: status || undefined,
  })

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Dashboard</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button size="small" startIcon={<RefreshIcon />} onClick={() => refresh()}>
            Refresh
          </Button>
          <TextField
            select
            size="small"
            label="Client"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            sx={{ minWidth: 170 }}
          >
            <MenuItem value="">All Clients</MenuItem>
            {clientOptions.map((id) => (
              <MenuItem key={id} value={id}>{id}</MenuItem>
            ))}
          </TextField>
          <TextField
            select
            size="small"
            label="Status"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            sx={{ minWidth: 150 }}
          >
            <MenuItem value="OPENED">Open</MenuItem>
            <MenuItem value="CLOSED">Closed</MenuItem>
            <MenuItem value="">All</MenuItem>
          </TextField>
        </Box>
      </Box>

      <KPICards kpis={buildCaseKPIs(cases)} />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} action={
          <Button color="inherit" size="small" onClick={() => refresh()}>Retry</Button>
        }>
          {error.message?.includes('fetch') || error.message?.includes('NetworkError')
            ? 'Cannot reach the server. Check that the MCP Gateway is running.'
            : `Failed to load cases: ${error.message}`
          }
        </Alert>
      )}

      {isLoading ? (
        <Typography color="text.secondary">Loading cases...</Typography>
      ) : (
        <CaseInbox cases={cases} />
      )}
    </Box>
  )
}
