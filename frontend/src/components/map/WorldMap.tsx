import { useRef, useEffect, useCallback } from 'react'
import maplibregl from 'maplibre-gl'
import type { RegionSummary } from '../../types'
import { fetchMapGeoJSON } from '../../lib/api'

interface Props {
  regions: RegionSummary[]
  selectedIso: string | null
  onSelectRegion: (iso: string) => void
}

// null/missing risk_score → grey; real scores use IPC band colors.
// Note: do not use to-number here — MapLibre converts null to 0, which would show green.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const FILL_COLOR: any = [
  'case',
  ['any', ['!', ['has', 'risk_score']], ['==', ['get', 'risk_score'], null]],
  '#374151', // no data
  [
    'step',
    ['get', 'risk_score'],
    '#00AC46', // Phase 1 Minimal (< 0.20)
    0.20, '#CADD00', // Phase 2 Stressed
    0.40, '#E7B000', // Phase 3 Crisis
    0.60, '#E35C00', // Phase 4 Emergency
    0.80, '#C80000', // Phase 5 Catastrophe
  ],
]

export function WorldMap({ regions, selectedIso, onSelectRegion }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const mapReadyRef = useRef(false)
  const prevSelectedRef = useRef<string | null>(null)

  const loadCountryData = useCallback(async (map: maplibregl.Map) => {
    try {
      const geojson = await fetchMapGeoJSON()
      const source = map.getSource('countries') as maplibregl.GeoJSONSource | undefined
      source?.setData(geojson)
    } catch (err) {
      console.error('Failed to load map GeoJSON:', err)
    }
  }, [])

  // Refresh map when region scores update
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapReadyRef.current || regions.length === 0) return
    loadCountryData(map)
  }, [regions, loadCountryData])

  // Init map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        glyphs: 'https://fonts.openmaptiles.org/{fontstack}/{range}.pbf',
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
        data: { type: 'FeatureCollection', features: [] },
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
          'text-field': ['coalesce', ['get', 'ADMIN'], ['get', 'name']],
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

      mapReadyRef.current = true
      loadCountryData(map)
    })

    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
      mapReadyRef.current = false
    }
  }, [loadCountryData, onSelectRegion])

  // Highlight selected country via feature-state (selection only)
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapReadyRef.current || !map.getSource('countries')) return

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
