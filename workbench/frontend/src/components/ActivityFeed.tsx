import {
  Accordion, AccordionSummary, AccordionDetails,
  Typography, Box, Chip,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { PipelineStage } from '@/services/api'
import { JsonView } from './JsonView'

export function ActivityFeed({ stages }: { stages: PipelineStage[] }) {
  if (stages.length === 0) {
    return <Typography color="text.secondary">No pipeline data available</Typography>
  }

  return (
    <Box>
      {stages.map((stage) => (
        <Accordion key={stage.stage_id} defaultExpanded={stage.status !== 'COMPLETED'}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
              <Typography variant="subtitle2" sx={{ textTransform: 'capitalize' }}>
                {stage.stage_name?.replace('_', ' ')}
              </Typography>
              <Chip
                label={stage.status}
                size="small"
                color={stage.status === 'COMPLETED' ? 'success' : stage.status === 'ERROR' ? 'error' : 'default'}
              />
              {stage.duration_seconds != null && (
                <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto', mr: 2 }}>
                  {stage.duration_seconds.toFixed(1)}s
                </Typography>
              )}
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {stage.error && (
              <Typography color="error" variant="body2" sx={{ mb: 1 }}>
                Error: {stage.error}
              </Typography>
            )}
            {stage.output_structured && (
              <JsonView data={stage.output_structured} />
            )}
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  )
}
