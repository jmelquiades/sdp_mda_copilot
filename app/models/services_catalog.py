"""Services catalog model."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ServiceCatalog(Base):
    """Catalog of services and communication SLA overrides."""

    __tablename__ = "services_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    service_code: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text)
    requirements: Mapped[str | None] = mapped_column(Text)
    first_response_notes: Mapped[str | None] = mapped_column(Text)
    update_notes: Mapped[str | None] = mapped_column(Text)
    closure_notes: Mapped[str | None] = mapped_column(Text)
    comm_sla_p1_hours: Mapped[float | None] = mapped_column(Numeric)
    comm_sla_p2_hours: Mapped[float | None] = mapped_column(Numeric)
    comm_sla_p3_hours: Mapped[float | None] = mapped_column(Numeric)
    comm_sla_p4_hours: Mapped[float | None] = mapped_column(Numeric)
    sdp_mapping_info: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
