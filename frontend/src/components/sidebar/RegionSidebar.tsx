import { X, Satellite, CloudRain, Users, AlertTriangle } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { fetchRegionDetail } from '../../lib/api'
import { MetricCard } from './MetricCard'
import { TrendChart } from './TrendChart'
import { AIAssessment } from './AIAssessment'
import { IPC_COLORS, IPC_LABELS, riskScoreToColor, formatPopulation } from '../../types'

interface Props {
  iso: string
  onClose: () => void
}

export function RegionSidebar({ iso, onClose }: Props) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['region', iso],
    queryFn: () => fetchRegionDetail(iso),
    staleTime: 5 * 60 * 1000,
  })

  return (
    <div className="w-80 bg-surface-secondary border-l border-slate-700/50 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
        <div>
          {data ? (
            <>
              <h2 className="text-white font-semibold text-lg leading-tight">{data.name}</h2>
              <p className="text-slate-400 text-xs">{iso}</p>
            </>
          ) : (
            <div className="h-7 w-32 bg-surface-hover animate-pulse rounded" />
          )}
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white transition-colors p-1"
        >
          <X size={18} />
        </button>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-surface-card animate-pulse rounded-lg" />
            ))}
          </div>
        )}

        {isError && (
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <AlertTriangle size={14} className="text-phase-4" />
            Failed to load data for {iso}
          </div>
        )}

        {data && (
          <>
            {/* Risk Score + IPC Phase */}
            <div className="grid grid-cols-2 gap-2">
              <MetricCard
                label="Risk Score"
                value={data.risk_score != null ? `${(data.risk_score * 100).toFixed(0)}%` : '—'}
                trend={data.trend}
                color={riskScoreToColor(data.risk_score)}
              />
              <MetricCard
                label="IPC Phase"
                value={data.ipc_phase ? `${data.ipc_phase}/5` : '—'}
                subvalue={data.ipc_phase ? IPC_LABELS[data.ipc_phase] : undefined}
                color={data.ipc_phase ? IPC_COLORS[data.ipc_phase] : undefined}
              />
            </div>

            {/* NDVI + Rainfall */}
            <div className="grid grid-cols-2 gap-2">
              <MetricCard
                label="NDVI Anomaly"
                value={
                  data.ndvi_anomaly != null
                    ? `${data.ndvi_anomaly > 0 ? '+' : ''}${data.ndvi_anomaly.toFixed(2)}σ`
                    : '—'
                }
                subvalue="vs 20yr mean"
                color={
                  data.ndvi_anomaly == null
                    ? undefined
                    : data.ndvi_anomaly < -1.5
                    ? '#E35C00'
                    : data.ndvi_anomaly < -0.5
                    ? '#E7B000'
                    : '#00AC46'
                }
              />
              <MetricCard
                label="Rainfall"
                value={
                  data.rainfall_anomaly_pct != null
                    ? `${data.rainfall_anomaly_pct > 0 ? '+' : ''}${data.rainfall_anomaly_pct.toFixed(0)}%`
                    : '—'
                }
                subvalue="vs baseline"
                color={
                  data.rainfall_anomaly_pct == null
                    ? undefined
                    : data.rainfall_anomaly_pct < -30
                    ? '#E35C00'
                    : data.rainfall_anomaly_pct < -10
                    ? '#E7B000'
                    : '#00AC46'
                }
              />
            </div>

            {/* Population */}
            {data.affected_population && (
              <div className="flex items-center gap-2 bg-surface-card rounded-lg p-3">
                <Users size={14} className="text-slate-400 flex-shrink-0" />
                <div>
                  <span className="text-white font-semibold">
                    {formatPopulation(data.affected_population)}
                  </span>
                  <span className="text-slate-400 text-sm ml-1">people food insecure</span>
                </div>
              </div>
            )}

            {/* Risk factor breakdown */}
            {data.risk_factors && (
              <div className="bg-surface-card rounded-lg p-3">
                <p className="text-slate-400 text-xs uppercase tracking-wider mb-2">Risk Drivers</p>
                {Object.entries(data.risk_factors).map(([key, val]) => (
                  <div key={key} className="flex items-center justify-between mb-1.5">
                    <span className="text-slate-300 text-xs capitalize">{key.replace('_', ' ')}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-20 bg-surface-primary rounded-full h-1.5">
                        <div
                          className="h-1.5 rounded-full"
                          style={{
                            width: `${Math.min(100, (val as number) * 100)}%`,
                            backgroundColor: val > 0.6 ? '#E35C00' : val > 0.4 ? '#E7B000' : '#00AC46',
                          }}
                        />
                      </div>
                      <span className="text-slate-400 text-xs w-8 text-right">
                        {((val as number) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Trend chart */}
            <TrendChart
              ndviHistory={data.ndvi_history}
              rainfallHistory={data.rainfall_history}
            />

            {/* AI Assessment */}
            <AIAssessment iso={iso} />
          </>
        )}
      </div>

      {/* Data source attribution */}
      <div className="p-3 border-t border-slate-700/50 text-xs text-slate-500">
        Sources: NASA MODIS · CHIRPS · WFP HungerMap · Open-Meteo
      </div>
    </div>
  )
}
