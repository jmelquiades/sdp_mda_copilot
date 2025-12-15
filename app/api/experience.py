"""Endpoints públicos para flujo de experiencia/review."""

from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.review_tokens import decode_token
from app.core.sdp_client import SdpClient
from app.core.config import settings
from app.db.session import get_db
from app.models.ticket_flags import TicketFlags
from app.models.settings import Setting
from app.schemas.experience import (
    ReviewSubmitRequest,
    ReviewSubmitResponse,
    ReviewValidateResponse,
)

router = APIRouter(prefix="/api/experience", tags=["experience"])


async def _load_settings(db: AsyncSession) -> Dict[str, dict]:
    result = await db.execute(select(Setting))
    rows = result.scalars().all()
    return {row.key: row.value for row in rows}


def _get_review_config(settings_map: Dict[str, dict]) -> tuple[str, int]:
    def _extract(key: str):
        val = settings_map.get(key) if settings_map else None
        if isinstance(val, dict) and "v" in val:
            return val.get("v")
        return val

    secret = _extract("review_token_secret")
    ttl_hours = _extract("review_token_ttl_hours")
    if not secret:
        secret = settings.review_token_secret
    if not secret:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="review_secret_missing")
    if ttl_hours is None:
        ttl_hours = settings.experience_review_token_ttl_hours
    try:
        ttl_hours_int = int(ttl_hours)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="review_ttl_invalid") from exc
    return secret, ttl_hours_int


@router.get("/review/validate", response_model=ReviewValidateResponse)
async def validate_token(
    token: str = Query(..., description="Token firmado que viene en el enlace del correo"),
    db: AsyncSession = Depends(get_db),
) -> ReviewValidateResponse:
    """Valida el token y devuelve el ticket asociado."""
    settings_map = await _load_settings(db)
    secret, _ = _get_review_config(settings_map)
    try:
        payload = decode_token(token, secret)
    except ValueError as exc:
        detail = str(exc)
        if detail == "token_expired":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="token_expired") from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_token") from exc
    return ReviewValidateResponse(valid=True, ticket_id=str(payload.get("ticket_id")))


@router.post("/review/submit", response_model=ReviewSubmitResponse)
async def submit_review(
    body: ReviewSubmitRequest,
    db: AsyncSession = Depends(get_db),
) -> ReviewSubmitResponse:
    """Registra la solicitud de revisión de experiencia en SDP y marca el flag local."""
    settings_map = await _load_settings(db)
    secret, _ = _get_review_config(settings_map)
    try:
        payload = decode_token(body.token, secret)
    except ValueError as exc:
        detail = str(exc)
        if detail == "token_expired":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="token_expired") from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_token") from exc

    ticket_id = str(payload.get("ticket_id"))
    if not ticket_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_token")

    note_parts = [f"Usuario solicitó revisión de experiencia. Motivo: {body.reason}"]
    if body.comment:
        note_parts.append(f"Comentario: {body.comment}")
    note_text = " | ".join(note_parts)

    client = SdpClient()
    # No pasamos technician_id: el gateway ya registra como nota interna del bot.
    await client.post_internal_note(ticket_id, note_text)

    # Upsert en ticket_flags
    result = await db.execute(select(TicketFlags).where(TicketFlags.ticket_id == ticket_id))
    flags = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if not flags:
        flags = TicketFlags(
            ticket_id=ticket_id,
            experience_review_requested=True,
            last_review_request_at=now,
        )
        db.add(flags)
    else:
        flags.experience_review_requested = True
        flags.last_review_request_at = now

    await db.commit()
    return ReviewSubmitResponse()
