"""IA logs model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class IALog(Base):
    """Trace IA operations for observability and audit."""

    __tablename__ = "ia_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    user_upn: Mapped[str | None] = mapped_column(String, index=True)
    ticket_id: Mapped[str | None] = mapped_column(String, index=True)
    operation: Mapped[str | None] = mapped_column(String)  # generate_reply / interpret_conversation
    message_type: Mapped[str | None] = mapped_column(String)  # primera_respuesta / actualizacion / cierre / interpretacion
    model: Mapped[str | None] = mapped_column(String)
    success: Mapped[bool | None] = mapped_column(Boolean)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    prompt_chars: Mapped[int | None] = mapped_column(Integer)
    response_chars: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
