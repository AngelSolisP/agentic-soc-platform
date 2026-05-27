import { Box, Card, CardContent, Typography } from '@mui/material'
import { socTokens } from '@/theme/dark'

interface KPI {
  label: string
  value: number | string
  color?: string
}

export function KPICards({ kpis }: { kpis: KPI[] }) {
  return (
    <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
      {kpis.map((kpi) => (
        <Card key={kpi.label} sx={{ minWidth: 160, flex: '1 1 0' }}>
          <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
            <Typography variant="overline" color="text.secondary">
              {kpi.label}
            </Typography>
            <Typography
              variant="h4"
              sx={{ fontWeight: 700, color: kpi.color || 'text.primary' }}
            >
              {kpi.value}
            </Typography>
          </CardContent>
        </Card>
      ))}
    </Box>
  )
}

export function buildCaseKPIs(cases: { priority?: string; status?: string }[]): KPI[] {
  const critical = cases.filter((c) => c.priority === 'CRITICAL' || c.priority === 'PRIORITY_CRITICAL').length
  const high = cases.filter((c) => c.priority === 'HIGH' || c.priority === 'PRIORITY_HIGH').length
  const opened = cases.filter((c) => c.status === 'OPENED').length
  const total = cases.length

  return [
    { label: 'Critical', value: critical, color: socTokens.severity.critical },
    { label: 'High', value: high, color: socTokens.severity.high },
    { label: 'Open Cases', value: opened, color: socTokens.severity.info },
    { label: 'Total', value: total },
  ]
}
