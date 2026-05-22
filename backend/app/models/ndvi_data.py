from datetime import date, datetime
from sqlalchemy import Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class NDVIData(Base):
    __tablename__ = "ndvi_data"
    __table_args__ = (UniqueConstraint("country_id", "date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country_id: Mapped[int] = mapped_column(Integer, ForeignKey("countries.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    ndvi_mean: Mapped[float] = mapped_column(Float, nullable=False)
    ndvi_anomaly: Mapped[float | None] = mapped_column(Float)   # std deviations from 20yr baseline
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
