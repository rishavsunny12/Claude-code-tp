import { useRef, useEffect } from 'react'
import maplibregl from 'maplibre-gl'
import type { RegionSummary } from '../../types'

interface Props {
  regions: RegionSummary[]
  selectedIso: string | null
  onSelectRegion: (iso: string) => void
}

// Our own API serves GeoJSON with risk_score embedded as a feature property.
// This is simpler and more reliable than feature-state.
const RISK_GEOJSON_URL = '/api/v1/map/geojson'

// Step expression: risk_score property 0–1 → IPC phase colour.
// null / missing → -1 via coalesce → grey (no data).
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const FILL_COLOR: any = [
  'step',
  ['coalesce', ['get', 'risk_score'], -1],
  '#374151',        // -1   no data
  0.001, '#00AC46', // Phase 1 Minimal
  0.20,  '#CADD00', // Phase 2 Stressed
  0.40,  '#E7B000', // Phase 3 Crisis
  0.60,  '#E35C00', // Phase 4 Emergency
  0.80,  '#C80000', // Phase 5 Catastrophe
]

export function WorldMap({ regions, selectedIso, onSelectRegion }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const prevSelectedRef = useRef<string | null>(null)

  // Init map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          'carto-dark': {
            type: 'raster',
            tiles: [
              'https://a.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png',
              'https://b.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}.png',
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors © CARTO',
          },
        },
        layers: [{ id: 'background', type: 'raster', source: 'carto-dark' }],
      },
      center: [20, 5],
      zoom: 2,
      minZoom: 1.5,
      maxZoom: 8,
    })

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-left')

    map.on('load', () => {
      // Our own API — GeoJSON with risk_score already in properties
      map.addSource('countries', {
        type: 'geojson',
        data: RISK_GEOJSON_URL,
        promoteId: 'ISO_A3',
      })

      // Fill coloured by risk_score property — no feature-state needed
      map.addLayer({
        id: 'country-fill',
        type: 'fill',
        source: 'countries',
        paint: {
          'fill-color': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            '#FFFFFF',
            FILL_COLOR,
          ],
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            0.35,
            0.75,
          ],
        },
      })

      map.addLayer({
        id: 'country-outline',
        type: 'line',
        source: 'countries',
        paint: {
          'line-color': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            '#FFFFFF',
            '#1F2937',
          ],
          'line-width': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            2,
            0.4,
          ],
        },
      })

      map.addLayer({
        id: 'country-labels',
        type: 'symbol',
        source: 'countries',
        minzoom: 3,
        layout: {
          'text-field': ['get', 'ADMIN'],
          'text-size': 11,
          'text-font': ['Open Sans Regular'],
        },
        paint: {
          'text-color': '#CBD5E1',
          'text-halo-color': '#0F1419',
          'text-halo-width': 1,
        },
      })

      map.on('click', 'country-fill', (e) => {
        const iso = e.features?.[0]?.properties?.ISO_A3
        if (iso) onSelectRegion(iso)
      })
      map.on('mouseenter', 'country-fill', () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseleave', 'country-fill', () => { map.getCanvas().style.cursor = '' })
    })

    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // When regions data refreshes, reload the GeoJSON source so new risk scores appear
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded() || regions.length === 0) return
    const source = map.getSource('countries') as maplibregl.GeoJSONSource | undefined
    if (source) {
      // Add cache-busting param so the browser fetches fresh data from our API
      source.setData(`${RISK_GEOJSON_URL}?t=${Date.now()}`)
    }
  }, [regions])

  // Highlight selected country via feature-state (selection only, not colour)
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded() || !map.getSource('countries')) return

    if (prevSelectedRef.current) {
      map.setFeatureState(
        { source: 'countries', id: prevSelectedRef.current },
        { selected: false },
      )
    }
    if (selectedIso) {
      map.setFeatureState(
        { source: 'countries', id: selectedIso },
        { selected: true },
      )
    }
    prevSelectedRef.current = selectedIso
  }, [selectedIso])

  return (
    <div ref={containerRef} className="w-full h-full" style={{ background: '#0F1419' }} />
  )
}
