import { useRef, useEffect } from 'react'
import maplibregl from 'maplibre-gl'
import type { RegionSummary } from '../../types'

interface Props {
  regions: RegionSummary[]
  selectedIso: string | null
  onSelectRegion: (iso: string) => void
}

// Country boundaries fetched once in JS, then merged with risk scores from our API.
// This gives us property-based styling (['get', 'risk_score']) which is the most
// reliable approach in MapLibre — no feature-state timing issues for colors.
const COUNTRIES_URL =
  'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const FILL_COLOR: any = [
  'step',
  ['coalesce', ['get', 'risk_score'], -1],
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
  // Both pieces of async data stored in refs so we can merge whenever either arrives
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const baseGeoJsonRef = useRef<any>(null)
  const regionsRef = useRef<RegionSummary[]>([])

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function mergeAndSetData(geojson: any, regionData: RegionSummary[]) {
    const map = mapRef.current
    if (!map || !map.isStyleLoaded()) return
    const source = map.getSource('countries') as maplibregl.GeoJSONSource | undefined
    if (!source) return

    const riskByIso: Record<string, number | null> = {}
    regionData.forEach((r) => { riskByIso[r.iso_code] = r.risk_score ?? null })

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const features = geojson.features.map((f: any) => ({
      ...f,
      properties: {
        ...f.properties,
        risk_score: riskByIso[f.properties?.ISO_A3] ?? null,
      },
    }))

    source.setData({ type: 'FeatureCollection', features })
  }

  // Keep regionsRef in sync and trigger a merge if the base GeoJSON is already ready
  useEffect(() => {
    regionsRef.current = regions
    if (regions.length > 0 && baseGeoJsonRef.current) {
      mergeAndSetData(baseGeoJsonRef.current, regions)
    }
  }, [regions]) // eslint-disable-line react-hooks/exhaustive-deps

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
      // Start with an empty collection — setData() will populate it once both
      // the base GeoJSON and risk scores are available.
      map.addSource('countries', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
        // promoteId lets us still use feature-state for selection highlight
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

      // Fetch the base GeoJSON once; merge with whatever risk scores we have
      fetch(COUNTRIES_URL)
        .then((r) => r.json())
        .then((geojson) => {
          baseGeoJsonRef.current = geojson
          // Merge immediately if regions data is already available
          if (regionsRef.current.length > 0) {
            mergeAndSetData(geojson, regionsRef.current)
          } else {
            // Show country outlines with no-data color while regions load
            const source = map.getSource('countries') as maplibregl.GeoJSONSource
            source?.setData(geojson)
          }
        })
        .catch((err) => console.error('Failed to load countries GeoJSON:', err))
    })

    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

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
