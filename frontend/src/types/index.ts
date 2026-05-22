export interface RegionSummary {
  iso_code: string
  name: string
  latitude: number | null
  longitude: number | null
  risk_score: number | null
  ipc_phase: number | null
  affected_population: number | null
  trend: 'improving' | 'stable' | 'deteriorating' | null
  ndvi_anomaly: number | null
  rainfall_anomaly_pct: number | null
}

export interface NDVIPoint {
  date: string
  ndvi_mean: number
  ndvi_anomaly: number | null
}

export interface RainfallPoint {
  date: string
  rainfall_mm: number
  anomaly_pct: number | null
}

export interface RegionDetail extends RegionSummary {
  ndvi_history: NDVIPoint[]
  rainfall_history: RainfallPoint[]
  risk_factors: Record<string, number> | null
}

export interface AlertItem {
  id: number
  iso_code: string
  country_name: string
  severity: 'watch' | 'warning' | 'emergency'
  message: string
  created_at: string
  resolved: boolean
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export const IPC_LABELS: Record<number, string> = {
  1: 'Minimal',
  2: 'Stressed',
  3: 'Crisis',
  4: 'Emergency',
  5: 'Catastrophe',
}

export const IPC_COLORS: Record<number, string> = {
  1: '#00AC46',
  2: '#CADD00',
  3: '#E7B000',
  4: '#E35C00',
  5: '#C80000',
}

export function riskScoreToColor(score: number | null): string {
  if (score === null) return '#374151'
  if (score >= 0.80) return '#C80000'
  if (score >= 0.60) return '#E35C00'
  if (score >= 0.40) return '#E7B000'
  if (score >= 0.20) return '#CADD00'
  return '#00AC46'
}

export function formatPopulation(pop: number | null): string {
  if (!pop) return '—'
  if (pop >= 1_000_000) return `${(pop / 1_000_000).toFixed(1)}M`
  if (pop >= 1_000) return `${(pop / 1_000).toFixed(0)}K`
  return pop.toString()
}
