import { createTheme } from '@mui/material/styles'

// Zevorus brand palette — navy + gold
// Extracted from zevorus.com design system
const zevorus = {
  bg: '#061427',
  bgDeep: '#04101f',
  bgSoft: '#0b213c',
  surface: '#102947',
  surface2: '#132f52',
  surface3: '#183b64',
  text: '#f5f8fc',
  muted: '#c1cedd',
  muted2: '#97a9bf',
  gold: '#c9b27e',
  gold2: '#d7c08c',
  goldDark: '#96763a',
  blue: '#67b7ff',
  border: 'rgba(255,255,255,0.10)',
  borderStrong: 'rgba(255,255,255,0.18)',
}

const palette = {
  primary: { main: zevorus.gold, dark: zevorus.goldDark, light: zevorus.gold2, contrastText: '#081019' },
  secondary: { main: zevorus.blue, dark: '#3d8bd4', light: '#9dd0ff', contrastText: '#04101f' },
  error: { main: '#F28B82', dark: '#93000A', contrastText: '#690005' },
  warning: { main: '#FDD663', contrastText: '#3F2E00' },
  success: { main: '#81C995', contrastText: '#00391C' },
  info: { main: zevorus.blue, contrastText: '#003063' },
  background: { default: zevorus.bg, paper: zevorus.surface },
  text: { primary: zevorus.text, secondary: zevorus.muted },
  divider: zevorus.border,
}

// SOC-specific tokens
export const socTokens = {
  severity: {
    critical: '#F28B82',
    high: '#FDD663',
    medium: '#FBBC04',
    low: '#81C995',
    info: zevorus.blue,
  },
  verdict: {
    malicious: '#F28B82',
    suspicious: '#FDD663',
    benign: '#81C995',
    inconclusive: '#DADCE0',
  },
  surface: {
    container: zevorus.surface,
    containerHigh: zevorus.surface2,
    containerHighest: zevorus.surface3,
  },
  brand: zevorus,
}

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    ...palette,
  },
  typography: {
    fontFamily: '"Google Sans Text", "Google Sans", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontFamily: '"Google Sans", sans-serif', fontWeight: 700 },
    h2: { fontFamily: '"Google Sans", sans-serif', fontWeight: 700 },
    h3: { fontFamily: '"Google Sans", sans-serif', fontWeight: 700 },
    h4: { fontFamily: '"Google Sans", sans-serif', fontWeight: 600 },
    h5: { fontFamily: '"Google Sans", sans-serif', fontWeight: 600 },
    h6: { fontFamily: '"Google Sans", sans-serif', fontWeight: 600 },
    subtitle1: { fontFamily: '"Google Sans Text", sans-serif', fontWeight: 500 },
    subtitle2: { fontFamily: '"Google Sans Text", sans-serif', fontWeight: 500 },
    body1: { fontFamily: '"Google Sans Text", sans-serif' },
    body2: { fontFamily: '"Google Sans Text", sans-serif' },
    button: { fontFamily: '"Google Sans", sans-serif', fontWeight: 500, textTransform: 'none' as const },
    caption: { fontFamily: '"Google Sans Text", sans-serif' },
    overline: { fontFamily: '"Google Sans Text", sans-serif', textTransform: 'uppercase' as const },
  },
  shape: { borderRadius: 16 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background: `
            radial-gradient(circle at 15% 20%, rgba(44,113,201,0.20), transparent 28%),
            radial-gradient(circle at 85% 10%, rgba(201,178,126,0.12), transparent 24%),
            linear-gradient(180deg, ${zevorus.bg} 0%, ${zevorus.bgDeep} 100%)`,
          backgroundAttachment: 'fixed',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          borderRadius: 20,
          background: `linear-gradient(180deg, rgba(16,41,71,0.92), rgba(10,28,49,0.92))`,
          border: `1px solid ${zevorus.border}`,
          boxShadow: '0 18px 60px rgba(0,0,0,0.25)',
          transition: 'transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease',
          '&:hover': {
            borderColor: 'rgba(201,178,126,0.35)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { borderRadius: 8, fontWeight: 500 },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          padding: '8px 22px',
          fontWeight: 700,
          transition: 'transform 0.2s ease, box-shadow 0.25s ease, border-color 0.25s ease, background 0.25s ease',
          '&:hover': {
            transform: 'translateY(-1px)',
          },
        },
        containedPrimary: {
          background: `linear-gradient(180deg, ${zevorus.gold2}, ${zevorus.gold})`,
          color: '#081019',
          boxShadow: '0 10px 24px rgba(201,178,126,0.24)',
          '&:hover': {
            background: `linear-gradient(180deg, ${zevorus.gold2}, ${zevorus.goldDark})`,
            boxShadow: '0 12px 28px rgba(201,178,126,0.32)',
          },
        },
        outlinedPrimary: {
          borderColor: zevorus.borderStrong,
          color: zevorus.text,
          '&:hover': {
            borderColor: zevorus.gold,
            backgroundColor: 'rgba(201,178,126,0.08)',
          },
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 24,
          background: `linear-gradient(180deg, ${zevorus.surface}, ${zevorus.bgSoft})`,
          border: `1px solid ${zevorus.border}`,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          background: 'rgba(4,12,22,0.72)',
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
          borderBottom: `1px solid rgba(255,255,255,0.08)`,
          boxShadow: '0 12px 30px rgba(0,0,0,0.18)',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
          '&.Mui-selected': {
            color: zevorus.gold,
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: {
          backgroundColor: zevorus.gold,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: { borderColor: zevorus.border },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(201,178,126,0.12)',
        },
        bar: {
          background: `linear-gradient(90deg, ${zevorus.gold}, ${zevorus.gold2})`,
        },
      },
    },
    MuiCircularProgress: {
      styleOverrides: {
        root: {
          color: zevorus.gold,
        },
      },
    },
  },
})
