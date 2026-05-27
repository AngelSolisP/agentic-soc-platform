import {
  Box, Typography, Card, CardContent, Chip,
} from '@mui/material'
import { PipelineStage, Approval } from '@/services/api'

interface TimelineEvent {
  timestamp: string
  actor: string
  actorType: 'agent' | 'analyst' | 'system'
  action: string
  details?: string
}

export function Timeline({
  stages,
  approvals,
}: {
  stages: PipelineStage[]
  approvals: Approval[]
}) {
  const events = buildTimeline(stages, approvals)

  if (events.length === 0) {
    return <Typography color="text.secondary">No timeline events</Typography>
  }

  return (
    <Box sx={{ position: 'relative', pl: 3 }}>
      {/* Vertical line */}
      <Box sx={{
        position: 'absolute', left: 11, top: 0, bottom: 0,
        width: 2, bgcolor: 'divider',
      }} />

      {events.map((event, i) => (
        <Box key={i} sx={{ position: 'relative', mb: 2 }}>
          {/* Dot */}
          <Box sx={{
            position: 'absolute', left: -21, top: 8,
            width: 10, height: 10, borderRadius: '50%',
            bgcolor: event.actorType === 'agent' ? '#67b7ff' : event.actorType === 'analyst' ? '#c9b27e' : 'text.secondary',
          }} />

          <Card variant="outlined" sx={{ ml: 1 }}>
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                  <Chip
                    label={event.actorType}
                    size="small"
                    color={event.actorType === 'agent' ? 'primary' : event.actorType === 'analyst' ? 'success' : 'default'}
                  />
                  <Typography variant="subtitle2">{event.action}</Typography>
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {formatTimestamp(event.timestamp)}
                </Typography>
              </Box>
              {event.details && (
                <Typography variant="body2" color="text.secondary">{event.details}</Typography>
              )}
            </CardContent>
          </Card>
        </Box>
      ))}
    </Box>
  )
}

function buildTimeline(stages: PipelineStage[], approvals: Approval[]): TimelineEvent[] {
  const events: TimelineEvent[] = []

  for (const stage of stages) {
    if (stage.started_at) {
      events.push({
        timestamp: stage.started_at,
        actor: stage.stage_name || 'agent',
        actorType: 'agent',
        action: `${stage.stage_name} started`,
      })
    }
    if (stage.completed_at) {
      events.push({
        timestamp: stage.completed_at,
        actor: stage.stage_name || 'agent',
        actorType: 'agent',
        action: `${stage.stage_name} ${stage.status?.toLowerCase() || 'completed'}`,
        details: stage.error || undefined,
      })
    }
  }

  for (const approval of approvals) {
    if (approval.decided_by && approval.decided_at) {
      events.push({
        timestamp: approval.decided_at,
        actor: approval.decided_by,
        actorType: 'analyst',
        action: `Action ${approval.status.toLowerCase()}`,
        details: JSON.stringify(approval.proposed_action),
      })
    }
  }

  events.sort((a, b) => a.timestamp.localeCompare(b.timestamp))
  return events
}

function formatTimestamp(ts: string): string {
  try {
    return new Date(ts).toLocaleString()
  } catch {
    return ts
  }
}
