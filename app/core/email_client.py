"""SMTP client with optional OAuth2 (Office 365) for sending emails."""

from __future__ import annotations

import base64
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from time import time
from typing import Iterable, Optional

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.settings import Setting


class EmailSendError(Exception):
    """Raised when email delivery fails."""


@dataclass
class EmailConfig:
    server: str
    port: int
    username: str
    password: str
    sender: str
    bcc: Optional[str] = None
    oauth_tenant_id: Optional[str] = None
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None

    @property
    def use_oauth(self) -> bool:
        return bool(self.oauth_tenant_id and self.oauth_client_id and self.oauth_client_secret)


class EmailClient:
    """SMTP client that supports basic auth or OAuth2 XOAUTH2 (like controller)."""

    def __init__(self, config: EmailConfig):
        self.cfg = config
        self._oauth_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

    def send(
        self,
        to: Iterable[str],
        subject: str,
        plain_body: str,
        html_body: Optional[str] = None,
    ) -> None:
        msg = EmailMessage()
        msg["From"] = self.cfg.sender or self.cfg.username
        msg["To"] = ",".join([x for x in to if x])
        if self.cfg.bcc:
            msg["Bcc"] = self.cfg.bcc
        msg["Subject"] = subject
        msg.set_content(plain_body)
        if html_body:
            msg.add_alternative(html_body, subtype="html")

        try:
            with smtplib.SMTP(self.cfg.server, self.cfg.port, timeout=15) as smtp:
                smtp.starttls()
                if self.cfg.use_oauth:
                    token = self._ensure_token()
                    self._authenticate_xoauth2(smtp, token)
                else:
                    smtp.login(self.cfg.username, self.cfg.password)
                smtp.send_message(msg)
        except Exception as exc:  # pragma: no cover - external dependency
            raise EmailSendError(str(exc)) from exc

    def _ensure_token(self) -> str:
        if self._oauth_token and self._token_expires_at and time() < self._token_expires_at - 60:
            return self._oauth_token
        token, expires_in = self._fetch_oauth_token()
        self._oauth_token = token
        self._token_expires_at = time() + expires_in
        return token

    def _fetch_oauth_token(self) -> tuple[str, int]:
        if not self.cfg.use_oauth:
            raise EmailSendError("oauth_not_configured")
        resp = httpx.post(
            f"https://login.microsoftonline.com/{self.cfg.oauth_tenant_id}/oauth2/v2.0/token",
            data={
                "client_id": self.cfg.oauth_client_id,
                "client_secret": self.cfg.oauth_client_secret,
                "scope": "https://outlook.office365.com/.default",
                "grant_type": "client_credentials",
            },
            timeout=10,
        )
        try:
            resp.raise_for_status()
        except Exception as exc:
            raise EmailSendError(f"oauth_token_error: {exc}") from exc
        data = resp.json()
        return data["access_token"], int(data.get("expires_in", 3600))

    def _authenticate_xoauth2(self, smtp, token: str) -> None:
        auth_string = base64.b64encode(
            f"user={self.cfg.username}\x01auth=Bearer {token}\x01\x01".encode("utf-8")
        ).decode("utf-8")
        smtp.docmd("AUTH", "XOAUTH2 " + auth_string)


def get_email_client_from_settings() -> EmailClient:
    """Factory to build EmailClient from environment settings."""
    cfg = EmailConfig(
        server=settings.smtp_server,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        sender=settings.smtp_sender or settings.smtp_username,
        bcc=settings.smtp_bcc or None,
        oauth_tenant_id=settings.smtp_oauth_tenant_id or None,
        oauth_client_id=settings.smtp_oauth_client_id or None,
        oauth_client_secret=settings.smtp_oauth_client_secret or None,
    )
    if not cfg.username:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="email_not_configured")
    return EmailClient(cfg)


SMTP_SETTING_KEYS = {
    "smtp_server",
    "smtp_port",
    "smtp_username",
    "smtp_password",
    "smtp_sender",
    "smtp_bcc",
    "smtp_oauth_tenant_id",
    "smtp_oauth_client_id",
    "smtp_oauth_client_secret",
}


async def get_email_client_from_db(db: AsyncSession) -> EmailClient:
    """
    Build EmailClient using overrides stored in copilot.settings table.
    Falls back to environment values if a key is missing.
    """
    result = await db.execute(select(Setting).where(Setting.key.in_(SMTP_SETTING_KEYS)))
    rows = result.scalars().all()
    values = {row.key: row.value for row in rows}

    def val(key: str, default):
        v = values.get(key, default)
        # values in table are JSONB; if stored as primitives, return directly
        return v

    cfg = EmailConfig(
        server=str(val("smtp_server", settings.smtp_server)),
        port=int(val("smtp_port", settings.smtp_port)),
        username=str(val("smtp_username", settings.smtp_username or "")),
        password=str(val("smtp_password", settings.smtp_password or "")),
        sender=str(val("smtp_sender", settings.smtp_sender or settings.smtp_username or "")),
        bcc=str(val("smtp_bcc", settings.smtp_bcc or "")) or None,
        oauth_tenant_id=str(val("smtp_oauth_tenant_id", settings.smtp_oauth_tenant_id or "")) or None,
        oauth_client_id=str(val("smtp_oauth_client_id", settings.smtp_oauth_client_id or "")) or None,
        oauth_client_secret=str(val("smtp_oauth_client_secret", settings.smtp_oauth_client_secret or "")) or None,
    )
    if not cfg.username:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="email_not_configured")
    return EmailClient(cfg)
