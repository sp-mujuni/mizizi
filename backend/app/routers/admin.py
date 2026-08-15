"""Admin console — moderation of users, objects and escrowed creator keys.

Everything under ``/admin`` requires the ``admin`` role. It is the surface
where the Mizizi Administrator can:

* view every user account and the objects they hold,
* permanently delete an object that violates archive policy,
* review the escrowed creator keys, and
* email a creator key back to its owner on request.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models import User
from app.schemas.admin import (
    AdminObjectBrief,
    AdminObjectList,
    AdminObjectRead,
    AdminUserList,
    AdminUserRead,
    CreatorKeyRead,
    CreatorKeyRequestRead,
    DeleteResponse,
)
from app.services import creator_key_service, cultural_object_service

router = APIRouter(prefix="/admin", tags=["Admin"])


def _brief(obj) -> AdminObjectBrief:
    return AdminObjectBrief.model_validate(obj)


def _user_read(user: User) -> AdminUserRead:
    objects = sorted(user.cultural_objects, key=lambda o: o.created_at, reverse=True)
    return AdminUserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        created_at=user.created_at,
        object_count=len(objects),
        objects=[_brief(o) for o in objects],
    )


def _object_read(obj) -> AdminObjectRead:
    creator = obj.creator_user
    return AdminObjectRead(
        id=obj.id,
        object_code=obj.object_code,
        object_type=obj.object_type,
        title=obj.title,
        status=obj.status,
        visibility=obj.visibility,
        verification_status=obj.verification_status,
        created_at=obj.created_at,
        user_id=obj.user_id,
        user_email=creator.email if creator else None,
        user_display_name=creator.display_name if creator else None,
    )


def _request_read(db: Session, req) -> CreatorKeyRequestRead:
    obj = cultural_object_service.get_object_or_404(db, req.cultural_object_id)
    user = db.get(User, req.user_id)
    return CreatorKeyRequestRead(
        id=req.id,
        user_id=req.user_id,
        user_email=user.email if user else "unknown",
        cultural_object_id=req.cultural_object_id,
        object_code=obj.object_code,
        object_title=obj.title,
        status=req.status,
        decided_at=req.decided_at,
        created_at=req.created_at,
    )


def _escrow_read(db: Session, escrow) -> CreatorKeyRead:
    obj = escrow.cultural_object
    user_email = None
    if escrow.user_id is not None:
        user = db.get(User, escrow.user_id)
        user_email = user.email if user else None
    return CreatorKeyRead(
        id=escrow.id,
        cultural_object_id=escrow.cultural_object_id,
        object_code=obj.object_code,
        object_title=obj.title,
        user_id=escrow.user_id,
        user_email=user_email,
        key=escrow.key,
        last_issued_at=escrow.last_issued_at,
        created_at=escrow.created_at,
    )


@router.get("/users", response_model=AdminUserList)
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    users, total = cultural_object_service.list_all_users_with_objects(db)
    return AdminUserList(items=[_user_read(u) for u in users], total=total)


@router.get("/objects", response_model=AdminObjectList)
def list_objects(
    q: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    items, total = cultural_object_service.list_all_objects(
        db, q=q, status=status, limit=limit, offset=offset
    )
    return AdminObjectList(items=[_object_read(o) for o in items], total=total)


@router.delete("/objects/{object_id}", response_model=DeleteResponse)
def delete_object(
    object_id: uuid.UUID,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Permanently remove an object that violates archive policy."""
    cultural_object_service.delete_object(db, object_id, actor=user.email, user=user)
    return DeleteResponse(
        ok=True,
        detail="Object permanently removed from the archive.",
        object_id=object_id,
    )


@router.get("/creator-keys", response_model=list[CreatorKeyRead])
def list_creator_keys(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """The administrator's ledger of escrowed creator keys."""
    return [_escrow_read(db, e) for e in cultural_object_service.list_creator_key_escrows(db)]


@router.get("/creator-key-requests", response_model=list[CreatorKeyRequestRead])
def list_key_requests(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [_request_read(db, r) for r in creator_key_service.list_pending_requests(db)]


@router.post("/creator-key-requests/{request_id}/issue", response_model=CreatorKeyRequestRead)
def issue_key(
    request_id: uuid.UUID,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Email the escrowed creator key to the requesting contributor."""
    req = creator_key_service.issue_key(db, user, request_id)
    return _request_read(db, req)


@router.post("/creator-key-requests/{request_id}/decline", response_model=CreatorKeyRequestRead)
def decline_key(
    request_id: uuid.UUID,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    req = creator_key_service.decline_request(db, user, request_id)
    return _request_read(db, req)
