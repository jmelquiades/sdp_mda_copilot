"""Schemas for /api/me."""

from pydantic import BaseModel


class MeResponse(BaseModel):
    user_upn: str
    display_name: str
    technician_id_sdp: str
