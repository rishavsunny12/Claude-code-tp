import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts'
import type { NDVIPoint, RainfallPoint } from '../../types'

interface Props {
  ndviHistory: NDVIPoint[]
  rainfallHistory: RainfallPoint[]
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en', { month: 'short', year: '2-digit' })
}

export function TrendChart({ ndviHistory, rainfallHistory }: Props) {
  // Merge by date
  const dateMap = new Map<string, { date: string; ndvi?: number; rainfall?: number }>()

  ndviHistory.forEach(({ date, ndvi_mean }) => {
    dateMap.set(date, { date, ndvi: ndvi_mean })
  })
  rainfallHistory.forEach(({ date, rainfall_mm }) => {
    const existing = dateMap.get(date) ?? { date }
    dateMap.set(date, { ...existing, rainfall: rainfall_mm })
  })

  const data = Array.from(dateMap.values())
    .sort((a, b) => a.date.localeCompare(b.date))
    .map((d) => ({ ...d, label: formatDate(d.date) }))

  if (data.length === 0) {
    return (
      <div className="h-32 flex items-center justify-center text-slate-500 text-sm">
        No trend data available
      </div>
    )
  }

  return (
    <div>
      <p className="text-slate-400 text-xs uppercase tracking-wider mb-2">90-Day Trend</p>
      <ResponsiveContainer width="100%" height={160}>
        <ComposedChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="label"
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis yAxisId="ndvi" domain={[0, 1]} tick={{ fill: '#9CA3AF', fontSize: 10 }} />
          <YAxis yAxisId="rain" orientation="right" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
          <Tooltip
            contentStyle={{ backgroundColor: '#212836', border: '1px solid #374151', borderRadius: 6 }}
            labelStyle={{ color: '#E4E6EB' }}
          />
          <Bar yAxisId="rain" dataKey="rainfall" name="Rainfall (mm)" fill="#01619C" opacity={0.7} radius={[2, 2, 0, 0]} />
          <Line
            yAxisId="ndvi"
            type="monotone"
            dataKey="ndvi"
            name="NDVI"
            stroke="#00AC46"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
