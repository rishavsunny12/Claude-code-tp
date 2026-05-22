import axios from 'axios'
import type { RegionSummary, RegionDetail, AlertItem } from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

export async function fetchRegions(): Promise<RegionSummary[]> {
  const { data } = await api.get<RegionSummary[]>('/regions')
  return data
}

export async function fetchRegionDetail(iso: string): Promise<RegionDetail> {
  const { data } = await api.get<RegionDetail>(`/regions/${iso}`)
  return data
}

export async function fetchAlerts(): Promise<AlertItem[]> {
  const { data } = await api.get<AlertItem[]>('/alerts')
  return data
}

export function streamForecast(iso: string, onChunk: (text: string) => void, onDone: () => void) {
  const es = new EventSource(`/api/v1/forecast/${iso}`)
  es.onmessage = (e) => {
    if (e.data === '[DONE]') {
      es.close()
      onDone()
      return
    }
    onChunk(e.data)
  }
  es.onerror = () => {
    es.close()
    onDone()
  }
  return () => es.close()
}

export function streamChat(
  messages: { role: string; content: string }[],
  selectedIso: string | null,
  onChunk: (text: string) => void,
  onDone: () => void,
) {
  let cancelled = false

  fetch('/api/v1/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, selected_iso: selectedIso }),
  }).then(async (res) => {
    const reader = res.body?.getReader()
    const decoder = new TextDecoder()
    if (!reader) { onDone(); return }

    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done || cancelled) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const text = line.slice(6)
          if (text === '[DONE]') { onDone(); return }
          onChunk(text.replace(/\\n/g, '\n'))
        }
      }
    }
    onDone()
  }).catch(() => onDone())

  return () => { cancelled = true }
}
