from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, UUID, func
from sqlalchemy.orm import Mapped, mapped_column
import uuid
from app.core.database import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(10), nullable=False)   # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
