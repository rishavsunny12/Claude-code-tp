import { clsx } from 'clsx'

interface Props {
  label: string
  value: string
  subvalue?: string
  color?: string
  trend?: 'improving' | 'stable' | 'deteriorating' | null
}

const trendIcon = {
  improving: '↓',
  stable: '→',
  deteriorating: '↑',
}

const trendColor = {
  improving: 'text-phase-1',
  stable: 'text-slate-400',
  deteriorating: 'text-phase-4',
}

export function MetricCard({ label, value, subvalue, color, trend }: Props) {
  return (
    <div className="bg-surface-card rounded-lg p-3">
      <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">{label}</p>
      <div className="flex items-end gap-2">
        <span
          className="text-xl font-semibold"
          style={color ? { color } : undefined}
        >
          {value}
        </span>
        {trend && (
          <span className={clsx('text-sm font-medium mb-0.5', trendColor[trend])}>
            {trendIcon[trend]}
          </span>
        )}
      </div>
      {subvalue && <p className="text-slate-400 text-xs mt-0.5">{subvalue}</p>}
    </div>
  )
}
