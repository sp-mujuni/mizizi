"""Cultural Object service — the core business logic of the archive.

Implements the object lifecycle (draft → processing → review → verified →
published → restricted/withdrawn/archived) with provenance recorded at every
step. The original is never overwritten; deletions are soft (withdraw).
"""

import hashlib
import secrets
import uuid

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core import access
from app.models import Community, CulturalObject, Language, Place, Contributor, Permission, ProvenanceEvent, User
from app.models.enums import ObjectStatus, ProvenanceEventType
from app.schemas.cultural_object import (
    CulturalObjectCreate,
    CulturalObjectStatusUpdate,
    CulturalObjectUpdate,
)
from app.services import object_code
from app.services.provenance_service import create_provenance_event


def _load_options():
    return (
        joinedload(CulturalObject.original_language),
        joinedload(CulturalObject.community),
        joinedload(CulturalObject.place),
        joinedload(CulturalObject.contributor),
        joinedload(CulturalObject.media_assets),
        joinedload(CulturalObject.transcriptions),
        joinedload(CulturalObject.translations),
        joinedload(CulturalObject.cultural_context),
        joinedload(CulturalObject.permissions),
        joinedload(CulturalObject.consents),
        joinedload(CulturalObject.provenance_events),
        joinedload(CulturalObject.derivatives),
        joinedload(CulturalObject.tags),
    )


def _validate_background(db: Session, payload: CulturalObjectCreate, user: User | None) -> None:
    """Registration captured the user's cultural background. Objects they record
    may only reference languages, places and communities they chose."""
    if user is None:
        return
    lang_ids = {l.id for l in user.languages}
    place_ids = {p.id for p in user.places}
    community_ids = {c.id for c in user.communities}
    if payload.original_language_id is not None and payload.original_language_id not in lang_ids:
        raise HTTPException(
            status_code=422,
            detail="That language is not in your cultural background. You can only record in the languages you chose at registration.",
        )
    if payload.place_id is not None and payload.place_id not in place_ids:
        raise HTTPException(
            status_code=422,
            detail="That place is not in your cultural background. You can only use places you chose at registration.",
        )
    if payload.community_id is not None and payload.community_id not in community_ids:
        raise HTTPException(
            status_code=422,
            detail="That community is not in your cultural background. You can only use communities you chose at registration.",
        )


def get_object_or_404(db: Session, object_id: uuid.UUID) -> CulturalObject:
    obj = (
        db.execute(
            select(CulturalObject)
            .options(*_load_options())
            .where(CulturalObject.id == object_id)
        )
        .scalars()
        .first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Cultural Object not found")
    return obj


def create_cultural_object(
    db: Session, payload: CulturalObjectCreate, user: User | None = None
) -> CulturalObject:
    _validate_background(db, payload, user)
    code = object_code.generate_object_code(
        db,
        object_type=payload.object_type.value,
        language_id=payload.original_language_id,
    )
    # A fresh creator credential for this object. The plaintext key is returned
    # to the creator exactly once; only its hash is stored.
    creator_key = secrets.token_urlsafe(24)
    obj = CulturalObject(
        object_code=code,
        object_type=payload.object_type.value,
        title=payload.title,
        description=payload.description,
        original_language_id=payload.original_language_id,
        community_id=payload.community_id,
        place_id=payload.place_id,
        contributor_id=payload.contributor_id,
        user_id=user.id if user else None,
        status=ObjectStatus.DRAFT.value,
        visibility=payload.visibility or "restricted",
        verification_status="unverified",
        creator_key_hash=hashlib.sha256(creator_key.encode("utf-8")).hexdigest(),
    )
    obj._creator_key = creator_key
    db.add(obj)
    db.flush()

    # Default permissions: preservation only, everything else requires consent.
    db.add(Permission(cultural_object_id=obj.id, preservation=True))
    create_provenance_event(
        db,
        obj.id,
        ProvenanceEventType.OBJECT_CREATED,
        actor="system",
        description=f"Cultural Object created ({code}).",
        metadata={"object_type": payload.object_type.value},
    )
    db.commit()
    db.refresh(obj)
    return obj


def list_cultural_objects(
    db: Session,
    *,
    object_type: str | None = None,
    language: str | None = None,
    community: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    user: User | None = None,
) -> tuple[list[CulturalObject], int]:
    query = select(CulturalObject).options(
        joinedload(CulturalObject.original_language),
        joinedload(CulturalObject.community),
        joinedload(CulturalObject.place),
    )
    count_query = select(func.count()).select_from(CulturalObject)

    # Visibility scope: the public archive is published-only for everyone.
    # A creator's other objects never surface here — they are managed from the
    # personal account (/auth/me/objects). Reviewers opt into the pipeline via
    # an explicit status filter.
    scope = CulturalObject.status.in_(access.visible_statuses(user, status))
    query = query.where(scope)
    count_query = count_query.where(scope)

    if object_type:
        query = query.where(CulturalObject.object_type == object_type)
        count_query = count_query.where(CulturalObject.object_type == object_type)
    if status:
        query = query.where(CulturalObject.status == status)
        count_query = count_query.where(CulturalObject.status == status)
    if q:
        like = f"%{q}%"
        query = query.where(
            or_(
                CulturalObject.title.ilike(like),
                CulturalObject.description.ilike(like),
                CulturalObject.object_code.ilike(like),
            )
        )
        count_query = count_query.where(
            or_(
                CulturalObject.title.ilike(like),
                CulturalObject.description.ilike(like),
                CulturalObject.object_code.ilike(like),
            )
        )

    if language:
        lang = db.execute(select(Language).where(Language.iso_639_3 == language)).scalars().first()
        if lang is not None:
            query = query.where(CulturalObject.original_language_id == lang.id)
            count_query = count_query.where(CulturalObject.original_language_id == lang.id)

    if community:
        comm = db.execute(select(Community).where(Community.name == community)).scalars().first()
        if comm is not None:
            query = query.where(CulturalObject.community_id == comm.id)
            count_query = count_query.where(CulturalObject.community_id == comm.id)

    total = db.execute(count_query).scalar() or 0
    items = (
        db.execute(query.order_by(CulturalObject.created_at.desc()).limit(limit).offset(offset))
        .scalars()
        .all()
    )
    return list(items), total


def update_cultural_object(
    db: Session,
    object_id: uuid.UUID,
    payload: CulturalObjectUpdate,
    actor: str = "system",
    user: User | None = None,
) -> CulturalObject:
    obj = get_object_or_404(db, object_id)
    _validate_background(db, payload, user)
    changed = False
    for field in ("title", "description", "original_language_id", "community_id", "place_id", "contributor_id", "visibility"):
        value = getattr(payload, field, None)
        if field == "visibility" and value is None:
            continue
        if value is not None and getattr(obj, field) != value:
            setattr(obj, field, value)
            changed = True
    if changed:
        obj.version += 1
        create_provenance_event(
            db, obj.id, ProvenanceEventType.STATUS_CHANGED, actor=actor, description="Object metadata updated."
        )
        db.commit()
        db.refresh(obj)
    return get_object_or_404(db, object_id)


def change_status(
    db: Session, object_id: uuid.UUID, payload: CulturalObjectStatusUpdate, actor: str = "system"
) -> CulturalObject:
    obj = get_object_or_404(db, object_id)
    new_status = payload.status
    valid = {s.value for s in ObjectStatus}
    if new_status not in valid:
        raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of: {sorted(valid)}")

    old_status = obj.status
    if new_status == old_status:
        return obj

    if new_status == ObjectStatus.PUBLISHED.value:
        # Publishing is the one transition the review pipeline must earn.
        ensure_can_publish(db, obj)

    obj.status = new_status
    obj.version += 1

    event_map = {
        ObjectStatus.PUBLISHED.value: ProvenanceEventType.OBJECT_PUBLISHED,
        ObjectStatus.RESTRICTED.value: ProvenanceEventType.OBJECT_RESTRICTED,
        ObjectStatus.WITHDRAWN.value: ProvenanceEventType.OBJECT_WITHDRAWN,
    }
    event_type = event_map.get(new_status, ProvenanceEventType.STATUS_CHANGED)
    create_provenance_event(
        db,
        obj.id,
        event_type,
        actor=actor,
        description=f"Status changed: {old_status} → {new_status}.",
        metadata={"from": old_status, "to": new_status},
    )
    db.commit()
    db.refresh(obj)
    return obj


def withdraw_object(db: Session, object_id: uuid.UUID, actor: str = "system") -> CulturalObject:
    """Soft delete — the object is withdrawn and restricted, never destroyed."""
    return change_status(db, object_id, CulturalObjectStatusUpdate(status=ObjectStatus.WITHDRAWN.value), actor=actor)


HUMAN_VERIFIED_STATUSES = {
    "human_reviewed",
    "community_verified",
    "expert_verified",
}


def publish_requirements(db: Session, obj: CulturalObject) -> list[dict]:
    """The publication checklist — the conditions an object must meet before
    it can appear in the public archive.

    Each entry is {"requirement": key, "label": human-readable, "satisfied": bool}.
    """

    def _human_verified() -> bool:
        if obj.verification_status in HUMAN_VERIFIED_STATUSES:
            return True
        return any(
            t.verification_status in HUMAN_VERIFIED_STATUSES for t in obj.transcriptions
        )

    def _has_content() -> bool:
        has_original_media = any(a.is_original for a in obj.media_assets)
        has_verified_transcript = any(
            t.verification_status in HUMAN_VERIFIED_STATUSES for t in obj.transcriptions
        )
        return has_original_media or has_verified_transcript

    def _public_access() -> bool:
        return any(p.public_access for p in obj.permissions)

    def _consented() -> bool:
        return len(obj.consents) > 0

    return [
        {
            "requirement": "status_verified",
            "label": "Object status must be 'verified' (the review pipeline is complete).",
            "satisfied": obj.status == ObjectStatus.VERIFIED.value,
        },
        {
            "requirement": "human_verification",
            "label": "A human (or community/expert) must have verified the content — the object or its transcript must be at least 'human_reviewed'.",
            "satisfied": _human_verified(),
        },
        {
            "requirement": "original_content",
            "label": "At least one original media asset or a human-verified transcript must exist.",
            "satisfied": _has_content(),
        },
        {
            "requirement": "public_access",
            "label": "The community must have granted 'public access' permission.",
            "satisfied": _public_access(),
        },
        {
            "requirement": "consent_recorded",
            "label": "At least one recorded consent must be on file.",
            "satisfied": _consented(),
        },
        {
            "requirement": "language_identified",
            "label": "The original language must be identified.",
            "satisfied": obj.original_language_id is not None,
        },
    ]


def ensure_can_publish(db: Session, obj: CulturalObject) -> None:
    """Raises 409 listing every unmet requirement if the object cannot be published."""
    unmet = [r["label"] for r in publish_requirements(db, obj) if not r["satisfied"]]
    if unmet:
        raise HTTPException(
            status_code=409,
            detail="Cannot publish — requirements not met:\n- " + "\n- ".join(unmet),
        )