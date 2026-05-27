import { useEffect, useState } from 'react'
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  Switch, FormControlLabel, IconButton, Tooltip,
} from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import BlockIcon from '@mui/icons-material/Block'
import { api } from '@/services/api'

interface ClientForm {
  client_id: string
  display_name: string
  gcp_project_id: string
  chronicle_customer_id: string
  chronicle_region: string
  service_account_email: string
  gti_enabled: boolean
}

const emptyForm: ClientForm = {
  client_id: '', display_name: '', gcp_project_id: '',
  chronicle_customer_id: '', chronicle_region: 'us',
  service_account_email: '', gti_enabled: false,
}

export default function ClientManagement() {
  const [clients, setClients] = useState<Record<string, unknown>[]>([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<ClientForm>(emptyForm)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [disableTarget, setDisableTarget] = useState<Record<string, unknown> | null>(null)

  const load = () => api.admin.clients.list().then((d) => setClients(d.clients))
  useEffect(() => { load() }, [])

  const openCreate = () => {
    setEditingId(null)
    setForm(emptyForm)
    setOpen(true)
  }

  const openEdit = (c: Record<string, unknown>) => {
    setEditingId(String(c.client_id))
    setForm({
      client_id: String(c.client_id ?? ''),
      display_name: String(c.display_name ?? ''),
      gcp_project_id: String(c.gcp_project_id ?? ''),
      chronicle_customer_id: String(c.chronicle_customer_id ?? ''),
      chronicle_region: String(c.chronicle_region ?? 'us'),
      service_account_email: String(c.service_account_email ?? ''),
      gti_enabled: Boolean(c.gti_enabled),
    })
    setOpen(true)
  }

  const handleSave = async () => {
    if (editingId) {
      const { client_id: _, ...updateData } = form
      await api.admin.clients.update(editingId, { ...updateData })
    } else {
      await api.admin.clients.create({ ...form })
    }
    setOpen(false)
    setForm(emptyForm)
    setEditingId(null)
    load()
  }

  const handleDisable = async () => {
    if (!disableTarget) return
    await api.admin.clients.disable(String(disableTarget.client_id))
    setDisableTarget(null)
    load()
  }

  const isFormValid = form.client_id && form.gcp_project_id

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h5">Client Management</Typography>
        <Button variant="contained" onClick={openCreate}>Add Client</Button>
      </Box>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Client ID</TableCell>
              <TableCell>Display Name</TableCell>
              <TableCell>GCP Project</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>GTI</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {clients.map((c) => {
              const disabled = c.enabled === false
              return (
                <TableRow key={String(c.client_id)} sx={disabled ? { opacity: 0.5 } : undefined}>
                  <TableCell>{String(c.client_id)}</TableCell>
                  <TableCell>{String(c.display_name || '')}</TableCell>
                  <TableCell>{String(c.gcp_project_id || '')}</TableCell>
                  <TableCell>
                    {disabled
                      ? <Chip label="Disabled" size="small" color="error" variant="outlined" />
                      : <Chip label="Active" size="small" color="success" />}
                  </TableCell>
                  <TableCell><Chip label={c.gti_enabled ? 'Yes' : 'No'} size="small" color={c.gti_enabled ? 'info' : 'default'} /></TableCell>
                  <TableCell align="right">
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => openEdit(c)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    {!disabled && (
                      <Tooltip title="Disable">
                        <IconButton size="small" color="error" onClick={() => setDisableTarget(c)}>
                          <BlockIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create / Edit Dialog */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingId ? 'Edit Client' : 'Add Client'}</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField
            label="Client ID" value={form.client_id}
            onChange={(e) => setForm({ ...form, client_id: e.target.value })}
            size="small" required disabled={!!editingId}
          />
          <TextField label="Display Name" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} size="small" />
          <TextField label="GCP Project ID" value={form.gcp_project_id} onChange={(e) => setForm({ ...form, gcp_project_id: e.target.value })} size="small" required />
          <TextField label="Chronicle Customer ID" value={form.chronicle_customer_id} onChange={(e) => setForm({ ...form, chronicle_customer_id: e.target.value })} size="small" required />
          <TextField label="Chronicle Region" value={form.chronicle_region} onChange={(e) => setForm({ ...form, chronicle_region: e.target.value })} size="small" />
          <TextField label="Service Account Email" value={form.service_account_email} onChange={(e) => setForm({ ...form, service_account_email: e.target.value })} size="small" required />
          <FormControlLabel
            control={<Switch checked={form.gti_enabled} onChange={(e) => setForm({ ...form, gti_enabled: e.target.checked })} />}
            label="Enable GTI (Google Threat Intelligence)"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave} disabled={!isFormValid}>
            {editingId ? 'Save' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Disable Confirmation Dialog */}
      <Dialog open={!!disableTarget} onClose={() => setDisableTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Disable Client</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to disable client <strong>{String(disableTarget?.client_id ?? '')}</strong>?
            This will prevent all agent processing for this tenant.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDisableTarget(null)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDisable}>Disable</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
