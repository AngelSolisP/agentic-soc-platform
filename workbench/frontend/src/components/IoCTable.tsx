import { useState } from 'react'
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, Typography, IconButton, Tooltip, Box,
} from '@mui/material'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import { socTokens } from '@/theme/dark'

interface IoC {
  type: string
  value: string
  verdict?: string
  source?: string
}

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation()
    void navigator.clipboard.writeText(value).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }

  return (
    <Tooltip title={copied ? 'Copied!' : 'Copy'} arrow>
      <IconButton size="small" onClick={handleCopy} sx={{ ml: 0.5, p: 0.25 }}>
        <ContentCopyIcon sx={{ fontSize: 14 }} />
      </IconButton>
    </Tooltip>
  )
}

export function IoCTable({ iocs }: { iocs: IoC[] }) {
  if (iocs.length === 0) {
    return <Typography color="text.secondary">No indicators found</Typography>
  }

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Type</TableCell>
            <TableCell>Value</TableCell>
            <TableCell>Verdict</TableCell>
            <TableCell>Source</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {iocs.map((ioc, i) => (
            <TableRow key={i}>
              <TableCell><Chip label={ioc.type} size="small" variant="outlined" /></TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography
                    component="span"
                    sx={{ fontFamily: '"Google Sans Mono", monospace', fontSize: '0.85rem' }}
                  >
                    {ioc.value}
                  </Typography>
                  <CopyButton value={ioc.value} />
                </Box>
              </TableCell>
              <TableCell>
                {ioc.verdict && (
                  <Chip
                    label={ioc.verdict}
                    size="small"
                    sx={{
                      bgcolor: (socTokens.verdict[ioc.verdict.toLowerCase() as keyof typeof socTokens.verdict] || '#888') + '22',
                      color: socTokens.verdict[ioc.verdict.toLowerCase() as keyof typeof socTokens.verdict] || '#888',
                    }}
                  />
                )}
              </TableCell>
              <TableCell>{ioc.source || '—'}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
