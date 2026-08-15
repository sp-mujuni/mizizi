"""Cultural Objects router — the heart of the API."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core import access
from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models import CulturalObject, User
from app.models.enums import CulturalObjectType
from app.schemas.cultural_object import (
    CulturalObjectCreate,
    CulturalObjectCreated,
    CulturalObjectRead,
    CulturalObjectStatusUpdate,
    CulturalObjectSummary,
    CulturalObjectUpdate,
    PaginatedCulturalObjects,
)
from app.services import cultural_object_service

router = APIRouter(prefix="/cultural-objects", tags=["Cultural Objects"])


def _require_view(user: User | None, obj: CulturalObject) -> None:
    if not access.can_view(user, obj):
        raise HTTPException(status_code=403, detail="This object is not public.")


def _require_manage(user: User | None, obj: CulturalObject) -> None:
    if not access.can_manage(user, obj):
        raise HTTPException(
            status_code=403,
            detail="Only the object's creator (or a reviewer) can do that.",
        )


@router.post("", response_model=CulturalObjectCreated, status_code=201)
def create_object(payload: CulturalObjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = cultural_object_service.create_cultural_object(db, payload, user=user)
    return CulturalObjectCreated(
        id=obj.id,
        object_code=obj.object_code,
        status=obj.status,
        visibility=obj.visibility,
        creator_key=obj._creator_key,
    )


@router.get("", response_model=PaginatedCulturalObjects)
def list_objects(
    object_type: CulturalObjectType | None = Query(default=None),
    language: str | None = Query(default=None, description="ISO 639-3 code, e.g. lug"),
    community: str | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    if status is not None and status not in access.visible_statuses(user, status):
        raise HTTPException(
            status_code=403,
            detail="You do not have access to objects in that status.",
        )
    items, total = cultural_object_service.list_cultural_objects(
        db,
        object_type=object_type.value if object_type else None,
        language=language,
        community=community,
        status=status,
        q=q,
        limit=limit,
        offset=offset,
        user=user,
    )
    return PaginatedCulturalObjects(
        items=[CulturalObjectSummary.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{object_id}", response_model=CulturalObjectRead)
def get_object(
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    obj = cultural_object_service.get_object_or_404(db, object_id)
    _require_view(user, obj)
    return obj


@router.patch("/{object_id}", response_model=CulturalObjectRead)
def update_object(
    object_id: uuid.UUID,
    payload: CulturalObjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = cultural_object_service.get_object_or_404(db, object_id)
    _require_manage(user, obj)
    return cultural_object_service.update_cultural_object(db, object_id, payload, actor=user.email, user=user)


@router.patch("/{object_id}/status", response_model=CulturalObjectRead)
def set_status(
    object_id: uuid.UUID,
    payload: CulturalObjectStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = cultural_object_service.get_object_or_404(db, object_id)
    _require_manage(user, obj)
    return cultural_object_service.change_status(db, object_id, payload, actor=user.email)


@router.post("/{object_id}/publish", response_model=CulturalObjectRead)
def publish_object(
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = cultural_object_service.get_object_or_404(db, object_id)
    _require_manage(user, obj)
    cultural_object_service.ensure_can_publish(db, obj)
    return cultural_object_service.change_status(
        db, object_id, CulturalObjectStatusUpdate(status="published"), actor=user.email
    )


@router.get("/{object_id}/publish-check")
def publish_check(
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return the publication checklist with each requirement's status."""
    obj = cultural_object_service.get_object_or_404(db, object_id)
    _require_manage(user, obj)
    return {"object_id": str(obj.id), "requirements": cultural_object_service.publish_requirements(db, obj)}


@router.delete("/{object_id}", response_model=CulturalObjectRead)
def withdraw_object(
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Soft-withdraw: the object is never physically deleted."""
    obj = cultural_object_service.get_object_or_404(db, object_id)
    _require_manage(user, obj)
    return cultural_object_service.withdraw_object(db, object_id, actor=user.email)