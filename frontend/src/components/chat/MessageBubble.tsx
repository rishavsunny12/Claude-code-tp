import ReactMarkdown from 'react-markdown'
import { clsx } from 'clsx'
import type { ChatMessage } from '../../types'

interface Props {
  message: ChatMessage
  isStreaming?: boolean
}

export function MessageBubble({ message, isStreaming }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={clsx('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={clsx(
          'max-w-[85%] rounded-lg px-3 py-2 text-sm',
          isUser
            ? 'bg-accent text-white'
            : 'bg-surface-card text-slate-300',
        )}
      >
        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-1.5 last:mb-0 text-slate-300">{children}</p>,
                strong: ({ children }) => <strong className="text-white">{children}</strong>,
                ul: ({ children }) => <ul className="list-disc list-inside space-y-0.5">{children}</ul>,
                li: ({ children }) => <li className="text-slate-300">{children}</li>,
              }}
            >
              {message.content || ''}
            </ReactMarkdown>
            {isStreaming && message.content && (
              <span className="inline-block w-0.5 h-3.5 bg-accent animate-pulse ml-0.5 align-middle" />
            )}
            {isStreaming && !message.content && (
              <span className="text-slate-500 animate-pulse">●</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
