import { Stepper, Step, StepLabel, Typography, Box } from '@mui/material'
import { PipelineStage } from '@/services/api'

const STAGE_ORDER = ['triage', 'enrichment', 'case_manager', 'response']
const STAGE_LABELS: Record<string, string> = {
  triage: 'Triage',
  enrichment: 'Enrichment',
  case_manager: 'Case Manager',
  response: 'Response',
}

export function PipelineStepper({ stages }: { stages: PipelineStage[] }) {
  const stageMap = new Map(stages.map((s) => [s.stage_name, s]))
  const activeStep = stages.filter((s) => s.status === 'COMPLETED').length

  return (
    <Box sx={{ mb: 3 }}>
      <Stepper activeStep={activeStep} alternativeLabel>
        {STAGE_ORDER.map((key) => {
          const stage = stageMap.get(key)
          const isError = stage?.status === 'ERROR'
          return (
            <Step key={key} completed={stage?.status === 'COMPLETED'}>
              <StepLabel error={isError}>
                <Typography variant="caption">{STAGE_LABELS[key]}</Typography>
                {stage?.duration_seconds != null && (
                  <Typography variant="caption" color="text.secondary" display="block">
                    {stage.duration_seconds.toFixed(1)}s
                  </Typography>
                )}
              </StepLabel>
            </Step>
          )
        })}
      </Stepper>
    </Box>
  )
}
