"""Endpoints IA (hito 6)."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAIError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.core.config import settings
from app.core.ia_client import IAClient
from app.core.sdp_client import SdpClient
from app.db.session import get_db
from app.models.ia_logs import IALog
from app.models.org_profile import OrgProfile
from app.models.persona_config import PersonaConfig
from app.models.services_catalog import ServiceCatalog
from app.models.settings import Setting
from app.models.technician_mapping import TechnicianMapping
from app.schemas.ia import (
    GenerateReplyRequest,
    GenerateReplyResponse,
    InterpretConversationRequest,
    InterpretConversationResponse,
)

router = APIRouter(prefix="/api/ia", tags=["ia"])


def get_sdp_client() -> SdpClient:
    return SdpClient()


def get_ia_client() -> IAClient:
    return IAClient()


async def _resolve_technician_id(db: AsyncSession, user_upn: str) -> str:
    result = await db.execute(
        select(TechnicianMapping).where(TechnicianMapping.user_upn == user_upn, TechnicianMapping.active.is_(True))
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user_not_configured")
    return mapping.technician_id_sdp


async def _load_settings(db: AsyncSession) -> Dict[str, str]:
    result = await db.execute(select(Setting))
    rows = result.scalars().all()
    return {row.key: row.value for row in rows}


async def _load_persona(db: AsyncSession) -> PersonaConfig:
    result = await db.execute(select(PersonaConfig).where(PersonaConfig.active.is_(True)).order_by(PersonaConfig.id.desc()))
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="persona_not_configured")
    return persona


async def _load_org_profile(db: AsyncSession) -> OrgProfile:
    result = await db.execute(select(OrgProfile).order_by(OrgProfile.id.asc()))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="org_profile_not_configured")
    return org


async def _load_service(db: AsyncSession, service_code: Optional[str]) -> Optional[ServiceCatalog]:
    if not service_code:
        return None
    result = await db.execute(
        select(ServiceCatalog).where(ServiceCatalog.service_code == str(service_code))
    )
    return result.scalar_one_or_none()


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _build_system_prompt(persona: PersonaConfig, org: OrgProfile) -> str:
    parts: List[str] = []
    if persona.system_prompt_template:
        parts.append(persona.system_prompt_template.strip())
    else:
        if persona.role_description:
            parts.append(f"Rol: {persona.role_description}")
        if persona.tone_attributes:
            tones = ", ".join(persona.tone_attributes) if isinstance(persona.tone_attributes, list) else str(persona.tone_attributes)
            parts.append(f"Tono: {tones}")
        if persona.rules:
            rules = persona.rules if isinstance(persona.rules, list) else [str(persona.rules)]
            parts.append("Reglas: " + "; ".join(rules))

    if org.industry:
        parts.append(f"Industria: {org.industry}")
    if org.context:
        parts.append(f"Contexto organización: {org.context}")
    if org.tone_notes:
        parts.append(f"Notas de tono: {org.tone_notes}")
    if org.critical_services:
        parts.append(f"Servicios críticos: {org.critical_services}")
    parts.append("Responde siempre en español y sé conciso.")
    return "\n".join(parts)


def _format_history(events: List[dict], limit: int) -> str:
    trimmed = events[-limit:] if limit and limit > 0 else events
    lines: List[str] = []
    for ev in trimmed:
        ts = ev.get("timestamp")
        lines.append(
            f"[{ts}] ({ev.get('visibility')}/{ev.get('author_type')}) {ev.get('author_name')}: {ev.get('text')}"
        )
    return "\n".join(lines)


def _format_internal(events: List[dict], limit: int) -> str:
    internal = [e for e in events if (e.get("visibility") or "").lower() == "interno"]
    trimmed = internal[-limit:] if limit and limit > 0 else internal
    return "\n".join(
        f"[{e.get('timestamp')}] {e.get('author_name')}: {e.get('text')}" for e in trimmed
    )


def _build_user_prompt(
    detail: dict,
    history: List[dict],
    service: Optional[ServiceCatalog],
    settings_map: Dict[str, str],
    req: GenerateReplyRequest,
    draft: Optional[str],
) -> str:
    requester = detail.get("requester") or {}
    requester_name = requester.get("name") or detail.get("requester_name")
    requester_email = requester.get("email") or requester.get("email_id") or detail.get("requester_email")
    last_contact = detail.get("last_user_contact_at") or detail.get("last_public_reply_time")
    created_time = detail.get("created_time")

    max_hist = int(settings_map.get("max_history_messages_in_prompt", 10))
    max_notes = int(settings_map.get("max_internal_notes_in_prompt", 5))

    history_txt = _format_history(history, max_hist)
    internal_txt = _format_internal(history, max_notes)
    service_line = None
    if service:
        service_line = f"{service.name} (code {service.service_code})"
    else:
        service_line = str(detail.get("service_code") or "N/D")

    return (
        f"Tipo de mensaje: {req.message_type}\n"
        f"Ticket: {detail.get('id')} / {detail.get('display_id')}\n"
        f"Asunto: {detail.get('subject')}\n"
        f"Estado: {detail.get('status')} | Prioridad: {detail.get('priority')}\n"
        f"Servicio: {service_line}\n"
        f"Solicitante: {requester_name} ({requester_email})\n"
        f"Creado: {created_time}\n"
        f"Último contacto usuario: {last_contact}\n"
        f"Descripción: {detail.get('description')}\n"
        f"Historial reciente:\n{history_txt}\n"
        f"Notas internas recientes:\n{internal_txt}\n"
        f"Borrador del técnico (si hay): {draft or 'N/A'}\n"
        "Entrega una sola respuesta sugerida y accionable, breve, en español."
    )


def _build_interpret_prompt(
    detail: dict,
    history: List[dict],
    settings_map: Dict[str, str],
) -> str:
    max_hist = int(settings_map.get("max_history_messages_in_prompt", 10))
    history_txt = _format_history(history, max_hist)
    return (
        "Analiza el historial del ticket y sugiere enfoque/acción próxima.\n"
        f"Ticket: {detail.get('id')} / {detail.get('display_id')}\n"
        f"Asunto: {detail.get('subject')}\n"
        f"Estado: {detail.get('status')} | Prioridad: {detail.get('priority')}\n"
        f"Historial reciente:\n{history_txt}\n"
        "Devuelve solo una sugerencia breve (no redactes el mensaje final)."
    )


@router.post("/generate_reply", response_model=GenerateReplyResponse)
async def generate_reply(
    req: GenerateReplyRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    sdp_client: SdpClient = Depends(get_sdp_client),
    ia_client: IAClient = Depends(get_ia_client),
) -> GenerateReplyResponse:
    """Genera mensaje sugerido con IA para un ticket."""
    user_upn = current_user
    # valida mapeo
    await _resolve_technician_id(db, user_upn)

    detail = await sdp_client.get_request_detail(req.ticket_id)
    history = await sdp_client.get_request_history(req.ticket_id)

    settings_map = await _load_settings(db)
    persona = await _load_persona(db)
    org = await _load_org_profile(db)
    service_entry = await _load_service(db, detail.get("service_code"))

    # Construir mensajes
    temperature = float(settings_map.get("temperature", 0.3))
    max_tokens = int(settings_map.get("max_tokens", 400))
    system_prompt = _build_system_prompt(persona, org)
    user_prompt = _build_user_prompt(detail, history, service_entry, settings_map, req, req.draft)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # Llamar IA y registrar log
    started = datetime.now(tz=timezone.utc)
    log = IALog(
        user_upn=user_upn,
        ticket_id=req.ticket_id,
        operation="generate_reply",
        message_type=req.message_type,
        model=settings.azure_openai_deployment_gpt,
    )
    db.add(log)
    try:
        reply = await ia_client.generate_reply(messages, temperature=temperature, max_tokens=max_tokens)
        log.success = True
        log.response_chars = len(reply)
        log.prompt_chars = sum(len(m["content"]) for m in messages)
        log.latency_ms = int((datetime.now(tz=timezone.utc) - started).total_seconds() * 1000)
        await db.commit()
        return GenerateReplyResponse(suggested_message=reply)
    except OpenAIError as exc:
        log.success = False
        log.error_message = str(exc)
        log.latency_ms = int((datetime.now(tz=timezone.utc) - started).total_seconds() * 1000)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="ia_provider_error") from exc


@router.post("/interpret_conversation", response_model=InterpretConversationResponse)
async def interpret_conversation(
    req: InterpretConversationRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    sdp_client: SdpClient = Depends(get_sdp_client),
    ia_client: IAClient = Depends(get_ia_client),
) -> InterpretConversationResponse:
    """Sugiere enfoque para la siguiente respuesta, basado en historial."""
    user_upn = current_user
    await _resolve_technician_id(db, user_upn)

    detail = await sdp_client.get_request_detail(req.ticket_id)
    history = await sdp_client.get_request_history(req.ticket_id)
    settings_map = await _load_settings(db)
    persona = await _load_persona(db)
    org = await _load_org_profile(db)

    temperature = float(settings_map.get("temperature", 0.3))
    max_tokens = int(settings_map.get("max_tokens", 400))
    system_prompt = _build_system_prompt(persona, org)
    user_prompt = _build_interpret_prompt(detail, history, settings_map)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    started = datetime.now(tz=timezone.utc)
    log = IALog(
        user_upn=user_upn,
        ticket_id=req.ticket_id,
        operation="interpret_conversation",
        message_type="interpretacion",
        model=settings.azure_openai_deployment_gpt,
    )
    db.add(log)
    try:
        suggestion = await ia_client.interpret_conversation(messages, temperature=temperature, max_tokens=max_tokens)
        log.success = True
        log.response_chars = len(suggestion)
        log.prompt_chars = sum(len(m["content"]) for m in messages)
        log.latency_ms = int((datetime.now(tz=timezone.utc) - started).total_seconds() * 1000)
        await db.commit()
        return InterpretConversationResponse(suggestion=suggestion)
    except OpenAIError as exc:
        log.success = False
        log.error_message = str(exc)
        log.latency_ms = int((datetime.now(tz=timezone.utc) - started).total_seconds() * 1000)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="ia_provider_error") from exc
