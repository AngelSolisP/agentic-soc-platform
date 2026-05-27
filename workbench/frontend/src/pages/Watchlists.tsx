import { useState, useEffect } from 'react'
import { Box, Typography, TextField, MenuItem, Button, Alert, Card, CardContent, Table, TableBody, TableCell, TableHead, TableRow, Chip, IconButton } from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import AddIcon from '@mui/icons-material/Add'
import VisibilityIcon from '@mui/icons-material/Visibility'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/services/api'
import { socTokens } from '@/theme/dark'

export default function Watchlists() {
  const { analyst, isAdmin } = useAuth()
  const [clientId, setClientId] = useState('')
  const [clientOptions, setClientOptions] = useState<string[]>([])
  const [watchlists, setWatchlists] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<any>(null)

  // Populate client dropdown
  useEffect(() => {
    if (isAdmin) {
      api.admin.clients.list()
        .then(({ clients }) => {
          const ids = clients
            .map((c) => (c.client_id ?? c.id ?? '') as string)
            .filter(Boolean)
          setClientOptions(ids.sort())
          if (ids.length > 0) setClientId(ids[0])
        })
        .catch(() => setClientOptions([]))
    } else if (analyst?.allowed_clients.length) {
      const ids = [...analyst.allowed_clients].sort()
      setClientOptions(ids)
      setClientId(ids[0])
    }
  }, [analyst, isAdmin])

  const fetchWatchlists = async () => {
    if (!clientId) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await api.watchlists.list(clientId)
      setWatchlists(data)
    } catch (err: any) {
      setError(err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchWatchlists()
  }, [clientId])

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Watchlists</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button size="small" startIcon={<RefreshIcon />} onClick={fetchWatchlists} disabled={isLoading}>
            Refresh
          </Button>
          <TextField
            select
            size="small"
            label="Client"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            sx={{ minWidth: 200 }}
          >
            {clientOptions.map((id) => (
              <MenuItem key={id} value={id}>{id}</MenuItem>
            ))}
          </TextField>
          <Button variant="contained" startIcon={<AddIcon />} size="small">
            Create Watchlist
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load watchlists: {error.message || 'Unknown error'}
        </Alert>
      )}

      <Card variant="outlined" sx={{ background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.08)' }}>
        <CardContent sx={{ p: 0 }}>
          <Table>
            <TableHead>
              <TableRow sx={{ background: 'rgba(255,255,255,0.03)' }}>
                <TableCell sx={{ fontWeight: 700 }}>Name</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Description</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Entity Type</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Entities</TableCell>
                <TableCell sx={{ fontWeight: 700 }} align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
                    <Typography color="text.secondary">Loading watchlists...</Typography>
                  </TableCell>
                </TableRow>
              ) : watchlists.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
                    <Typography color="text.secondary">No watchlists found for this client.</Typography>
                  </TableCell>
                </TableRow>
              ) : (
                watchlists.map((wl) => (
                  <TableRow key={wl.name} hover sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                    <TableCell sx={{ fontWeight: 600, color: socTokens.brand.gold }}>
                      {wl.displayName || wl.name.split('/').pop()}
                    </TableCell>
                    <TableCell sx={{ color: 'text.secondary', maxWidth: 400 }}>
                      {wl.description || 'No description'}
                    </TableCell>
                    <TableCell>
                      <Chip label={wl.entityType} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      {wl.entityCount || 0} entities
                    </TableCell>
                    <TableCell align="right">
                      <IconButton size="small" title="View Details">
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Box>
  )
}
