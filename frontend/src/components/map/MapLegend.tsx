import { IPC_COLORS, IPC_LABELS } from '../../types'

export function MapLegend() {
  return (
    <div className="absolute bottom-8 left-4 bg-surface-secondary/90 backdrop-blur-sm rounded-lg p-3 text-xs">
      <p className="text-slate-400 font-medium mb-2 uppercase tracking-wider">IPC Phase</p>
      {[1, 2, 3, 4, 5].map((phase) => (
        <div key={phase} className="flex items-center gap-2 mb-1">
          <div
            className="w-3 h-3 rounded-sm flex-shrink-0"
            style={{ backgroundColor: IPC_COLORS[phase] }}
          />
          <span className="text-slate-300">
            {phase} — {IPC_LABELS[phase]}
          </span>
        </div>
      ))}
      <div className="flex items-center gap-2 mt-1">
        <div className="w-3 h-3 rounded-sm flex-shrink-0 bg-gray-600" />
        <span className="text-slate-400">No data</span>
      </div>
    </div>
  )
}
