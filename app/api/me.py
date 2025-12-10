"""Endpoint for /api/me."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.models.technician_mapping import TechnicianMapping
from app.schemas.me import MeResponse

router = APIRouter(prefix="/api", tags=["me"])


@router.get("/me", response_model=MeResponse)
async def get_me(current_user: CurrentUser, db: AsyncSession = Depends(get_db)) -> MeResponse:
    """Return mapping info for the authenticated user."""
    result = await db.execute(
        select(TechnicianMapping).where(TechnicianMapping.user_upn == current_user, TechnicianMapping.active.is_(True))
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user_not_configured")

    display_name = current_user  # mock; real scenario should use token claims
    return MeResponse(
        user_upn=mapping.user_upn,
        display_name=display_name,
        technician_id_sdp=mapping.technician_id_sdp,
    )
