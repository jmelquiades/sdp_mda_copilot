"""Endpoints for tickets list."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.config import settings
from app.core.sdp_client import SdpClient
from app.db.session import get_db
from app.models.services_catalog import ServiceCatalog
from app.models.ticket_flags import TicketFlags
from app.models.technician_mapping import TechnicianMapping
from app.schemas.tickets import (
    ServiceCatalogItem,
    TicketDetail,
    TicketHistoryEvent,
    TicketHistoryResponse,
    TicketItem,
    TicketsResponse,
)

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


def _select_comm_sla(service: Optional[ServiceCatalog], priority: Optional[str], default_hours: float) -> float:
    """Pick SLA from service catalog given priority; fallback to default."""
    if not service:
        return default_hours
    priority_key = (priority or "").strip().lower()
    mapping = {
        "p1": service.comm_sla_p1_hours,
        "p2": service.comm_sla_p2_hours,
        "p3": service.comm_sla_p3_hours,
        "p4": service.comm_sla_p4_hours,
    }
    value = mapping.get(priority_key)
    return float(value) if value is not None else default_hours


def _extract_name(obj: Optional[dict | str]) -> Optional[str]:
    if obj is None:
        return None
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return obj.get("name") or obj.get("display_value") or obj.get("display_name") or obj.get("value")
    return None


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
        service_code = t.get("service_code")
        if service_code is not None:
            service_code = str(service_code)
        # El gateway expone la última comunicación como last_user_contact_at (alias de last_public_reply_time).
        last_contact_dt = _parse_datetime(t.get("last_user_contact_at") or t.get("last_public_reply_time"))
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
        flags.service_code = service_code
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
                service_code=service_code,
                last_user_contact_at=last_contact_dt,
                hours_since_last_user_contact=hours_since,
                communication_sla_hours=comm_sla,
                is_silent=is_silent,
                experience_review_requested=bool(flags.experience_review_requested),
            )
        )

    await db.commit()
    return TicketsResponse(tickets=response_items)


async def _get_service_entry(db: AsyncSession, service_code: Optional[str]) -> Optional[ServiceCatalog]:
    if not service_code:
        return None
    result = await db.execute(
        select(ServiceCatalog).where(func.lower(ServiceCatalog.service_code) == service_code.strip().lower())
    )
    return result.scalar_one_or_none()


@router.get("/tickets/{ticket_id}", response_model=TicketDetail)
async def ticket_detail(
    ticket_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    sdp_client: SdpClient = Depends(get_sdp_client),
) -> TicketDetail:
    """Detalle del ticket combinando gateway, SLA de servicio y flags locales."""
    # Valida que el usuario esté mapeado (aunque no usemos el id aquí).
    await _resolve_technician_id(db, current_user)

    detail = await sdp_client.get_request_detail(ticket_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ticket_not_found")

    service_code = detail.get("service_code")
    if service_code is not None:
        service_code = str(service_code)
    priority_name = _extract_name(detail.get("priority"))
    status_name = _extract_name(detail.get("status"))
    display_id = str(detail.get("display_id") or detail.get("id"))
    service_entry = await _get_service_entry(db, service_code)
    service_out = None
    if service_entry:
        service_out = ServiceCatalogItem(
            service_code=service_entry.service_code,
            name=service_entry.name,
            short_description=service_entry.short_description,
            comm_sla_p1_hours=float(service_entry.comm_sla_p1_hours) if service_entry.comm_sla_p1_hours else None,
            comm_sla_p2_hours=float(service_entry.comm_sla_p2_hours) if service_entry.comm_sla_p2_hours else None,
            comm_sla_p3_hours=float(service_entry.comm_sla_p3_hours) if service_entry.comm_sla_p3_hours else None,
            comm_sla_p4_hours=float(service_entry.comm_sla_p4_hours) if service_entry.comm_sla_p4_hours else None,
        )

    site_name = _extract_name(detail.get("site"))
    group_name = _extract_name(detail.get("group"))

    last_contact_dt = _parse_datetime(
        detail.get("last_user_contact_at") or detail.get("last_public_reply_time")
    )
    now = datetime.now(tz=timezone.utc)
    hours_since = (now - last_contact_dt).total_seconds() / 3600 if last_contact_dt else None
    comm_sla = _select_comm_sla(service_entry, priority_name, settings.comm_sla_default_hours)
    is_silent = bool(hours_since is not None and comm_sla is not None and hours_since >= comm_sla)

    # Upsert flags
    result = await db.execute(select(TicketFlags).where(TicketFlags.ticket_id == str(detail.get("id"))))
    flags = result.scalar_one_or_none()
    if not flags:
        flags = TicketFlags(ticket_id=str(detail.get("id")))
        db.add(flags)
    flags.display_id = display_id
    flags.service_code = service_code
    flags.status = status_name
    flags.priority = priority_name
    flags.last_user_contact_at = last_contact_dt
    flags.hours_since_last_user_contact = hours_since
    flags.communication_sla_hours = comm_sla
    flags.is_silent = is_silent

    await db.commit()

    return TicketDetail(
        id=str(detail.get("id")),
        display_id=display_id,
        subject=detail.get("subject"),
        description=detail.get("description"),
        requester=detail.get("requester"),
        status=status_name,
        priority=priority_name,
        site=site_name,
        group=group_name,
        technician_id=detail.get("technician_id"),
        created_time=_parse_datetime(detail.get("created_time")),
        sla=detail.get("sla"),
        service_code=service_code,
        service=service_out,
        last_user_contact_at=last_contact_dt,
        hours_since_last_user_contact=hours_since,
        communication_sla_hours=comm_sla,
        is_silent=is_silent,
        experience_review_requested=bool(flags.experience_review_requested),
    )


@router.get("/tickets/{ticket_id}/history", response_model=TicketHistoryResponse)
async def ticket_history(
    ticket_id: str,
    current_user: CurrentUser,
    sdp_client: SdpClient = Depends(get_sdp_client),
) -> TicketHistoryResponse:
    """Historial cronológico de eventos del ticket."""
    events = await sdp_client.get_request_history(ticket_id)
    # Orden cronológico ascendente por timestamp si viene.
    def _sort_key(ev: dict) -> float:
        dt = _parse_datetime(ev.get("timestamp"))
        return dt.timestamp() if dt else 0.0

    events_sorted = sorted(events, key=_sort_key)
    parsed_events = [
        TicketHistoryEvent(
            event_id=e.get("event_id"),
            type=e.get("type"),
            author_name=e.get("author_name"),
            author_type=e.get("author_type"),
            visibility=e.get("visibility"),
            timestamp=_parse_datetime(e.get("timestamp")),
            text=e.get("text"),
            old_value=e.get("old_value"),
            new_value=e.get("new_value"),
        )
        for e in events_sorted
    ]
    return TicketHistoryResponse(events=parsed_events)
