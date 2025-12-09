"""Persona IA configuration model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PersonaConfig(Base):
    """Centralized persona definition for IA prompts."""

    __tablename__ = "persona_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_description: Mapped[str | None] = mapped_column(Text)
    tone_attributes: Mapped[dict | None] = mapped_column(JSONB)
    rules: Mapped[dict | None] = mapped_column(JSONB)
    max_reply_length: Mapped[int | None] = mapped_column(Integer)
    system_prompt_template: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
