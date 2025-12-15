"""HTTP client to talk to SDP_API_GW_OP."""

from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


class SdpClient:
    """Lightweight async client for the SDP gateway."""

    def __init__(self) -> None:
        self.base_url = settings.gateway_base_url.rstrip("/")
        self.client_name = settings.gateway_client
        self.api_key = settings.gateway_api_key

    async def get_assigned_requests(
        self,
        technician_id: str,
        *,
        statuses: Optional[List[str]] = None,
        priorities: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Call /request/assigned in the gateway."""
        headers = {
            "X-Cliente": self.client_name,
            "X-Api-Key": self.api_key,
        }
        params: Dict[str, str] = {"technician_id": str(technician_id)}
        if statuses:
            params["status"] = ",".join(statuses)
        if priorities:
            params["priority"] = ",".join(priorities)

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as client:
            resp = await client.get("/request/assigned", params=params, headers=headers)

        # Parse and bubble up gateway errors with more context.
        try:
            data = resp.json()
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="gateway_invalid_json") from exc

        if resp.status_code != 200 or not isinstance(data, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"gateway_request_failed (status={resp.status_code})",
            )

        if not data.get("ok"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=data.get("error") or "gateway_error",
            )

        return data.get("tickets", []) or []

    async def get_request_detail(self, ticket_id: str) -> Dict[str, Any]:
        """Call /request/{ticket_id} in the gateway."""
        headers = {
            "X-Cliente": self.client_name,
            "X-Api-Key": self.api_key,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as client:
            resp = await client.get(f"/request/{ticket_id}", headers=headers)
        try:
            data = resp.json()
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="gateway_invalid_json") from exc

        if resp.status_code != 200 or not isinstance(data, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"gateway_request_failed (status={resp.status_code})",
            )
        # Gateway puede devolver {"ok":true,"ticket":{...}} o el ticket directo.
        if "ticket" in data and isinstance(data.get("ticket"), dict):
            return data["ticket"]
        return data

    async def get_request_history(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Call /request/{ticket_id}/history in the gateway."""
        headers = {
            "X-Cliente": self.client_name,
            "X-Api-Key": self.api_key,
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as client:
            resp = await client.get(f"/request/{ticket_id}/history", headers=headers)
        try:
            data = resp.json()
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="gateway_invalid_json") from exc

        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"gateway_request_failed (status={resp.status_code})",
            )
        # Gateway puede devolver {"ok": true, "events": [...]} o la lista directa.
        if isinstance(data, dict) and "events" in data:
            events = data.get("events") or []
        else:
            events = data if isinstance(data, list) else []
        return events

    async def post_internal_note(self, ticket_id: str, text: str, technician_id: Optional[str] = None) -> None:
        """Send an internal note to SDP via gateway."""
        headers = {
            "X-Cliente": self.client_name,
            "X-Api-Key": self.api_key,
        }
        payload: Dict[str, Any] = {"text": text}
        if technician_id:
            payload["technician_id"] = str(technician_id)

        async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as client:
            resp = await client.post(f"/request/{ticket_id}/note_internal", json=payload, headers=headers)

        try:
            data = resp.json()
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="gateway_invalid_json") from exc

        if resp.status_code != 200 or not data.get("ok"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=data.get("error") or f"gateway_request_failed (status={resp.status_code})",
            )
