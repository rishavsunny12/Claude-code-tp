from datetime import datetime
from sqlalchemy import Integer, Float, SmallInteger, BigInteger, String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country_id: Mapped[int] = mapped_column(Integer, ForeignKey("countries.id"), nullable=False, index=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    score: Mapped[float] = mapped_column(Float, nullable=False)           # 0.0–1.0
    ipc_phase: Mapped[int | None] = mapped_column(SmallInteger)           # 1–5
    affected_pop: Mapped[int | None] = mapped_column(BigInteger)
    trend: Mapped[str | None] = mapped_column(String(20))                 # improving | stable | deteriorating
    factors: Mapped[dict | None] = mapped_column(JSON)
