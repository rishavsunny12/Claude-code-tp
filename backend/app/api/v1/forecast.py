from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.models.country import Country
from app.models.risk_score import RiskScore
from app.models.ndvi_data import NDVIData
from app.models.rainfall_data import RainfallData
from app.services.ai.assessment import stream_risk_assessment

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.get("/{iso_code}")
async def get_forecast(iso_code: str, db: AsyncSession = Depends(get_db)):
    """
    Stream a Claude AI risk assessment for the given country.
    Uses real satellite and field data in the prompt.
    Returns Server-Sent Events (text/event-stream).
    """
    result = await db.execute(
        select(Country).where(Country.iso_code == iso_code.upper())
    )
    country = result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {iso_code} not found")

    # Fetch latest indicators
    score_result = await db.execute(
        select(RiskScore)
        .where(RiskScore.country_id == country.id)
        .order_by(desc(RiskScore.computed_at))
        .limit(1)
    )
    latest_score = score_result.scalar_one_or_none()

    ndvi_result = await db.execute(
        select(NDVIData)
        .where(NDVIData.country_id == country.id)
        .order_by(desc(NDVIData.date))
        .limit(2)
    )
    ndvi_records = ndvi_result.scalars().all()
    latest_ndvi = ndvi_records[0] if ndvi_records else None
    prev_ndvi = ndvi_records[1] if len(ndvi_records) > 1 else None
    ndvi_trend_30d = (
        (latest_ndvi.ndvi_mean - prev_ndvi.ndvi_mean) if latest_ndvi and prev_ndvi else None
    )

    rainfall_result = await db.execute(
        select(RainfallData)
        .where(RainfallData.country_id == country.id)
        .order_by(desc(RainfallData.date))
        .limit(1)
    )
    latest_rainfall = rainfall_result.scalar_one_or_none()

    async def event_stream():
        async for chunk in stream_risk_assessment(
            country_name=country.name,
            iso_code=country.iso_code,
            ndvi_current=latest_ndvi.ndvi_mean if latest_ndvi else None,
            ndvi_anomaly=latest_ndvi.ndvi_anomaly if latest_ndvi else None,
            ndvi_trend_30d=ndvi_trend_30d,
            rainfall_current_mm=latest_rainfall.rainfall_mm if latest_rainfall else None,
            rainfall_anomaly_pct=latest_rainfall.anomaly_pct if latest_rainfall else None,
            ipc_phase=latest_score.ipc_phase if latest_score else None,
            affected_pop=latest_score.affected_pop if latest_score else None,
            risk_score=latest_score.score if latest_score else 0.0,
            trend=latest_score.trend if latest_score else "stable",
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
