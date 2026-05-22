import { AlertTriangle, AlertOctagon, Eye } from 'lucide-react'
import { clsx } from 'clsx'
import { useQuery } from '@tanstack/react-query'
import { fetchAlerts } from '../../lib/api'
import type { AlertItem } from '../../types'

interface Props {
  onSelectRegion: (iso: string) => void
}

const severityConfig = {
  emergency: { icon: AlertOctagon, color: 'text-phase-5', bg: 'bg-phase-5/10 border-phase-5/30' },
  warning:   { icon: AlertTriangle, color: 'text-phase-4', bg: 'bg-phase-4/10 border-phase-4/30' },
  watch:     { icon: Eye, color: 'text-phase-3', bg: 'bg-phase-3/10 border-phase-3/30' },
}

function AlertChip({ alert, onSelect }: { alert: AlertItem; onSelect: () => void }) {
  const cfg = severityConfig[alert.severity]
  const Icon = cfg.icon
  return (
    <button
      onClick={onSelect}
      className={clsx(
        'flex items-center gap-1.5 px-3 py-1.5 rounded border text-xs whitespace-nowrap flex-shrink-0 hover:opacity-90 transition-opacity',
        cfg.bg,
      )}
    >
      <Icon size={11} className={cfg.color} />
      <span className={clsx('font-medium', cfg.color)}>{alert.severity.toUpperCase()}</span>
      <span className="text-slate-300">{alert.country_name}</span>
    </button>
  )
}

export function AlertsBar({ onSelectRegion }: Props) {
  const { data: alerts = [] } = useQuery({
    queryKey: ['alerts'],
    queryFn: fetchAlerts,
    refetchInterval: 5 * 60 * 1000,
  })

  if (alerts.length === 0) return null

  return (
    <div className="bg-surface-secondary border-b border-slate-700/50 px-4 py-2">
      <div className="flex items-center gap-3 overflow-x-auto scrollbar-hide">
        <span className="text-slate-500 text-xs uppercase tracking-wider flex-shrink-0">
          Active Alerts
        </span>
        {alerts.slice(0, 20).map((alert) => (
          <AlertChip
            key={alert.id}
            alert={alert}
            onSelect={() => onSelectRegion(alert.iso_code)}
          />
        ))}
      </div>
    </div>
  )
}
