"""Schemas for experiencia review endpoints."""

from typing import Optional

from pydantic import BaseModel


class ReviewValidateResponse(BaseModel):
    valid: bool
    ticket_id: Optional[str] = None


class ReviewSubmitRequest(BaseModel):
    token: str
    reason: str
    comment: Optional[str] = None


class ReviewSubmitResponse(BaseModel):
    ok: bool = True
