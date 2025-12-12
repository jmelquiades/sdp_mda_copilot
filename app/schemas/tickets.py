"""Schemas for tickets responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TicketItem(BaseModel):
    id: str
    display_id: Optional[str] = None
    subject: Optional[str] = None
    requester: Optional[dict] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    service_code: Optional[str] = None
    last_user_contact_at: Optional[datetime] = None
    hours_since_last_user_contact: Optional[float] = None
    communication_sla_hours: float
    is_silent: bool
    experience_review_requested: bool


class TicketsResponse(BaseModel):
    tickets: List[TicketItem] = Field(default_factory=list)


class ServiceCatalogItem(BaseModel):
    service_code: str
    name: Optional[str] = None
    short_description: Optional[str] = None
    comm_sla_p1_hours: Optional[float] = None
    comm_sla_p2_hours: Optional[float] = None
    comm_sla_p3_hours: Optional[float] = None
    comm_sla_p4_hours: Optional[float] = None


class TicketDetail(BaseModel):
    id: str
    display_id: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    requester: Optional[dict] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    site: Optional[str] = None
    group: Optional[str] = None
    technician_id: Optional[int] = None
    created_time: Optional[datetime] = None
    sla: Optional[dict] = None
    service_code: Optional[str] = None
    service: Optional[ServiceCatalogItem] = None
    last_user_contact_at: Optional[datetime] = None
    hours_since_last_user_contact: Optional[float] = None
    communication_sla_hours: Optional[float] = None
    is_silent: Optional[bool] = None
    experience_review_requested: bool = False

    model_config = {
        "exclude_none": True,
        "extra": "ignore",
    }


class TicketHistoryEvent(BaseModel):
    event_id: Optional[int] = None
    type: Optional[str] = None
    author_name: Optional[str] = None
    author_type: Optional[str] = None
    visibility: Optional[str] = None
    timestamp: Optional[datetime] = None
    text: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None


class TicketHistoryResponse(BaseModel):
    events: List[TicketHistoryEvent] = Field(default_factory=list)
