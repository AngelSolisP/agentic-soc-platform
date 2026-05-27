import { Box } from '@mui/material'

/**
 * Regex-based syntax highlighter for JSON display.
 * Safe to use with dangerouslySetInnerHTML because JSON.stringify escapes
 * all HTML-significant characters (<, >, &, ") and the regex only injects
 * hardcoded <span> tags with inline styles.
 */
function highlight(json: string): string {
  return json.replace(
    /("(?:\\.|[^"\\])*")\s*:|("(?:\\.|[^"\\])*")|([-+]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|(\btrue\b|\bfalse\b|\bnull\b)/g,
    (match, key?: string, str?: string, num?: string, lit?: string) => {
      if (key) return `<span style="color:#c9b27e">${key}</span>:`
      if (str) return `<span style="color:#c1cedd">${str}</span>`
      if (num) return `<span style="color:#67b7ff">${num}</span>`
      if (lit) return `<span style="color:#97a9bf">${lit}</span>`
      return match
    },
  )
}

export function JsonView({ data }: { data: unknown }) {
  const raw = JSON.stringify(data, null, 2) ?? ''
  return (
    <Box
      component="pre"
      sx={{
        m: 0,
        p: 2,
        fontFamily: '"Google Sans Mono", monospace',
        fontSize: 12,
        bgcolor: '#0b213c',
        borderRadius: 1,
        overflow: 'auto',
        maxHeight: 400,
      }}
      // Safe: JSON.stringify escapes HTML chars; regex only adds hardcoded <span> tags
      dangerouslySetInnerHTML={{ __html: highlight(raw) }}
    />
  )
}
