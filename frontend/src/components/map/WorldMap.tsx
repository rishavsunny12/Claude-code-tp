import { useRef, useEffect } from 'react'
import maplibregl from 'maplibre-gl'
import type { RegionSummary } from '../../types'

interface Props {
  regions: RegionSummary[]
  selectedIso: string | null
  onSelectRegion: (iso: string) => void
}

const WORLD_GEOJSON_URL =
  'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'

// MapLibre step expression: risk score 0–1 → IPC phase color
const RISK_COLOR_EXPRESSION: maplibregl.ExpressionSpecification = [
  'case',
  ['==', ['feature-state', 'risk'], null],
  '#374151',   // no data — gray
  [
    'step',
    ['feature-state', 'risk'],
    '#00AC46',   // 0.00–0.20  Phase 1 Minimal
    0.20, '#CADD00',  // 0.20–0.40  Phase 2 Stressed
    0.40, '#E7B000',  // 0.40–0.60  Phase 3 Crisis
    0.60, '#E35C00',  // 0.60–0.80  Phase 4 Emergency
    0.80, '#C80000',  // 0.80–1.00  Phase 5 Catastrophe
  ],
]

export function WorldMap({ regions, selectedIso, onSelectRegion }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const prevSelectedRef = useRef<string | null>(null)

  // Apply risk scores as numeric feature states whenever regions data changes
  const applyRiskColors = (map: maplibregl.Map, data: RegionSummary[]) => {
    data.forEach(({ iso_code, risk_score }) => {
      map.setFeatureState(
        { source: 'countries', id: iso_code },
        { risk: risk_score ?? null },
      )
    })
  }

  // Initialise map once
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
        data: WORLD_GEOJSON_URL,
        promoteId: 'ISO_A3',
      })

      // Fill — colored by numeric risk feature-state via step expression
      map.addLayer({
        id: 'country-fill',
        type: 'fill',
        source: 'countries',
        paint: {
          'fill-color': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            '#FFFFFF',
            RISK_COLOR_EXPRESSION,
          ],
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            0.35,
            0.70,
          ],
        },
      })

      // Outline
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

      // Country name labels (visible on zoom)
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

      // Apply any regions data that arrived before the map finished loading
      if (mapRef.current) {
        // Access current regions via the closure — will be empty on first load,
        // the regions effect below handles subsequent updates
      }
    })

    // Re-apply colors after GeoJSON finishes loading (sourcedata fires multiple times)
    map.on('sourcedata', (e) => {
      if (e.sourceId === 'countries' && (e as any).isSourceLoaded) {
        const currentRegions = (map as any)._harvestguardRegions as RegionSummary[] | undefined
        if (currentRegions?.length) applyRiskColors(map, currentRegions)
      }
    })

    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Apply risk colors whenever regions data arrives or changes
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    // Stash on map instance so the sourcedata handler can access latest data
    ;(map as any)._harvestguardRegions = regions

    if (map.isStyleLoaded() && map.getSource('countries')) {
      applyRiskColors(map, regions)
    }
    // If map/source not ready yet, sourcedata event above will catch it
  }, [regions])

  // Update selected country highlight
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
