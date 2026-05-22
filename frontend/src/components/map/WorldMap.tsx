import { useRef, useEffect, useCallback } from 'react'
import maplibregl from 'maplibre-gl'
import type { RegionSummary } from '../../types'
import { riskScoreToColor } from '../../types'

interface Props {
  regions: RegionSummary[]
  selectedIso: string | null
  onSelectRegion: (iso: string) => void
}

const WORLD_GEOJSON_URL =
  'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'

export function WorldMap({ regions, selectedIso, onSelectRegion }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)

  const riskByIso = useRef<Map<string, number>>(new Map())

  useEffect(() => {
    riskByIso.current = new Map(
      regions.map((r) => [r.iso_code, r.risk_score ?? -1])
    )
  }, [regions])

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
      // Add country boundaries GeoJSON
      map.addSource('countries', {
        type: 'geojson',
        data: WORLD_GEOJSON_URL,
        promoteId: 'ISO_A3',
      })

      // Fill layer — colored by risk score
      map.addLayer({
        id: 'country-fill',
        type: 'fill',
        source: 'countries',
        paint: {
          'fill-color': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            '#FFFFFF',
            ['coalesce', ['feature-state', 'color'], '#374151'],
          ],
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            0.4,
            0.65,
          ],
        },
      })

      // Outline layer
      map.addLayer({
        id: 'country-outline',
        type: 'line',
        source: 'countries',
        paint: {
          'line-color': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            '#FFFFFF',
            '#374151',
          ],
          'line-width': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            2,
            0.5,
          ],
        },
      })

      // Labels layer
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
        paint: { 'text-color': '#CBD5E1', 'text-halo-color': '#0F1419', 'text-halo-width': 1 },
      })

      // Click handler
      map.on('click', 'country-fill', (e) => {
        const iso = e.features?.[0]?.properties?.ISO_A3
        if (iso) onSelectRegion(iso)
      })

      map.on('mouseenter', 'country-fill', () => {
        map.getCanvas().style.cursor = 'pointer'
      })
      map.on('mouseleave', 'country-fill', () => {
        map.getCanvas().style.cursor = ''
      })
    })

    mapRef.current = map
    return () => map.remove()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Update feature states when regions data changes
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded()) return

    const updateColors = () => {
      riskByIso.current.forEach((score, iso) => {
        const color = score >= 0 ? riskScoreToColor(score) : '#374151'
        map.setFeatureState({ source: 'countries', id: iso }, { color })
      })
    }

    if (map.getSource('countries')) {
      updateColors()
    } else {
      map.once('idle', updateColors)
    }
  }, [regions])

  // Highlight selected country
  useEffect(() => {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded()) return

    const updateSelected = () => {
      if (!map.getSource('countries')) return
      // Clear all selections
      // We rely on feature state — set selected=false broadly not easy in maplibre
      // Instead we track previous selection
    }

    if (map.getSource('countries')) {
      updateSelected()
    }
  }, [selectedIso])

  return (
    <div
      ref={containerRef}
      className="w-full h-full"
      style={{ background: '#0F1419' }}
    />
  )
}
