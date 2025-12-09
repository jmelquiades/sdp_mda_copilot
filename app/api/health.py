"""Healthcheck endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


@router.get("/health", tags=["health"])
async def health(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Return ok if API and DB (schema Copilot) are reachable."""
    try:
        await db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="database_unavailable") from exc
    return {"status": "ok"}
