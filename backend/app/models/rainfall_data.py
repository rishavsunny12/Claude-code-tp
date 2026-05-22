from datetime import date, datetime
from sqlalchemy import Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RainfallData(Base):
    __tablename__ = "rainfall_data"
    __table_args__ = (UniqueConstraint("country_id", "date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country_id: Mapped[int] = mapped_column(Integer, ForeignKey("countries.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)         # month start
    rainfall_mm: Mapped[float] = mapped_column(Float, nullable=False)
    anomaly_pct: Mapped[float | None] = mapped_column(Float)        # % vs 1981-2010 baseline
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
