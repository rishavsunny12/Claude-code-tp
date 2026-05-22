import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Sprout, MessageSquare, Globe, RefreshCw } from 'lucide-react'
import { WorldMap } from './components/map/WorldMap'
import { MapLegend } from './components/map/MapLegend'
import { RegionSidebar } from './components/sidebar/RegionSidebar'
import { AlertsBar } from './components/alerts/AlertsBar'
import { ChatDrawer } from './components/chat/ChatDrawer'
import { fetchRegions } from './lib/api'

export default function App() {
  const [selectedIso, setSelectedIso] = useState<string | null>(null)
  const [chatOpen, setChatOpen] = useState(false)

  const { data: regions = [], isLoading, refetch } = useQuery({
    queryKey: ['regions'],
    queryFn: fetchRegions,
    refetchInterval: 10 * 60 * 1000,   // refetch every 10 minutes
  })

  return (
    <div className="flex flex-col h-screen bg-surface-primary text-slate-200 overflow-hidden">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 bg-surface-secondary border-b border-slate-700/50 flex-shrink-0 z-10">
        <div className="flex items-center gap-2.5">
          <Sprout size={20} className="text-phase-1" />
          <span className="text-white font-bold text-lg tracking-tight">HarvestGuard</span>
          <span className="text-slate-500 text-sm hidden sm:block">· Food Insecurity Early Warning</span>
        </div>

        <div className="flex items-center gap-3">
          {isLoading && (
            <span className="text-slate-500 text-xs flex items-center gap-1">
              <RefreshCw size={10} className="animate-spin" /> Loading data…
            </span>
          )}
          {!isLoading && (
            <span className="text-slate-500 text-xs flex items-center gap-1">
              <Globe size={10} />
              {regions.length} countries monitored
            </span>
          )}
          <button
            onClick={() => setChatOpen((v) => !v)}
            className="flex items-center gap-1.5 bg-accent hover:bg-accent/80 text-white text-sm rounded-lg px-3 py-1.5 transition-colors"
          >
            <MessageSquare size={14} />
            <span className="hidden sm:block">AI Analyst</span>
          </button>
        </div>
      </header>

      {/* Alerts ticker */}
      <AlertsBar onSelectRegion={setSelectedIso} />

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Map */}
        <div className="flex-1 relative">
          <WorldMap
            regions={regions}
            selectedIso={selectedIso}
            onSelectRegion={setSelectedIso}
          />
          <MapLegend />
        </div>

        {/* Region sidebar */}
        {selectedIso && (
          <RegionSidebar
            iso={selectedIso}
            onClose={() => setSelectedIso(null)}
          />
        )}

        {/* Chat drawer */}
        {chatOpen && (
          <ChatDrawer
            selectedIso={selectedIso}
            onClose={() => setChatOpen(false)}
          />
        )}
      </div>
    </div>
  )
}
