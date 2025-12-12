"""Schemas para IA."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class GenerateReplyRequest(BaseModel):
    ticket_id: str = Field(..., description="ID del ticket en SDP")
    message_type: Literal["primera_respuesta", "actualizacion", "cierre"] = Field(...)
    draft: Optional[str] = Field(default=None, description="Borrador opcional del técnico")


class GenerateReplyResponse(BaseModel):
    suggested_message: str
