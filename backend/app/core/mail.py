"""Outbound email — stdlib only.

Two backends are supported:

* ``console`` (default for development) — the message is rendered and logged to
  the application logger (and printed to the console) instead of being sent.
  This keeps local development email-free while the flow stays testable.
* ``smtp`` — sends via ``smtplib`` using the settings in :mod:`app.core.config`.

Creator keys are delivered to the recipient's registered email address, and
administrators are notified whenever a new key is escrowed or a key request
arrives.
"""

import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import settings

logger = logging.getLogger("mizizi.mail")


def _parse_address(address: str) -> tuple[str, str]:
    """Turn ``"Name <email>"`` (or a bare email) into (name, addr)."""
    if "<" in address and address.endswith(">"):
        name, _, addr = address.partition("<")
        return name.strip().strip('"'), addr.rstrip(">").strip()
    return "", address.strip()


def _build_message(to: str, subject: str, text: str) -> EmailMessage:
    msg = EmailMessage()
    from_name, from_addr = _parse_address(settings.mail_from or "Mizizi <no-reply@mizizi.org>")
    msg["From"] = formataddr((from_name, from_addr))
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    return msg


def _send_smtp(msg: EmailMessage) -> None:
    if not settings.smtp_host:
        raise RuntimeError("mail_backend=smtp requires SMTP_HOST to be set.")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password or "")
        server.send_message(msg)


def send_email(to: str, subject: str, text: str) -> bool:
    """Send an email, or log it when the console backend is active.

    Returns True when the message was accepted for delivery (or, in console
    mode, recorded). Never raises — failures are logged so a broken mail relay
    does not take down the archive.
    """
    try:
        msg = _build_message(to, subject, text)
        if settings.mail_backend == "smtp":
            _send_smtp(msg)
        else:
            rendered = (
                "=" * 60 + "\n[Mail · console backend]\n"
                f"To:      {msg['To']}\nSubject: {msg['Subject']}\n"
                + "-" * 60 + f"\n{text}\n" + "=" * 60
            )
            # Log AND print: uvicorn does not always attach a root handler, so
            # the developer needs to see the message on the console.
            logger.info("\n%s", rendered)
            print(rendered, flush=True)
        return True
    except Exception as exc:  # pragma: no cover - relay/network failures vary
        logger.error("Failed to send email to %s: %s", to, exc)
        return False
