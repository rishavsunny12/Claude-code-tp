import { useRef, useEffect } from 'react'
import maplibregl from 'maplibre-gl'
import type { RegionSummary } from '../../types'

interface Props {
  regions: RegionSummary[]
  selectedIso: string | null
  onSelectRegion: (iso: string) => void
}

// Browser loads boundaries directly from CDN — no Docker download needed.
// This file uses uppercase ISO_A3 and ADMIN as property names.
const COUNTRIES_URL =
  'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const FILL_COLOR: any = [
  'step',
  ['coalesce', ['feature-state', 'risk_score'], -1],
  '#374151',        // no data
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
  // Keep a ref to regions so the sourcedata callback can access the latest value
  const regionsRef = useRef<RegionSummary[]>(regions)

  useEffect(() => {
    regionsRef.current = regions
  }, [regions])

  function applyRiskScores(map: maplibregl.Map, data: RegionSummary[]) {
    data.forEach((r) => {
      if (r.risk_score != null) {
        map.setFeatureState(
          { source: 'countries', id: r.iso_code },
          { risk_score: r.risk_score },
        )
      }
    })
  }

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
      map.addSource('countries', {
        type: 'geojson',
        data: COUNTRIES_URL,
        // promoteId tells MapLibre to use ISO_A3 as the feature id for setFeatureState
        promoteId: 'ISO_A3',
      })

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

      // Apply risk scores once the GeoJSON source has fully loaded
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      map.on('sourcedata', (e: any) => {
        if (e.sourceId === 'countries' && e.isSourceLoaded) {
          applyRiskScores(map, regionsRef.current)
        }
      })
    })

    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Re-apply risk scores whenever regions data refreshes
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded() || regions.length === 0) return
    if (!map.isSourceLoaded('countries')) return
    applyRiskScores(map, regions)
  }, [regions])

  // Highlight selected country via feature-state
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
