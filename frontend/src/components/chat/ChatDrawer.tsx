import { useState, useRef, useEffect } from 'react'
import { X, Send, BrainCircuit } from 'lucide-react'
import { streamChat } from '../../lib/api'
import type { ChatMessage } from '../../types'
import { MessageBubble } from './MessageBubble'

interface Props {
  selectedIso: string | null
  onClose: () => void
}

const SUGGESTIONS = [
  'What are the main drivers of food insecurity here?',
  'What interventions are most effective for this phase?',
  'How does rainfall affect crop yields in this region?',
  'What early warning signs should NGOs watch for?',
]

export function ChatDrawer({ selectedIso, onClose }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const cancelRef = useRef<(() => void) | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = (content: string) => {
    if (!content.trim() || streaming) return

    const userMsg: ChatMessage = { role: 'user', content: content.trim() }
    const updatedMessages = [...messages, userMsg]
    setMessages([...updatedMessages, { role: 'assistant', content: '' }])
    setInput('')
    setStreaming(true)

    cancelRef.current?.()
    cancelRef.current = streamChat(
      updatedMessages,
      selectedIso,
      (chunk) => {
        setMessages((prev) => {
          const last = prev[prev.length - 1]
          if (last.role !== 'assistant') return prev
          return [...prev.slice(0, -1), { ...last, content: last.content + chunk }]
        })
      },
      () => setStreaming(false),
    )
  }

  return (
    <div className="w-96 bg-surface-secondary border-l border-slate-700/50 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
        <div className="flex items-center gap-2">
          <BrainCircuit size={16} className="text-accent" />
          <span className="text-white font-semibold">HarvestGuard AI</span>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
          <X size={18} />
        </button>
      </div>

      {/* Context indicator */}
      {selectedIso && (
        <div className="px-4 py-2 bg-accent/10 border-b border-accent/20">
          <p className="text-xs text-accent-light">
            Context: {selectedIso} data loaded
          </p>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-slate-400 text-sm">
              Ask me anything about food security, agricultural conditions, or specific countries.
            </p>
            <div className="space-y-1.5 mt-4">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="w-full text-left text-xs text-slate-300 bg-surface-card hover:bg-surface-hover rounded-lg p-2.5 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} isStreaming={streaming && i === messages.length - 1} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-slate-700/50">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
            placeholder={selectedIso ? `Ask about ${selectedIso}...` : 'Ask about food security...'}
            disabled={streaming}
            className="flex-1 bg-surface-card text-slate-200 placeholder-slate-500 rounded-lg px-3 py-2 text-sm border border-slate-700 focus:outline-none focus:border-accent disabled:opacity-50"
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || streaming}
            className="bg-accent hover:bg-accent/80 disabled:opacity-40 text-white rounded-lg p-2 transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}
