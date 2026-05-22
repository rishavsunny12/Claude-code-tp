"""
GeoJSON endpoint that serves country boundaries with risk scores embedded
as feature properties. This lets MapLibre use data-driven styling based on
properties (much more reliable than feature-state for dynamic data).

Country boundaries come from Natural Earth (bundled with the API).
Risk scores are merged in from the database on each request.
"""

import httpx
import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from functools import lru_cache

from app.core.database import get_db
from app.models.country import Country
from app.models.risk_score import RiskScore

router = APIRouter(prefix="/map", tags=["map"])
logger = logging.getLogger(__name__)

NATURAL_EARTH_URL = (
    "https://raw.githubusercontent.com/datasets/geo-countries"
    "/master/data/countries.geojson"
)

_geojson_cache: dict | None = None


async def _get_base_geojson() -> dict:
    """Fetch and cache the Natural Earth GeoJSON (fetched once per process)."""
    global _geojson_cache
    if _geojson_cache is not None:
        return _geojson_cache

    logger.info("Fetching Natural Earth GeoJSON (one-time download)...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(NATURAL_EARTH_URL)
        response.raise_for_status()
        _geojson_cache = response.json()
    logger.info("GeoJSON cached (%d features)", len(_geojson_cache.get("features", [])))
    return _geojson_cache


@router.get("/geojson")
async def get_risk_geojson(db: AsyncSession = Depends(get_db)):
    """
    Returns Natural Earth country GeoJSON with risk_score and ipc_phase
    merged into each feature's properties. Used by the frontend map for
    data-driven fill coloring — no feature-state required.
    """
    # Fetch latest risk score per country in one query
    result = await db.execute(
        select(Country.iso_code, RiskScore.score, RiskScore.ipc_phase, RiskScore.trend)
        .join(RiskScore, RiskScore.country_id == Country.id)
        .distinct(Country.iso_code)
        .order_by(Country.iso_code, desc(RiskScore.computed_at))
    )
    rows = result.all()
    risk_by_iso = {
        row.iso_code: {
            "risk_score": round(row.score, 4),
            "ipc_phase": row.ipc_phase,
            "trend": row.trend,
        }
        for row in rows
    }

    base = await _get_base_geojson()

    # Merge risk data into feature properties
    features = []
    for feature in base.get("features", []):
        raw_props = feature.get("properties", {})
        # geo-countries dataset uses ISO3166-1-Alpha-3; older files used ISO_A3
        iso = raw_props.get("ISO_A3") or raw_props.get("ISO3166-1-Alpha-3") or ""
        risk_data = risk_by_iso.get(iso, {"risk_score": None, "ipc_phase": None, "trend": None})
        props = {
            **raw_props,
            **risk_data,
            "ISO_A3": iso,
            "ADMIN": raw_props.get("ADMIN") or raw_props.get("name") or "",
        }
        features.append({**feature, "properties": props})

    return JSONResponse({"type": "FeatureCollection", "features": features})
