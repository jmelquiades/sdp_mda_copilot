"""Organization profile model."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class OrgProfile(Base):
    """Organization profile used as IA context."""

    __tablename__ = "org_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    industry: Mapped[str | None] = mapped_column(String)
    context: Mapped[str | None] = mapped_column(Text)
    critical_services: Mapped[dict | None] = mapped_column(JSONB)
    tone_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
