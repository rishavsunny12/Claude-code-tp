from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.models.alert import Alert
from app.models.country import Country

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertResponse(BaseModel):
    id: int
    iso_code: str
    country_name: str
    severity: str
    message: str
    created_at: datetime
    resolved: bool


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    active_only: bool = True,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Return active food security alerts, ordered by severity then recency."""
    query = (
        select(Alert, Country.iso_code, Country.name)
        .join(Country, Alert.country_id == Country.id)
        .order_by(desc(Alert.created_at))
        .limit(limit)
    )
    if active_only:
        query = query.where(Alert.resolved_at.is_(None))

    result = await db.execute(query)
    rows = result.all()

    severity_order = {"emergency": 0, "warning": 1, "watch": 2}
    alerts = []
    for alert, iso_code, country_name in rows:
        alerts.append(AlertResponse(
            id=alert.id,
            iso_code=iso_code,
            country_name=country_name,
            severity=alert.severity,
            message=alert.message,
            created_at=alert.created_at,
            resolved=alert.resolved_at is not None,
        ))

    alerts.sort(key=lambda a: (severity_order.get(a.severity, 99), -a.created_at.timestamp()))
    return alerts
