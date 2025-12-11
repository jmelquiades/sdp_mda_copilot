"""Endpoints for tickets list."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.config import settings
from app.core.sdp_client import SdpClient
from app.db.session import get_db
from app.models.ticket_flags import TicketFlags
from app.models.technician_mapping import TechnicianMapping
from app.schemas.tickets import TicketItem, TicketsResponse

router = APIRouter(prefix="/api", tags=["tickets"])


def get_sdp_client() -> SdpClient:
    return SdpClient()


async def _resolve_technician_id(db: AsyncSession, user_upn: str) -> str:
    result = await db.execute(
        select(TechnicianMapping).where(TechnicianMapping.user_upn == user_upn, TechnicianMapping.active.is_(True))
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user_not_configured")
    return mapping.technician_id_sdp


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    # Try ISO first
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _select_sla_hours(service_code: Optional[str], priority: Optional[str], comm_default: float) -> float:
    # Placeholder: service_code is not available from gateway today.
    # Return default SLA for now.
    return comm_default


@router.get("/tickets", response_model=TicketsResponse)
async def list_tickets(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    sdp_client: SdpClient = Depends(get_sdp_client),
) -> TicketsResponse:
    """Return tickets assigned to the authenticated technician with communication info."""
    technician_id = await _resolve_technician_id(db, current_user)

    # Call gateway
    tickets = await sdp_client.get_assigned_requests(technician_id)

    now = datetime.now(tz=timezone.utc)
    comm_default = settings.comm_sla_default_hours
    response_items: List[TicketItem] = []

    for t in tickets:
        # Prefer explicit last_contact; fallback to last_public_reply_time returned by gateway.
        raw_contact = t.get("last_contact") or t.get("last_public_reply_time")
        last_contact_dt = _parse_datetime(raw_contact)
        hours_since = None
        if last_contact_dt:
            hours_since = (now - last_contact_dt).total_seconds() / 3600

        comm_sla = _select_sla_hours(t.get("service_code"), t.get("priority"), comm_default)
        is_silent = False
        if hours_since is not None and comm_sla is not None:
            is_silent = hours_since >= comm_sla

        # Upsert ticket_flags
        result = await db.execute(select(TicketFlags).where(TicketFlags.ticket_id == str(t.get("id"))))
        flags = result.scalar_one_or_none()
        if not flags:
            flags = TicketFlags(ticket_id=str(t.get("id")))
            db.add(flags)
        flags.display_id = t.get("display_id")
        flags.status = t.get("status")
        flags.priority = t.get("priority")
        flags.last_user_contact_at = last_contact_dt
        flags.hours_since_last_user_contact = hours_since
        flags.communication_sla_hours = comm_sla
        flags.is_silent = is_silent

        response_items.append(
            TicketItem(
                id=str(t.get("id")),
                display_id=str(t.get("display_id") or t.get("id")),
                subject=t.get("subject"),
                status=t.get("status"),
                priority=t.get("priority"),
                last_user_contact_at=last_contact_dt,
                hours_since_last_user_contact=hours_since,
                communication_sla_hours=comm_sla,
                is_silent=is_silent,
                experience_review_requested=bool(flags.experience_review_requested),
            )
        )

    await db.commit()
    return TicketsResponse(tickets=response_items)
