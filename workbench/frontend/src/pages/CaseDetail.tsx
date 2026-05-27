import { useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import {
  Box, Typography, Tabs, Tab, Chip, Card, CardContent, Button, CircularProgress,
  Alert, Snackbar,
} from '@mui/material'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import { useCaseDetail } from '@/hooks/useCases'
import { useWebSocket } from '@/hooks/useWebSocket'
import { socTokens } from '@/theme/dark'
import { PipelineStepper } from '@/components/PipelineStepper'
import { ActivityFeed } from '@/components/ActivityFeed'
import { ActionApproval } from '@/components/ActionApproval'
import { IoCTable } from '@/components/IoCTable'
import { api, PipelineStage, getAuthToken } from '@/services/api'
import { EnrichmentReport } from '@/components/EnrichmentReport'
import { InvestigationChat } from '@/components/InvestigationChat'
import { Timeline } from '@/components/Timeline'

export default function CaseDetail() {
  const { id: caseId } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const clientId = searchParams.get('client_id') || ''
  const [tab, setTab] = useState(0)

  const [triggering, setTriggering] = useState(false)
  const [snack, setSnack] = useState<{ msg: string; severity: 'success' | 'error' } | null>(null)

  const { detail, isLoading, error, refresh } = useCaseDetail(caseId, clientId)

  // WebSocket for live pipeline updates (auth token + client_id required)
  const wsToken = getAuthToken()
  useWebSocket({
    url: `/ws/pipeline/${caseId}`,
    params: { ...(clientId ? { client_id: clientId } : {}), ...(wsToken ? { token: wsToken } : {}) },
    onMessage: () => refresh(),
    enabled: !!clientId,
  })

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 6 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error || !detail) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">Failed to load case: {error?.message || 'Not found'}</Typography>
      </Box>
    )
  }

  const caseData = detail.case as Record<string, string>
  const triageStage = detail.pipeline_stages.find((s) => s.stage_name === 'triage')
  const verdict = triageStage?.output_structured as Record<string, any> | undefined
  const tin = verdict?.seclm_investigation as Record<string, any> | undefined

  const handleTrigger = async () => {
    if (!caseId || !clientId || triggering) return
    setTriggering(true)
    try {
      const alertType = caseData?.name || caseData?.displayName || 'GENERIC'
      await api.cases.trigger(caseId, clientId, alertType)
      setSnack({ msg: 'Pipeline triggered — monitoring progress...', severity: 'success' })
      refresh()
    } catch (e) {
      setSnack({ msg: `Pipeline failed: ${e instanceof Error ? e.message : 'Unknown error'}`, severity: 'error' })
    } finally {
      setTriggering(false)
    }
  }

  return (
    <Box sx={{ p: 3, maxWidth: 1400, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <Typography variant="h5" sx={{ fontFamily: '"Google Sans Mono", monospace' }}>
          Case {caseId}
        </Typography>
        {caseData.priority && (
          <Chip
            label={caseData.priority.replace('PRIORITY_', '')}
            sx={{
              bgcolor: (socTokens.severity[caseData.priority.replace('PRIORITY_', '').toLowerCase() as keyof typeof socTokens.severity] || '#888') + '22',
              color: socTokens.severity[caseData.priority.replace('PRIORITY_', '').toLowerCase() as keyof typeof socTokens.severity] || '#888',
            }}
          />
        )}
        {verdict?.verdict && (
          <Chip
            label={verdict.verdict}
            sx={{
              bgcolor: (socTokens.verdict[verdict.verdict.toLowerCase() as keyof typeof socTokens.verdict] || '#888') + '22',
              color: socTokens.verdict[verdict.verdict.toLowerCase() as keyof typeof socTokens.verdict] || '#888',
            }}
          />
        )}
        <Typography variant="body2" color="text.secondary">{clientId}</Typography>
        <Box sx={{ ml: 'auto' }}>
          <Button
            variant="outlined"
            startIcon={triggering ? <CircularProgress size={16} /> : <PlayArrowIcon />}
            onClick={handleTrigger}
            size="small"
            disabled={triggering}
          >
            {triggering ? 'Running...' : 'Run Pipeline'}
          </Button>
        </Box>
      </Box>

      {/* Tabs */}
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label="Summary" />
        <Tab label="Pipeline" />
        <Tab label="Enrichment" />
        <Tab label="Investigation" />
        <Tab label="Timeline" />
      </Tabs>

      {/* Tab Panels */}
      {tab === 0 && (
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          <Box sx={{ flex: '2 1 600px' }}>
            {/* Agent Verdict Card */}
            {verdict && (
              <Card sx={{ mb: 2, background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.08)' }}>
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom sx={{ color: socTokens.brand.gold }}>Agent Analysis</Typography>
                  <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Verdict</Typography>
                      <Typography sx={{ fontWeight: 600 }}>{verdict.verdict || '—'}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Priority</Typography>
                      <Typography>{verdict.priority || '—'}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Confidence</Typography>
                      <Typography>{verdict.confidence_score || '—'}</Typography>
                    </Box>
                  </Box>
                  {verdict.summary && (
                    <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary', fontStyle: 'italic' }}>
                      "{verdict.summary}"
                    </Typography>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Gemini TIN Investigation Card */}
            {tin && tin.available && (
              <Card sx={{ mb: 2, border: '1px solid rgba(44,113,201,0.2)', background: 'rgba(44,113,201,0.05)' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <Box component="img" src="/logo-zevorus.png" sx={{ height: 16, filter: 'grayscale(1) brightness(2)' }} />
                    <Typography variant="subtitle2" sx={{ color: '#4cc9f0', fontWeight: 700 }}>Gemini TIN Investigation (SecLM)</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 3, mb: 2 }}>
                    <Box>
                      <Typography variant="caption" color="text.secondary">TIN Verdict</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: tin.tin_verdict === 'TRUE_POSITIVE' ? 'error.main' : 'success.main' }}>
                        {tin.tin_verdict || '—'}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">TIN Confidence</Typography>
                      <Typography variant="body2">{tin.tin_confidence || '—'}</Typography>
                    </Box>
                    <Box>
                      <Typography variant="caption" color="text.secondary">Agreement</Typography>
                      <Chip 
                        label={tin.agent_agrees ? 'AGREEMENT' : 'DIVERGENCE'} 
                        size="small" 
                        color={tin.agent_agrees ? 'success' : 'warning'}
                        sx={{ height: 20, fontSize: '0.65rem' }}
                      />
                    </Box>
                  </Box>
                  {tin.tin_summary && (
                    <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
                      {tin.tin_summary}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Case Alerts */}
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Case Alerts</Typography>
            {detail.alerts.length === 0 ? (
              <Typography color="text.secondary" variant="body2" sx={{ mb: 2 }}>No alerts</Typography>
            ) : (
              <Card sx={{ mb: 2 }}>
                <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                  {detail.alerts.map((rawAlert: Record<string, unknown>, i: number) => {
                    const a = rawAlert as Record<string, string | number>
                    return (
                      <Box key={i} sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center', py: 0.5, borderBottom: i < detail.alerts.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
                        <Typography variant="body2" sx={{ fontWeight: 500, minWidth: 200 }}>
                          {String(a.displayName || '—')}
                        </Typography>
                        {a.priority && (
                          <Chip label={String(a.priority)} size="small" variant="outlined" />
                        )}
                        {a.environment && (
                          <Typography variant="caption" color="text.secondary">{String(a.environment)}</Typography>
                        )}
                        {a.eventCount && (
                          <Typography variant="caption" color="text.secondary">{String(a.eventCount)} events</Typography>
                        )}
                        {a.playbookStatus && (
                          <Chip
                            label={String(a.playbookStatus)}
                            size="small"
                            color={a.playbookStatus === 'COMPLETED' ? 'success' : 'default'}
                            variant="outlined"
                          />
                        )}
                        {a.sourceUrl && (
                          <Typography
                            variant="caption"
                            component="a"
                            href={String(a.sourceUrl)}
                            target="_blank"
                            rel="noopener"
                            sx={{ color: 'primary.main', textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
                          >
                            View in Chronicle
                          </Typography>
                        )}
                      </Box>
                    )
                  })}
                </CardContent>
              </Card>
            )}

            {/* IoCs */}
            <Typography variant="subtitle2" sx={{ mb: 1 }}>Indicators of Compromise</Typography>
            <IoCTable iocs={extractIoCs(detail.pipeline_stages)} />

            {/* Proposed Actions */}
            <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>Proposed Actions</Typography>
            {detail.approvals.length === 0 ? (
              <Typography color="text.secondary" variant="body2">No pending actions</Typography>
            ) : (
              detail.approvals.map((a) => (
                <ActionApproval key={a.approval_id} approval={a} caseId={caseId!} onDecided={refresh} />
              ))
            )}
          </Box>

          {/* Sidebar */}
          <Card sx={{ flex: '1 1 250px', alignSelf: 'flex-start' }}>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom>Case Metadata</Typography>
              <MetadataRow label="Case ID" value={caseId} />
              <MetadataRow label="Name" value={caseData.name || caseData.displayName} />
              <MetadataRow label="Client" value={clientId} />
              <MetadataRow label="Status" value={caseData.status} />
              <MetadataRow label="Priority" value={caseData.priority} />
              <MetadataRow label="Environment" value={caseData.environment} />
              <MetadataRow label="Assignee" value={caseData.assignee} />
              <MetadataRow label="Alerts" value={String(detail.alerts.length)} />
              <MetadataRow label="Stages" value={`${detail.pipeline_stages.filter(s => s.status === 'COMPLETED').length}/${detail.pipeline_stages.length}`} />
            </CardContent>
          </Card>
        </Box>
      )}

      {tab === 1 && (
        <Box>
          <PipelineStepper stages={detail.pipeline_stages} />
          <ActivityFeed stages={detail.pipeline_stages} />
        </Box>
      )}

      {tab === 2 && <EnrichmentReport stages={detail.pipeline_stages} />}
      {tab === 3 && <InvestigationChat caseId={caseId!} clientId={clientId} />}
      {tab === 4 && <Timeline stages={detail.pipeline_stages} approvals={detail.approvals} />}

      <Snackbar
        open={!!snack}
        autoHideDuration={6000}
        onClose={() => setSnack(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snack?.severity} onClose={() => setSnack(null)} variant="filled">
          {snack?.msg}
        </Alert>
      </Snackbar>
    </Box>
  )
}

function MetadataRow({ label, value }: { label: string; value?: string }) {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
      <Typography variant="caption">{value || '—'}</Typography>
    </Box>
  )
}

function extractIoCs(stages: PipelineStage[]): { type: string; value: string; verdict?: string; source?: string }[] {
  const iocs: { type: string; value: string; verdict?: string; source?: string }[] = []
  for (const stage of stages) {
    const output = stage.output_structured as Record<string, unknown> | undefined
    if (!output) continue

    // Handle legacy 'indicators' array
    if (output.indicators && Array.isArray(output.indicators)) {
      for (const ind of output.indicators) {
        if (typeof ind === 'object' && ind !== null) {
          iocs.push(ind as { type: string; value: string; verdict?: string; source?: string })
        }
      }
    }

    // Handle new 'iocs_found' array
    if (output.iocs_found && Array.isArray(output.iocs_found)) {
      for (const ind of output.iocs_found) {
        if (typeof ind === 'object' && ind !== null) {
          const ioc = ind as Record<string, any>
          iocs.push({
            type: ioc.type || 'UNKNOWN',
            value: ioc.value || '',
            verdict: ioc.verdict || output.verdict || undefined,
            source: stage.stage_name
          })
        }
      }
    }

    // Handle 'enrichments' from enrichment agent
    if (output.enrichments && Array.isArray(output.enrichments)) {
      for (const e of output.enrichments) {
        if (typeof e === 'object' && e !== null) {
          const enc = e as Record<string, any>
          iocs.push({
            type: enc.ioc_type || 'UNKNOWN',
            value: enc.ioc_value || '',
            verdict: enc.gti_verdict || enc.chronicle_verdict || undefined,
            source: 'enrichment'
          })
        }
      }
    }
  }
  return iocs
}
