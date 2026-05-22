from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.country import Country
from app.models.risk_score import RiskScore
from app.models.ndvi_data import NDVIData
from app.models.rainfall_data import RainfallData
from app.services.ai.chat import stream_chat_response, build_region_context

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str       # user | assistant
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    selected_iso: Optional[str] = None   # country currently selected in UI


@router.post("")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Stream a conversational AI response.
    Injects real region data context if a country is selected.
    """
    region_context = None
    if request.selected_iso:
        region_context = await _build_region_context(db, request.selected_iso.upper())

    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    async def event_stream():
        async for chunk in stream_chat_response(messages, region_context):
            # Escape SSE special chars
            safe_chunk = chunk.replace("\n", "\\n")
            yield f"data: {safe_chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


async def _build_region_context(db: AsyncSession, iso_code: str) -> Optional[str]:
    result = await db.execute(
        select(Country).where(Country.iso_code == iso_code)
    )
    country = result.scalar_one_or_none()
    if not country:
        return None

    score_result = await db.execute(
        select(RiskScore)
        .where(RiskScore.country_id == country.id)
        .order_by(desc(RiskScore.computed_at))
        .limit(1)
    )
    score = score_result.scalar_one_or_none()

    ndvi_result = await db.execute(
        select(NDVIData)
        .where(NDVIData.country_id == country.id)
        .order_by(desc(NDVIData.date))
        .limit(1)
    )
    ndvi = ndvi_result.scalar_one_or_none()

    rainfall_result = await db.execute(
        select(RainfallData)
        .where(RainfallData.country_id == country.id)
        .order_by(desc(RainfallData.date))
        .limit(1)
    )
    rainfall = rainfall_result.scalar_one_or_none()

    return build_region_context(
        country_name=country.name,
        iso_code=country.iso_code,
        risk_score=score.score if score else None,
        ipc_phase=score.ipc_phase if score else None,
        ndvi_anomaly=ndvi.ndvi_anomaly if ndvi else None,
        rainfall_anomaly_pct=rainfall.anomaly_pct if rainfall else None,
        affected_pop=score.affected_pop if score else None,
        trend=score.trend if score else None,
    )
