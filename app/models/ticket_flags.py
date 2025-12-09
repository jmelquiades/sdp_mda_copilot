"""Ticket flags model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TicketFlags(Base):
    """Per-ticket communication and review flags."""

    __tablename__ = "ticket_flags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    display_id: Mapped[str | None] = mapped_column(String)
    service_code: Mapped[str | None] = mapped_column(String)
    priority: Mapped[str | None] = mapped_column(String)
    status: Mapped[str | None] = mapped_column(String)
    last_user_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hours_since_last_user_contact: Mapped[float | None] = mapped_column(Numeric)
    communication_sla_hours: Mapped[float | None] = mapped_column(Numeric)
    is_silent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    experience_review_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    last_review_request_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
