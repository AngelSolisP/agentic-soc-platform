import { useState, useRef, useEffect } from 'react'
import {
  Box, TextField, Button, Typography, Paper, Card, CardContent, Chip, CircularProgress,
} from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import { api, ChatMessage } from '@/services/api'

interface Message {
  role: 'analyst' | 'agent'
  text: string
  toolCalls?: ChatMessage['tool_calls']
  timestamp: Date
}

export function InvestigationChat({ caseId, clientId }: { caseId: string; clientId: string }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>()
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const userMessage = input.trim()
    setInput('')

    setMessages((prev) => [...prev, { role: 'analyst', text: userMessage, timestamp: new Date() }])
    setLoading(true)

    try {
      const result = await api.cases.chat(caseId, clientId, userMessage, sessionId)
      setSessionId(result.session_id || sessionId)
      setMessages((prev) => [
        ...prev,
        {
          role: 'agent',
          text: result.response,
          toolCalls: result.tool_calls,
          timestamp: new Date(),
        },
      ])
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: 'agent', text: `Error: ${e instanceof Error ? e.message : 'Unknown error'}`, timestamp: new Date() },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 280px)', minHeight: 400 }}>
      {/* Context banner */}
      <Paper variant="outlined" sx={{ p: 1.5, mb: 2, display: 'flex', gap: 1, alignItems: 'center' }}>
        <Chip label={`Case ${caseId}`} size="small" />
        <Chip label={clientId} size="small" variant="outlined" />
        <Typography variant="caption" color="text.secondary">
          Agent has access to Chronicle + GTI MCP tools
        </Typography>
      </Paper>

      {/* Messages */}
      <Box sx={{ flex: 1, overflow: 'auto', mb: 2 }}>
        {messages.length === 0 && (
          <Typography color="text.secondary" sx={{ textAlign: 'center', mt: 4 }}>
            Ask the agent to investigate this case. It can search entities, check GTI reports, and run UDM queries.
          </Typography>
        )}
        {messages.map((msg, i) => (
          <Box
            key={i}
            sx={{
              display: 'flex',
              justifyContent: msg.role === 'analyst' ? 'flex-end' : 'flex-start',
              mb: 1.5,
            }}
          >
            <Card
              sx={{
                maxWidth: '75%',
                bgcolor: msg.role === 'analyst' ? '#183b64' : 'background.paper',
              }}
            >
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {msg.text}
                </Typography>
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    {msg.toolCalls.map((tc, j) => (
                      <Chip
                        key={j}
                        label={`${tc.tool}(${Object.keys(tc.args || {}).join(', ')})`}
                        size="small"
                        variant="outlined"
                        sx={{ mr: 0.5, mb: 0.5, fontFamily: '"Google Sans Mono", monospace', fontSize: '0.75rem' }}
                      />
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        ))}
        {loading && (
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', ml: 1 }}>
            <CircularProgress size={16} />
            <Typography variant="caption" color="text.secondary">Investigating...</Typography>
          </Box>
        )}
        <div ref={endRef} />
      </Box>

      {/* Input */}
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Ask the agent to investigate..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
          disabled={loading}
          multiline
          maxRows={3}
        />
        <Button variant="contained" onClick={handleSend} disabled={loading || !input.trim()}>
          <SendIcon />
        </Button>
      </Box>
    </Box>
  )
}
