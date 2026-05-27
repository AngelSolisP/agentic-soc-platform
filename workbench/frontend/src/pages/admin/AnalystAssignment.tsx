import { useEffect, useState, useCallback } from 'react'
import {
  Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Chip,
  IconButton, Tooltip, MenuItem, Select, FormControl, InputLabel, Autocomplete,
  type SelectChangeEvent,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import { api } from '@/services/api'

interface AnalystForm {
  email: string
  role: string
  allowed_clients: string[]
}

const EMPTY_FORM: AnalystForm = { email: '', role: 'analyst', allowed_clients: [] }

export default function AnalystAssignment() {
  const [analysts, setAnalysts] = useState<Record<string, unknown>[]>([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<AnalystForm>(EMPTY_FORM)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const [clientOptions, setClientOptions] = useState<string[]>([])

  const load = () => api.admin.analysts.list().then((d) => setAnalysts(d.analysts))
  useEffect(() => { load() }, [])

  const loadClients = useCallback(() => {
    api.admin.clients.list().then((d) => {
      const ids = d.clients
        .map((c) => String(c.client_id ?? c.id ?? ''))
        .filter(Boolean)
      setClientOptions(ids)
    })
  }, [])

  const handleSave = async () => {
    await api.admin.analysts.update(form.email, {
      role: form.role,
      allowed_clients: form.allowed_clients.filter(Boolean),
    })
    setOpen(false)
    load()
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    await api.admin.analysts.delete(deleteTarget)
    setDeleteTarget(null)
    load()
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h5">Analyst Assignments</Typography>
        <Button variant="contained" onClick={() => { setForm({ ...EMPTY_FORM }); loadClients(); setOpen(true) }}>Add Analyst</Button>
      </Box>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Allowed Clients</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {analysts.map((a) => (
              <TableRow key={String(a.email)}>
                <TableCell>{String(a.email)}</TableCell>
                <TableCell><Chip label={String(a.role)} size="small" /></TableCell>
                <TableCell>
                  {Array.isArray(a.allowed_clients)
                    ? (a.allowed_clients as string[]).map((c) => (
                        <Chip key={c} label={c} size="small" sx={{ mr: 0.5 }} />
                      ))
                    : '—'}
                </TableCell>
                <TableCell>
                  <Button
                    size="small"
                    onClick={() => {
                      setForm({
                        email: String(a.email),
                        role: String(a.role || 'analyst'),
                        allowed_clients: Array.isArray(a.allowed_clients) ? (a.allowed_clients as string[]) : [],
                      })
                      loadClients()
                      setOpen(true)
                    }}
                  >
                    Edit
                  </Button>
                  <Tooltip title="Delete analyst">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => setDeleteTarget(String(a.email))}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add / Edit dialog */}
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Analyst Assignment</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          <TextField label="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} size="small" />
          <FormControl size="small" fullWidth>
            <InputLabel id="role-select-label">Role</InputLabel>
            <Select
              labelId="role-select-label"
              label="Role"
              value={form.role}
              onChange={(e: SelectChangeEvent) => setForm({ ...form, role: e.target.value })}
            >
              <MenuItem value="analyst">analyst</MenuItem>
              <MenuItem value="admin">admin</MenuItem>
            </Select>
          </FormControl>
          <Autocomplete
            multiple
            freeSolo
            options={clientOptions.filter((o) => !form.allowed_clients.includes(o))}
            value={form.allowed_clients}
            onChange={(_e, newValue) => setForm({ ...form, allowed_clients: newValue as string[] })}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => {
                const { key, ...rest } = getTagProps({ index })
                return <Chip key={key} label={option} size="small" {...rest} />
              })
            }
            renderInput={(params) => (
              <TextField
                {...params}
                label="Allowed Clients"
                size="small"
                placeholder={form.allowed_clients.length === 0 ? 'Select or type client IDs...' : ''}
                helperText="Choose from registered clients or type a new ID and press Enter"
              />
            )}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave}>Save</Button>
        </DialogActions>
      </Dialog>

      {/* Delete confirmation dialog */}
      <Dialog open={deleteTarget !== null} onClose={() => setDeleteTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Delete Analyst</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to remove <strong>{deleteTarget}</strong>? This will revoke all their access immediately.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDelete}>Delete</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
