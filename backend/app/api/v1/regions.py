from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.models.country import Country
from app.models.risk_score import RiskScore
from app.models.ndvi_data import NDVIData
from app.models.rainfall_data import RainfallData

router = APIRouter(prefix="/regions", tags=["regions"])


class RegionSummary(BaseModel):
    iso_code: str
    name: str
    latitude: Optional[float]
    longitude: Optional[float]
    risk_score: Optional[float]
    ipc_phase: Optional[int]
    affected_population: Optional[int]
    trend: Optional[str]
    ndvi_anomaly: Optional[float]
    rainfall_anomaly_pct: Optional[float]


class NDVIPoint(BaseModel):
    date: date
    ndvi_mean: float
    ndvi_anomaly: Optional[float]


class RainfallPoint(BaseModel):
    date: date
    rainfall_mm: float
    anomaly_pct: Optional[float]


class RegionDetail(RegionSummary):
    ndvi_history: list[NDVIPoint]
    rainfall_history: list[RainfallPoint]
    risk_factors: Optional[dict]


@router.get("", response_model=list[RegionSummary])
async def list_regions(db: AsyncSession = Depends(get_db)):
    """Return all countries with their latest risk scores."""
    result = await db.execute(
        select(Country).order_by(Country.name)
    )
    countries = result.scalars().all()

    summaries = []
    for country in countries:
        latest_score = await _get_latest_risk_score(db, country.id)
        latest_ndvi = await _get_latest_ndvi(db, country.id)
        latest_rainfall = await _get_latest_rainfall(db, country.id)

        summaries.append(RegionSummary(
            iso_code=country.iso_code,
            name=country.name,
            latitude=country.latitude,
            longitude=country.longitude,
            risk_score=latest_score.score if latest_score else None,
            ipc_phase=latest_score.ipc_phase if latest_score else None,
            affected_population=latest_score.affected_pop if latest_score else None,
            trend=latest_score.trend if latest_score else None,
            ndvi_anomaly=latest_ndvi.ndvi_anomaly if latest_ndvi else None,
            rainfall_anomaly_pct=latest_rainfall.anomaly_pct if latest_rainfall else None,
        ))

    return summaries


@router.get("/{iso_code}", response_model=RegionDetail)
async def get_region(iso_code: str, db: AsyncSession = Depends(get_db)):
    """Return full detail for a single country including historical trends."""
    result = await db.execute(
        select(Country).where(Country.iso_code == iso_code.upper())
    )
    country = result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {iso_code} not found")

    latest_score = await _get_latest_risk_score(db, country.id)
    latest_ndvi = await _get_latest_ndvi(db, country.id)
    latest_rainfall = await _get_latest_rainfall(db, country.id)

    # Fetch 90-day history
    ndvi_history = await _get_ndvi_history(db, country.id, limit=6)
    rainfall_history = await _get_rainfall_history(db, country.id, limit=6)

    return RegionDetail(
        iso_code=country.iso_code,
        name=country.name,
        latitude=country.latitude,
        longitude=country.longitude,
        risk_score=latest_score.score if latest_score else None,
        ipc_phase=latest_score.ipc_phase if latest_score else None,
        affected_population=latest_score.affected_pop if latest_score else None,
        trend=latest_score.trend if latest_score else None,
        ndvi_anomaly=latest_ndvi.ndvi_anomaly if latest_ndvi else None,
        rainfall_anomaly_pct=latest_rainfall.anomaly_pct if latest_rainfall else None,
        ndvi_history=[NDVIPoint(date=r.date, ndvi_mean=r.ndvi_mean, ndvi_anomaly=r.ndvi_anomaly) for r in ndvi_history],
        rainfall_history=[RainfallPoint(date=r.date, rainfall_mm=r.rainfall_mm, anomaly_pct=r.anomaly_pct) for r in rainfall_history],
        risk_factors=latest_score.factors if latest_score else None,
    )


async def _get_latest_risk_score(db: AsyncSession, country_id: int) -> Optional[RiskScore]:
    result = await db.execute(
        select(RiskScore)
        .where(RiskScore.country_id == country_id)
        .order_by(desc(RiskScore.computed_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _get_latest_ndvi(db: AsyncSession, country_id: int) -> Optional[NDVIData]:
    result = await db.execute(
        select(NDVIData)
        .where(NDVIData.country_id == country_id)
        .order_by(desc(NDVIData.date))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _get_latest_rainfall(db: AsyncSession, country_id: int) -> Optional[RainfallData]:
    result = await db.execute(
        select(RainfallData)
        .where(RainfallData.country_id == country_id)
        .order_by(desc(RainfallData.date))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _get_ndvi_history(db: AsyncSession, country_id: int, limit: int) -> list[NDVIData]:
    result = await db.execute(
        select(NDVIData)
        .where(NDVIData.country_id == country_id)
        .order_by(desc(NDVIData.date))
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))


async def _get_rainfall_history(db: AsyncSession, country_id: int, limit: int) -> list[RainfallData]:
    result = await db.execute(
        select(RainfallData)
        .where(RainfallData.country_id == country_id)
        .order_by(desc(RainfallData.date))
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))
