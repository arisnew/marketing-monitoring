from __future__ import annotations
import json
import logging
import smtplib
from email.message import EmailMessage

import httpx

from app.config import get_settings
from app.models.enums import CheckStatus
from app.models.monitor import MonitorRule

logger = logging.getLogger(__name__)


async def notify_status_change(
    rule: MonitorRule,
    previous: CheckStatus,
    current: CheckStatus,
    message: str,
    webhook_url: str | None = None,
    notify_email: str | None = None,
) -> None:
    if previous == current:
        return

    payload = {
        "event": "monitor.status_changed",
        "rule_id": rule.id,
        "rule_name": rule.name,
        "previous_status": previous.value,
        "current_status": current.value,
        "message": message,
    }
    settings = get_settings()
    url = webhook_url or settings.default_notify_webhook_url
    if url:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                await client.post(url, json=payload)
        except Exception:
            logger.exception("Webhook notification failed")

    recipient = notify_email
    if recipient and settings.smtp_host:
        _send_email(recipient, f"[Marketing Monitor] {rule.name}: {current.value}", json.dumps(payload, indent=2))


def _send_email(to: str, subject: str, body: str) -> None:
    settings = get_settings()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from or settings.smtp_user or "monitor@localhost"
    msg["To"] = to
    msg.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)
