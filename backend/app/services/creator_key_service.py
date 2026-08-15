"""Creator-key recovery service.

Implements the hand-off between the creator (who lost their key) and the
administrator (who holds the escrowed copy):

1. A contributor requests their key via ``POST /creator-keys/requests``.
2. The administrator reviews the pending request in the admin console and
   issues it; the key is emailed to the requester's registered address and the
   escrow ledger records the issuance.
"""

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.models.creator_key import CreatorKeyEscrow, CreatorKeyRequest
from app.services import cultural_object_service


def _require_escrow(db: Session, object_id: uuid.UUID) -> CreatorKeyEscrow:
    escrow = (
        db.execute(
            select(CreatorKeyEscrow).where(CreatorKeyEscrow.cultural_object_id == object_id)
        )
        .scalars()
        .first()
    )
    if escrow is None:
        raise HTTPException(
            status_code=404,
            detail="No creator key is on record for this object.",
        )
    return escrow


def create_key_request(db: Session, user: User, object_id: uuid.UUID) -> CreatorKeyRequest:
    """The creator asks the administrator to email their key back.

    Only the object's own creator can request its key; the request lands in the
    admin console and is fulfilled there by an administrator.
    """
    obj = cultural_object_service.get_object_or_404(db, object_id)
    if obj.user_id is None or obj.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only request the key for objects you created.",
        )
    # Only objects that actually have an escrowed key are requestable.
    _require_escrow(db, object_id)

    open_request = (
        db.execute(
            select(CreatorKeyRequest).where(
                CreatorKeyRequest.user_id == user.id,
                CreatorKeyRequest.cultural_object_id == object_id,
                CreatorKeyRequest.status == "pending",
            )
        )
        .scalars()
        .first()
    )
    if open_request is not None:
        raise HTTPException(status_code=409, detail="You already have a pending key request for this object.")

    request = CreatorKeyRequest(user_id=user.id, cultural_object_id=object_id, status="pending")
    db.add(request)
    db.commit()
    db.refresh(request)

    from app.core.mail import send_email
    from app.models import ADMIN

    for admin in db.execute(select(User).where(User.role == ADMIN)).scalars().all():
        send_email(
            admin.email,
            f"[Mizizi] Creator key request — {obj.object_code}",
            (
                f"{user.email} ({user.display_name or 'no display name'}) has requested "
                f"the creator key for {obj.object_code} — {obj.title or '(untitled)'}.\n\n"
                "Review and issue it from the Mizizi admin console so the key can be "
                "emailed back to the contributor."
            ),
        )
    return request


def list_user_requests(db: Session, user: User) -> list[CreatorKeyRequest]:
    return list(
        db.execute(
            select(CreatorKeyRequest)
            .where(CreatorKeyRequest.user_id == user.id)
            .order_by(CreatorKeyRequest.created_at.desc())
        )
        .scalars()
        .all()
    )


def list_pending_requests(db: Session) -> list[CreatorKeyRequest]:
    return list(
        db.execute(
            select(CreatorKeyRequest)
            .where(CreatorKeyRequest.status == "pending")
            .order_by(CreatorKeyRequest.created_at.asc())
        )
        .scalars()
        .all()
    )


def issue_key(db: Session, admin: User, request_id: uuid.UUID) -> CreatorKeyRequest:
    """Email the escrowed creator key to the requester and close the request."""
    request = db.get(CreatorKeyRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Key request not found.")
    if request.status != "pending":
        raise HTTPException(status_code=409, detail="This request has already been decided.")

    requester = db.get(User, request.user_id)
    if requester is None:
        raise HTTPException(status_code=410, detail="The requesting account no longer exists.")
    escrow = _require_escrow(db, request.cultural_object_id)
    obj = escrow.cultural_object

    from app.core.mail import send_email

    sent = send_email(
        requester.email,
        f"Your Mizizi creator key — {obj.object_code}",
        (
            f"Hello {requester.display_name or requester.email},\n\n"
            f"The Mizizi Administrator has issued the creator key for your Cultural Object "
            f"{obj.object_code} — {obj.title or '(untitled)'}.\n\n"
            f"Creator key: {escrow.key}\n\n"
            "Use this key to grant public access to the object from your account. "
            "Keep it somewhere safe — it is the only credential that unlocks public access.\n\n"
            "So the stories don't disappear.\nMizizi Archive"
        ),
    )
    if not sent:
        raise HTTPException(
            status_code=502,
            detail="The key could not be emailed right now. Please check the mail settings and try again.",
        )

    request.status = "sent"
    request.decided_by = admin.id
    from datetime import datetime, timezone

    request.decided_at = datetime.now(timezone.utc)
    escrow.last_issued_at = request.decided_at
    db.commit()
    db.refresh(request)
    return request


def decline_request(db: Session, admin: User, request_id: uuid.UUID) -> CreatorKeyRequest:
    request = db.get(CreatorKeyRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Key request not found.")
    if request.status != "pending":
        raise HTTPException(status_code=409, detail="This request has already been decided.")
    request.status = "declined"
    request.decided_by = admin.id
    from datetime import datetime, timezone

    request.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(request)
    return request
