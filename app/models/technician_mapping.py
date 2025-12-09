"""Technician mapping model."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TechnicianMapping(Base):
    """Map O365 user UPN to SDP technician id."""

    __tablename__ = "technician_mapping"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_upn: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    technician_id_sdp: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
