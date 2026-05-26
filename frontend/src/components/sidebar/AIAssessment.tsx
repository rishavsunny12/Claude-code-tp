import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { BrainCircuit, RefreshCw } from 'lucide-react'
import { streamForecast } from '../../lib/api'

interface Props {
  iso: string
}

/** Strip LLM section labels that sometimes leak into streamed text. */
function sanitizeAssessment(text: string): string {
  return text
    .replace(
      /(\*{0,2}\s*)?[Pp]aragraph\s*\d+\s*([—–-]\s*)?(Current Situation|Key Drivers|(?:30[- ]?60[- ]?Day\s+)?Outlook)?\s*:?\s*\*{0,2}/gi,
      '\n\n',
    )
    .replace(
      /(\*{0,2}\s*)?(Current Situation|Key Drivers|(?:30[- ]?60[- ]?Day\s+)?Outlook)\s*:?\s*\*{0,2}/gi,
      '',
    )
    .replace(/^[Pp]aragraph\s*\d+\s*:?\s*/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

export function AIAssessment({ iso }: Props) {
  const [text, setText] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState(false)
  const cancelRef = useRef<(() => void) | null>(null)

  const startStream = () => {
    setText('')
    setError(false)
    setStreaming(true)

    cancelRef.current?.()
    cancelRef.current = streamForecast(
      iso,
      (chunk) => setText((prev) => prev + chunk),
      () => setStreaming(false),
    )
  }

  useEffect(() => {
    startStream()
    return () => cancelRef.current?.()
  }, [iso]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5 text-slate-400 text-xs uppercase tracking-wider">
          <BrainCircuit size={12} />
          AI Risk Assessment
        </div>
        {!streaming && (
          <button
            onClick={startStream}
            className="text-slate-500 hover:text-slate-300 transition-colors"
            title="Refresh analysis"
          >
            <RefreshCw size={12} />
          </button>
        )}
      </div>

      <div className="bg-surface-card rounded-lg p-3 text-sm text-slate-300 leading-relaxed min-h-[80px]">
        {text ? (
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
            }}
          >
            {sanitizeAssessment(text)}
          </ReactMarkdown>
        ) : streaming ? (
          <div className="flex items-center gap-2 text-slate-500">
            <span className="animate-pulse">●</span>
            <span>Analyzing satellite and field data...</span>
          </div>
        ) : (
          <p className="text-slate-500">Click refresh to generate analysis</p>
        )}
        {streaming && text && (
          <span className="inline-block w-0.5 h-4 bg-accent animate-pulse ml-0.5 align-middle" />
        )}
      </div>
    </div>
  )
}
