# HarvestGuard 🌾

**AI-Powered Food Insecurity Early Warning System**

HarvestGuard is an open-source platform that fuses real satellite vegetation data, rainfall anomalies, and WFP food security indicators to generate AI-powered 30-60 day early warnings of crop failure and food insecurity — accessible to NGOs, governments, and humanitarian responders worldwide.

## The Problem

828 million people face food insecurity. Smallholder farmers (who produce 70% of the world's food) have zero access to advance crop failure warnings. WFP's HungerMap shows *current* status; FEWS NET publishes monthly expert reports. No open, accessible platform provides real-time predictive intelligence at country level.

HarvestGuard fills this gap.

## How It Works

```
NASA MODIS NDVI  ──┐
CHIRPS Rainfall  ──┤──► Risk Engine ──► Claude AI ──► Risk Assessment + Alerts
WFP HungerMap    ──┘                              ──► Conversational Analysis
Open-Meteo       ──┘
```

1. **Real satellite data** — NASA MODIS vegetation indices updated every 16 days
2. **Rainfall anomalies** — CHIRPS precipitation vs 1981-2010 historical baseline
3. **Ground truth** — WFP HungerMap IPC phases and affected population counts
4. **AI analysis** — Claude generates plain-language risk assessments from real data
5. **Early warnings** — Alerts fire when composite risk scores deteriorate significantly

## Data Sources (100% Real, No Synthetic Data)

| Source | Data | Update Frequency |
|--------|------|-----------------|
| [NASA MODIS MOD13A2](https://lpdaac.usgs.gov/products/mod13a2v061/) | NDVI/EVI vegetation indices | 16 days |
| [CHIRPS](https://www.chc.ucsb.edu/data/chirps) | Precipitation anomalies (1981-present) | Monthly |
| [WFP HungerMap](https://hungermap.wfp.org/) | IPC phases, affected populations | 6 hours |
| [Open-Meteo](https://open-meteo.com/) | Historical & forecast weather | Daily |

## Features

- **Interactive World Map** — 60+ countries color-coded by IPC risk phase
- **Real-time NDVI & Rainfall** — Satellite vegetation health and precipitation anomaly trends
- **AI Risk Assessments** — Claude-powered streaming analysis with real data context
- **Early Warning Alerts** — Automatic detection of deteriorating food security
- **Trend Charts** — 90-day NDVI + rainfall history per country
- **AI Chat** — Ask "What's happening in Ethiopia?" and get data-grounded answers

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Anthropic API key ([console.anthropic.com](https://console.anthropic.com))

### 1. Clone and configure
```bash
git clone https://github.com/rishavsunny12/claude-code-tp
cd claude-code-tp
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY
```

### 2. Launch
```bash
docker compose up --build
```

### 3. Seed real data
```bash
# Trigger the first data refresh (fetches WFP + weather data)
curl -X POST http://localhost:8000/api/v1/admin/refresh
```

### 4. Open the app
Navigate to **http://localhost:3000**

Click any country on the map to see:
- Current IPC phase and affected population
- NDVI and rainfall anomalies vs historical baseline
- 90-day trend chart
- Live-streaming Claude AI risk assessment

## API Reference

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/regions` | All monitored countries with current risk scores |
| `GET /api/v1/regions/{iso}` | Full country detail with 90-day history |
| `GET /api/v1/forecast/{iso}` | Stream AI risk assessment (SSE) |
| `GET /api/v1/alerts` | Active food security alerts |
| `POST /api/v1/chat` | Conversational AI query (SSE) |
| `GET /health` | Health check |

## Architecture

```
harvestguard/
├── backend/          Python FastAPI + SQLAlchemy + APScheduler
│   └── app/
│       ├── services/data/    NASA NDVI, CHIRPS, WFP, Open-Meteo integrations
│       ├── services/analysis/ Risk scoring + alert engine
│       ├── services/ai/       Claude API streaming
│       └── api/v1/           REST endpoints
├── frontend/         React + TypeScript + MapLibre GL + Tailwind
│   └── src/
│       ├── components/map/    Interactive choropleth world map
│       ├── components/sidebar/ Country detail panel
│       └── components/chat/   AI conversation interface
└── docker-compose.yml
```

## Optional: NASA Earthdata (Enhanced NDVI)

For higher-accuracy NDVI from actual MODIS raster data:
1. Register free at [urs.earthaccess.nasa.gov](https://urs.earthaccess.nasa.gov/users/new)
2. Add `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` to `.env`

Without credentials, NDVI is estimated from Open-Meteo weather correlates (still useful as a proxy).

## Contributing

This project is designed to serve humanitarian organizations, governments, and researchers. Contributions welcome — especially:
- Additional data source integrations (ACLED conflict data, FEWS NET)
- Sub-national resolution (admin level 1/2)
- SMS/WhatsApp alert delivery for rural communities
- Multi-language support

## License

MIT — free for humanitarian and research use.

## Data Attribution

- Vegetation data: NASA/USGS MODIS Land Processes DAAC
- Precipitation: CHIRPS, Climate Hazards Center, UC Santa Barbara
- Food security: World Food Programme HungerMap LIVE
- Weather: Open-Meteo (CC BY 4.0)
