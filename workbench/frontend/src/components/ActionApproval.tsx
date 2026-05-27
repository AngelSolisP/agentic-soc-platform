import { useState } from 'react'
import {
  Card, CardContent, Typography, Button, TextField, Box, Chip, Divider,
} from '@mui/material'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import CancelIcon from '@mui/icons-material/Cancel'
import { Approval, api } from '@/services/api'
import { JsonView } from './JsonView'

export function ActionApproval({
  approval,
  caseId,
  onDecided,
}: {
  approval: Approval
  caseId: string
  onDecided: () => void
}) {
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)

  const handleDecision = async (action: 'approve' | 'reject') => {
    setLoading(true)
    try {
      if (action === 'approve') {
        await api.cases.approve(caseId, approval.approval_id, notes)
      } else {
        await api.cases.reject(caseId, approval.approval_id, notes)
      }
      onDecided()
    } finally {
      setLoading(false)
    }
  }

  const isPending = approval.status === 'PENDING'

  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="subtitle2">Proposed Action</Typography>
          <Chip label={approval.status} size="small" color={isPending ? 'warning' : 'default'} />
        </Box>

        <Box sx={{ mb: 1 }}>
          <JsonView data={approval.proposed_action} />
        </Box>

        {approval.triage_summary && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {approval.triage_summary}
          </Typography>
        )}

        {isPending && (
          <>
            <Divider sx={{ my: 2 }} />
            <TextField
              fullWidth
              size="small"
              label="Analyst Notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              multiline
              rows={2}
              sx={{ mb: 2 }}
            />
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                color="success"
                startIcon={<CheckCircleIcon />}
                disabled={loading}
                onClick={() => handleDecision('approve')}
              >
                Approve
              </Button>
              <Button
                variant="outlined"
                color="error"
                startIcon={<CancelIcon />}
                disabled={loading}
                onClick={() => handleDecision('reject')}
              >
                Reject
              </Button>
            </Box>
          </>
        )}

        {!isPending && approval.decided_by && (
          <Typography variant="caption" color="text.secondary">
            {approval.status} by {approval.decided_by} at {approval.decided_at}
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}
