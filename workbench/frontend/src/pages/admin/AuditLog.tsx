import { useEffect, useState } from 'react'
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, TextField, MenuItem, Chip, Button,
} from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'
import { api } from '@/services/api'

const ACTIONS = [
  '', 'LOGIN', 'VIEW_CASE', 'APPROVE_ACTION', 'REJECT_ACTION', 'TRIGGER_PIPELINE',
  'INVESTIGATION_CHAT', 'CREATE_CLIENT', 'UPDATE_CLIENT', 'DISABLE_CLIENT', 'UPDATE_ANALYST',
]

export default function AuditLog() {
  const [entries, setEntries] = useState<Record<string, unknown>[]>([])
  const [action, setAction] = useState('')
  const [limit, setLimit] = useState(50)

  useEffect(() => {
    api.admin.audit({ action: action || undefined, limit }).then((d) => setEntries(d.entries))
  }, [action, limit])

  const exportCsv = () => {
    const escapeCsv = (val: string) => `"${val.replace(/"/g, '""')}"`
    const header = 'Timestamp,Action,Analyst,Client,Details'
    const rows = entries.map((e) => {
      const ts = e.timestamp ? new Date(String(e.timestamp)).toISOString() : ''
      const details = e.details != null ? JSON.stringify(e.details) : ''
      return [ts, String(e.action || ''), String(e.analyst_email || ''), String(e.client_id || ''), details]
        .map(escapeCsv)
        .join(',')
    })
    const csv = [header, ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit_log_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h5">Audit Log</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            size="small"
            startIcon={<DownloadIcon />}
            onClick={exportCsv}
            disabled={entries.length === 0}
          >
            Export CSV
          </Button>
          <TextField
            select
            size="small"
            value={action}
            onChange={(e) => setAction(e.target.value)}
            sx={{ minWidth: 150 }}
            label="Action"
          >
            <MenuItem value="">All</MenuItem>
            {ACTIONS.filter(Boolean).map((a) => (
              <MenuItem key={a} value={a}>{a}</MenuItem>
            ))}
          </TextField>
          <TextField
            select
            size="small"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            sx={{ minWidth: 80 }}
            label="Limit"
          >
            <MenuItem value={25}>25</MenuItem>
            <MenuItem value={50}>50</MenuItem>
            <MenuItem value={100}>100</MenuItem>
          </TextField>
        </Box>
      </Box>
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
            {entries.map((e, i) => (
              <TableRow key={i}>
                <TableCell>
                  <Typography variant="caption">
                    {e.timestamp ? new Date(String(e.timestamp)).toLocaleString() : '—'}
                  </Typography>
                </TableCell>
                <TableCell><Chip label={String(e.action || '')} size="small" /></TableCell>
                <TableCell>{String(e.analyst_email || '—')}</TableCell>
                <TableCell>{String(e.client_id || '—')}</TableCell>
                <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {String(e.details || '—')}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
