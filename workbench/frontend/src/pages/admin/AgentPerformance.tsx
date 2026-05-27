import { useEffect, useState } from 'react'
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, TextField, MenuItem,
} from '@mui/material'
import { api } from '@/services/api'

export default function AgentPerformance() {
  const [metrics, setMetrics] = useState<Record<string, unknown>[]>([])
  const [days, setDays] = useState(7)

  useEffect(() => {
    api.admin.performance({ days }).then((d) => setMetrics(d.metrics))
  }, [days])

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h5">Agent Performance</Typography>
        <TextField
          select
          size="small"
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          sx={{ minWidth: 120 }}
        >
          <MenuItem value={1}>Last 24h</MenuItem>
          <MenuItem value={7}>Last 7 days</MenuItem>
          <MenuItem value={30}>Last 30 days</MenuItem>
        </TextField>
      </Box>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Agent</TableCell>
              <TableCell align="right">Runs</TableCell>
              <TableCell align="right">Avg Duration (s)</TableCell>
              <TableCell align="right">Success Rate</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {metrics.map((m) => (
              <TableRow key={String(m.agent_name)}>
                <TableCell sx={{ textTransform: 'capitalize' }}>{String(m.agent_name || '').replace('_', ' ')}</TableCell>
                <TableCell align="right">{Number(m.total_runs || 0)}</TableCell>
                <TableCell align="right">{Number(m.avg_duration_seconds || 0).toFixed(1)}</TableCell>
                <TableCell align="right">
                  {m.total_runs ? `${((Number(m.completed || 0) / Number(m.total_runs)) * 100).toFixed(0)}%` : '—'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
