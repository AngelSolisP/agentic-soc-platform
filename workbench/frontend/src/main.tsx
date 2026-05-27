import React, { useEffect, useState } from 'react'
import ReactDOM from 'react-dom/client'
import { ThemeProvider, CssBaseline, Box, CircularProgress } from '@mui/material'
import { BrowserRouter } from 'react-router-dom'
import { GoogleOAuthProvider } from '@react-oauth/google'
import App from './App'
import { darkTheme } from './theme/dark'
import { AuthProvider } from './hooks/useAuth'

function ConfiguredApp() {
  const [googleClientId, setGoogleClientId] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/config')
      .then(r => r.json())
      .then(d => setGoogleClientId(d.google_client_id ?? ''))
      .catch(() => setGoogleClientId(''))
  }, [])

  if (googleClientId === null) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  const app = (
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  )

  return (
    <GoogleOAuthProvider clientId={googleClientId || 'placeholder'}>
      {app}
    </GoogleOAuthProvider>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <ConfiguredApp />
    </ThemeProvider>
  </React.StrictMode>,
)
