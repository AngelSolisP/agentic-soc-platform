import { useState, useMemo } from 'react'
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  TablePagination, TableSortLabel,
  Chip, Box, Typography, Paper, Tooltip,
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { Case } from '@/services/api'
import { socTokens } from '@/theme/dark'

const severityColor: Record<string, string> = {
  CRITICAL: socTokens.severity.critical,
  PRIORITY_CRITICAL: socTokens.severity.critical,
  HIGH: socTokens.severity.high,
  PRIORITY_HIGH: socTokens.severity.high,
  MEDIUM: socTokens.severity.medium,
  PRIORITY_MEDIUM: socTokens.severity.medium,
  LOW: socTokens.severity.low,
  PRIORITY_LOW: socTokens.severity.low,
}

const verdictColor: Record<string, string> = {
  MALICIOUS: socTokens.verdict.malicious,
  SUSPICIOUS: socTokens.verdict.suspicious,
  BENIGN: socTokens.verdict.benign,
  INCONCLUSIVE: socTokens.verdict.inconclusive,
}

// Numeric rank maps for custom sort orders
const PRIORITY_RANK: Record<string, number> = {
  CRITICAL: 0, PRIORITY_CRITICAL: 0,
  HIGH: 1, PRIORITY_HIGH: 1,
  MEDIUM: 2, PRIORITY_MEDIUM: 2,
  LOW: 3, PRIORITY_LOW: 3,
  INFORMATIVE: 4, PRIORITY_INFORMATIVE: 4,
}

const VERDICT_RANK: Record<string, number> = {
  MALICIOUS: 0,
  SUSPICIOUS: 1,
  INCONCLUSIVE: 2,
  BENIGN: 3,
}

type SortableColumn = 'priority' | 'status' | 'client_id' | 'verdict'
type Order = 'asc' | 'desc'

function getCaseValue(c: Case, col: SortableColumn): number | string {
  switch (col) {
    case 'priority':
      return PRIORITY_RANK[c.priority ?? ''] ?? 99
    case 'verdict':
      return VERDICT_RANK[c.pipeline?.verdict ?? ''] ?? 99
    case 'status':
      return c.status ?? ''
    case 'client_id':
      return c.client_id
  }
}

function compareCase(a: Case, b: Case, orderBy: SortableColumn, order: Order): number {
  const aVal = getCaseValue(a, orderBy)
  const bVal = getCaseValue(b, orderBy)
  let cmp: number
  if (typeof aVal === 'number' && typeof bVal === 'number') {
    cmp = aVal - bVal
  } else {
    cmp = String(aVal).localeCompare(String(bVal))
  }
  return order === 'desc' ? -cmp : cmp
}

export function CaseInbox({ cases }: { cases: Case[] }) {
  const navigate = useNavigate()
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(25)
  const [order, setOrder] = useState<Order>('asc')
  const [orderBy, setOrderBy] = useState<SortableColumn>('priority')

  // Reset to first page when data changes
  const caseCount = cases.length
  if (page > 0 && page * rowsPerPage >= caseCount) {
    setPage(0)
  }

  const sorted = useMemo(
    () => [...cases].sort((a, b) => compareCase(a, b, orderBy, order)),
    [cases, orderBy, order],
  )

  const paginated = useMemo(
    () => sorted.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage),
    [sorted, page, rowsPerPage],
  )

  const handleSort = (col: SortableColumn) => {
    const isAsc = orderBy === col && order === 'asc'
    setOrder(isAsc ? 'desc' : 'asc')
    setOrderBy(col)
  }

  if (cases.length === 0) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography color="text.secondary">No cases found</Typography>
      </Paper>
    )
  }

  const sortLabel = (col: SortableColumn, label: string) => (
    <TableSortLabel
      active={orderBy === col}
      direction={orderBy === col ? order : 'asc'}
      onClick={() => handleSort(col)}
    >
      {label}
    </TableSortLabel>
  )

  return (
    <TableContainer component={Paper}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell width={4} />
            <TableCell>Case ID</TableCell>
            <TableCell>Name</TableCell>
            <TableCell>{sortLabel('status', 'Status')}</TableCell>
            <TableCell>{sortLabel('priority', 'Priority')}</TableCell>
            <TableCell>{sortLabel('verdict', 'Verdict')}</TableCell>
            <TableCell>{sortLabel('client_id', 'Client')}</TableCell>
            <TableCell>Pipeline</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {paginated.map((c) => (
            <TableRow
              key={`${c.client_id}-${c.id}`}
              hover
              sx={{ cursor: 'pointer' }}
              onClick={() => navigate(`/cases/${c.id}?client_id=${c.client_id}`)}
            >
              <TableCell sx={{ p: 0 }}>
                <Box sx={{
                  width: 4, height: '100%', minHeight: 40,
                  bgcolor: severityColor[c.priority || ''] || 'transparent',
                }} />
              </TableCell>
              <TableCell>
                <Tooltip title={c.id} arrow enterDelay={400}>
                  <Typography
                    variant="body2"
                    sx={{
                      fontFamily: '"Google Sans Mono", monospace',
                      textOverflow: 'ellipsis',
                      overflow: 'hidden',
                      whiteSpace: 'nowrap',
                      maxWidth: 200,
                    }}
                  >
                    {c.id}
                  </Typography>
                </Tooltip>
              </TableCell>
              <TableCell>
                <Tooltip title={c.name || '—'} arrow enterDelay={400}>
                  <Typography
                    variant="body2"
                    sx={{
                      textOverflow: 'ellipsis',
                      overflow: 'hidden',
                      whiteSpace: 'nowrap',
                      maxWidth: 200,
                    }}
                  >
                    {c.name || '—'}
                  </Typography>
                </Tooltip>
              </TableCell>
              <TableCell>
                {c.status && (
                  <Chip
                    label={c.status}
                    size="small"
                    variant="outlined"
                    color={c.status === 'OPENED' ? 'info' : 'default'}
                  />
                )}
              </TableCell>
              <TableCell>
                {c.priority && (
                  <Chip
                    label={c.priority.replace('PRIORITY_', '')}
                    size="small"
                    sx={{ bgcolor: severityColor[c.priority] + '22', color: severityColor[c.priority] }}
                  />
                )}
              </TableCell>
              <TableCell>
                {c.pipeline?.verdict && (
                  <Chip
                    label={c.pipeline.verdict}
                    size="small"
                    sx={{ bgcolor: verdictColor[c.pipeline.verdict] + '22', color: verdictColor[c.pipeline.verdict] }}
                  />
                )}
              </TableCell>
              <TableCell>
                <Typography variant="caption">{c.client_id}</Typography>
              </TableCell>
              <TableCell>
                {c.pipeline ? (
                  <Typography variant="caption">
                    {c.pipeline.stages_completed}/{c.pipeline.total_stages} — {c.pipeline.latest_stage}
                  </Typography>
                ) : (
                  <Typography variant="caption" color="text.secondary">—</Typography>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <TablePagination
        component="div"
        count={caseCount}
        page={page}
        onPageChange={(_, newPage) => setPage(newPage)}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={(e) => {
          setRowsPerPage(parseInt(e.target.value, 10))
          setPage(0)
        }}
        rowsPerPageOptions={[25, 50, 100]}
      />
    </TableContainer>
  )
}
