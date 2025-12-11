"""Schemas for tickets responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TicketItem(BaseModel):
    id: str
    display_id: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    last_user_contact_at: Optional[datetime] = None
    hours_since_last_user_contact: Optional[float] = None
    communication_sla_hours: float
    is_silent: bool
    experience_review_requested: bool


class TicketsResponse(BaseModel):
    tickets: List[TicketItem] = Field(default_factory=list)
