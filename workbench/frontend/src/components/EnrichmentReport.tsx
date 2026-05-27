import {
  Card, CardContent, Typography, Box, Chip, Divider,
} from '@mui/material'
import { PipelineStage } from '@/services/api'
import { JsonView } from './JsonView'

export function EnrichmentReport({ stages }: { stages: PipelineStage[] }) {
  const enrichmentStage = stages.find((s) => s.stage_name === 'enrichment')

  if (!enrichmentStage?.output_structured) {
    return <Typography color="text.secondary">No enrichment data available</Typography>
  }

  const output = enrichmentStage.output_structured as Record<string, unknown>
  const hasGti = Boolean(output.gti_reports)
  const hasUdm = Boolean(output.udm_results)
  const hasEntities = Boolean(output.entities) && Array.isArray(output.entities)
  const hasOther = !hasGti && !hasUdm && !hasEntities

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* GTI Reports */}
      {hasGti && (
        <Card>
          <CardContent>
            <Typography variant="subtitle2" gutterBottom>GTI Reports</Typography>
            <JsonView data={output.gti_reports} />
          </CardContent>
        </Card>
      )}

      {/* UDM Search Results */}
      {hasUdm && (
        <Card>
          <CardContent>
            <Typography variant="subtitle2" gutterBottom>UDM Search Results</Typography>
            <JsonView data={output.udm_results} />
          </CardContent>
        </Card>
      )}

      {/* Entity Summaries */}
      {hasEntities && (
        <Card>
          <CardContent>
            <Typography variant="subtitle2" gutterBottom>Entity Summaries</Typography>
            {(output.entities as Record<string, unknown>[]).map((entity, i) => (
              <Box key={i} sx={{ mb: 1 }}>
                <Chip label={String(entity.type || 'unknown')} size="small" sx={{ mr: 1 }} />
                <Typography variant="body2" component="span">
                  {String(entity.value || entity.indicator || '')}
                </Typography>
                {i < (output.entities as unknown[]).length - 1 && <Divider sx={{ mt: 1 }} />}
              </Box>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Raw output fallback */}
      {hasOther && (
        <Card>
          <CardContent>
            <Typography variant="subtitle2" gutterBottom>Enrichment Output</Typography>
            <JsonView data={output} />
          </CardContent>
        </Card>
      )}
    </Box>
  )
}
