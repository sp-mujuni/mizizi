"""Media, transcription, translation, permission, consent, provenance,
derivative and relationship sub-resources of a Cultural Object."""

import hashlib
import re
import uuid

from fastapi import APIRouter, Depends, File, Header, HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import access
from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user, get_optional_user_anywhere
from app.core.storage import get_storage
from app.models import (
    Consent,
    CulturalObject,
    CulturalRelationship,
    Derivative,
    Language,
    Permission,
    ProvenanceEvent,
    Transcription,
    Translation,
    User,
)
from app.models.enums import ProvenanceEventType
from app.schemas.cultural_object import (
    ConsentRead,
    DerivativeRead,
    PermissionRead,
    ProvenanceEventRead,
    TranscriptionRead,
    TranslationRead,
)
from app.schemas.mizizi import (
    ConsentCreate,
    CulturalContextUpdate,
    DerivativeCreate,
    MediaUploadResponse,
    PermissionUpdate,
    ProvenanceEventCreate,
    RelationshipCreate,
    RelationshipRead,
    TranscriptionCreate,
    TranscriptionUpdate,
    TranslationCreate,
    TranslationUpdate,
)
from app.services import cultural_object_service, media_service
from app.services.provenance_service import create_provenance_event

router = APIRouter(prefix="/cultural-objects/{object_id}", tags=["Cultural Object resources"])


def _require_object(db: Session, object_id: uuid.UUID):
    return cultural_object_service.get_object_or_404(db, object_id)


def _require_view(user: User | None, obj: CulturalObject) -> None:
    if not access.can_view(user, obj):
        raise HTTPException(status_code=403, detail="This object is not public.")


def _require_manage(user: User | None, obj: CulturalObject) -> None:
    if not access.can_manage(user, obj):
        raise HTTPException(
            status_code=403,
            detail="Only the object's creator (or a reviewer) can do that.",
        )


def _require_creator_key(obj: CulturalObject, creator_key: str | None) -> None:
    if obj.creator_key_hash is None:
        raise HTTPException(
            status_code=403,
            detail="This object has no creator credential on record; its permissions are locked.",
        )
    if not creator_key:
        raise HTTPException(
            status_code=403,
            detail="Granting public access needs the creator key. Send it in the X-Creator-Key header.",
        )
    if hashlib.sha256(creator_key.encode("utf-8")).hexdigest() != obj.creator_key_hash:
        raise HTTPException(status_code=403, detail="Invalid creator key. Permission changes denied.")


def _require_creator(
    obj: CulturalObject, user: User | None, payload: PermissionUpdate, creator_key: str | None
) -> None:
    """Permissions are managed by the creator's account; the community's consent
    to be public (public_access) additionally needs the creator key."""
    changes = payload.model_dump(exclude_unset=True)
    sets_public = changes.get("public_access") is True
    is_creator = user is not None and obj.user_id is not None and obj.user_id == user.id
    if sets_public:
        _require_creator_key(obj, creator_key)
    elif is_creator:
        return
    else:
        _require_creator_key(obj, creator_key)


# --- Media ---------------------------------------------------------------
@router.post("/media", response_model=MediaUploadResponse, status_code=201)
async def upload_media(
    object_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = _require_object(db, object_id)
    _require_manage(user, obj)
    data = await file.read()
    if not data:
        raise HTTPException(status_code=422, detail="Empty file")
    uploaded = media_service.UploadedFile(
        filename=file.filename or "recording.bin",
        content_type=file.content_type or "application/octet-stream",
        data=data,
        size=len(data),
    )
    asset = media_service.attach_media(db, object_id, uploaded, is_original=True)
    return MediaUploadResponse(
        id=asset.id,
        media_type=asset.media_type,
        original_filename=asset.original_filename,
        storage_key=asset.storage_key,
        file_size=asset.file_size,
        sha256_checksum=asset.sha256_checksum,
        is_original=asset.is_original,
        created_at=asset.created_at,
    )


@router.get("/media/{asset_id}")
def get_media(
    object_id: uuid.UUID,
    asset_id: uuid.UUID,
    range_header: str | None = Header(default=None, alias="Range"),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user_anywhere),
):
    """Stream a media asset with HTTP Range support.

    Browsers fetch media through a plain ``<audio>``/``<video>`` URL, so the
    session token is accepted via a ``?token=`` query parameter as well as the
    ``Authorization`` header. Requests for published objects are anonymous;
    requests for objects in the review pipeline require the creator's or a
    reviewer/admin's token.
    """
    obj = _require_object(db, object_id)
    _require_view(user, obj)
    data, mime = media_service.stream_media(object_id, asset_id, db, storage=get_storage())
    content_type = mime or "application/octet-stream"
    cache = (
        "public, max-age=31536000, immutable"
        if obj.status in access.PUBLIC_STATUSES
        else "private, no-store"
    )
    return _media_response(data, content_type, range_header, cache)


_RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


def _media_response(
    data: bytes, content_type: str, range_header: str | None, cache_control: str
) -> Response:
    """Build a media response honouring a single-byte-range request.

    Full responses are ``200 OK``; range requests return ``206 Partial
    Content`` with ``Content-Range`` so the browser can seek; invalid ranges
    return ``416 Range Not Satisfiable``.
    """
    size = len(data)
    headers = {"Accept-Ranges": "bytes", "Cache-Control": cache_control}

    if range_header:
        match = _RANGE_RE.match(range_header.strip())
        if match:
            start_s, end_s = match.groups()
            if start_s == "":
                start = max(0, size - int(end_s or 0))
                end = size - 1
            else:
                start = int(start_s)
                end = int(end_s) if end_s else size - 1
                end = min(end, size - 1)
            if start < 0 or start > end or start >= size:
                return Response(
                    status_code=416,
                    media_type=content_type,
                    headers={"Content-Range": f"bytes */{size}", "Cache-Control": cache_control},
                )
            chunk = data[start : end + 1]
            headers.update(
                {
                    "Content-Range": f"bytes {start}-{end}/{size}",
                    "Content-Length": str(len(chunk)),
                }
            )
            return Response(content=chunk, status_code=206, media_type=content_type, headers=headers)

    headers["Content-Length"] = str(size)
    return Response(content=data, media_type=content_type, headers=headers)


# --- Transcriptions -------------------------------------------------------
@router.get("/transcriptions", response_model=list[TranscriptionRead])
def list_transcriptions(
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    obj = _require_object(db, object_id)
    _require_view(user, obj)
    items = db.execute(
        select(Transcription).where(Transcription.cultural_object_id == object_id)
    ).scalars().all()
    return _hydrate_transcriptions(db, items)


@router.post("/transcriptions", response_model=TranscriptionRead, status_code=201)
def create_transcription(
    object_id: uuid.UUID,
    payload: TranscriptionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = _require_object(db, object_id)
    _require_manage(user, obj)
    transcription = Transcription(
        cultural_object_id=obj.id,
        media_asset_id=payload.media_asset_id,
        language_id=payload.language_id or obj.original_language_id,
        text=payload.text,
        model_name=payload.model_name,
        model_version=payload.model_version,
        confidence=payload.confidence,
        verification_status=payload.verification_status,
        created_by=payload.created_by,
    )
    db.add(transcription)
    db.flush()
    create_provenance_event(
        db,
        obj.id,
        ProvenanceEventType.TRANSCRIPTION_GENERATED,
        actor=payload.created_by or "system",
        description="Transcription created.",
        metadata={"model": payload.model_name},
    )
    db.commit()
    db.refresh(transcription)
    # Keep the object's verification_status in step with its transcriptions.
    cultural_object_service.sync_verification_status(db, obj)
    db.commit()
    return _hydrate_transcriptions(db, [transcription])[0]


@router.patch("/transcriptions/{transcription_id}", response_model=TranscriptionRead)
def update_transcription(
    object_id: uuid.UUID,
    transcription_id: uuid.UUID,
    payload: TranscriptionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = _require_object(db, object_id)
    _require_manage(user, obj)
    transcription = _get_subresource(db, Transcription, object_id, transcription_id)
    if payload.text is not None:
        transcription.text = payload.text
    if payload.verification_status is not None:
        transcription.verification_status = payload.verification_status
    if payload.verification_status == "human_reviewed":
        create_provenance_event(
            db, object_id, ProvenanceEventType.TRANSCRIPTION_REVIEWED, actor=user.email,
            description="Transcription reviewed by a human.",
        )
    db.commit()
    db.refresh(transcription)
    # Keep the object's verification_status in step with its transcriptions.
    cultural_object_service.sync_verification_status(db, obj)
    db.commit()
    return _hydrate_transcriptions(db, [transcription])[0]


def _hydrate_transcriptions(db: Session, items: list[Transcription]) -> list[TranscriptionRead]:
    reads = []
    for t in items:
        lang = db.get(Language, t.language_id) if t.language_id else None
        reads.append(
            TranscriptionRead(
                id=t.id,
                language_id=t.language_id,
                language=(
                    {"id": lang.id, "name": lang.name, "iso_639_3": lang.iso_639_3}
                    if lang else None
                ),
                text=t.text,
                model_name=t.model_name,
                model_version=t.model_version,
                confidence=t.confidence,
                version=t.version,
                verification_status=t.verification_status,
                created_by=t.created_by,
                created_at=t.created_at,
            )
        )
    return reads


# --- Translations ---------------------------------------------------------
@router.get("/translations", response_model=list[TranslationRead])
def list_translations(
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    obj = _require_object(db, object_id)
    _require_view(user, obj)
    items = db.execute(
        select(Translation).where(Translation.cultural_object_id == object_id)
    ).scalars().all()
    return _hydrate_translations(db, items)


@router.post("/translations", response_model=TranslationRead, status_code=201)
def create_translation(
    object_id: uuid.UUID,
    payload: TranslationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = _require_object(db, object_id)
    _require_manage(user, obj)
    translation = Translation(
        cultural_object_id=obj.id,
        source_transcription_id=payload.source_transcription_id,
        source_language_id=payload.source_language_id or obj.original_language_id,
        target_language_id=payload.target_language_id,
        text=payload.text,
        model_name=payload.model_name,
        model_version=payload.model_version,
        verification_status=payload.verification_status,
    )
    db.add(translation)
    db.flush()
    create_provenance_event(
        db, obj.id, ProvenanceEventType.TRANSLATION_GENERATED, actor="system",
        description="Translation created.",
    )
    db.commit()
    db.refresh(translation)
    return _hydrate_translations(db, [translation])[0]


def _hydrate_translations(db: Session, items: list[Translation]) -> list[TranslationRead]:
    reads = []
    for tr in items:
        src = db.get(Language, tr.source_language_id) if tr.source_language_id else None
        tgt = db.get(Language, tr.target_language_id) if tr.target_language_id else None
        reads.append(
            TranslationRead(
                id=tr.id,
                source_transcription_id=tr.source_transcription_id,
                source_language=(
                    {"id": src.id, "name": src.name, "iso_639_3": src.iso_639_3} if src else None
                ),
                target_language=(
                    {"id": tgt.id, "name": tgt.name, "iso_639_3": tgt.iso_639_3} if tgt else None
                ),
                text=tr.text,
                model_name=tr.model_name,
                model_version=tr.model_version,
                verification_status=tr.verification_status,
                created_at=tr.created_at,
            )
        )
    return reads


# --- Permissions ----------------------------------------------------------
@router.get("/permissions", response_model=PermissionRead | None)
def get_permissions(
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    obj = _require_object(db, object_id)
    _require_view(user, obj)
    return db.execute(
        select(Permission).where(Permission.cultural_object_id == object_id)
    ).scalars().first()


@router.put("/permissions", response_model=PermissionRead)
def upsert_permissions(
    object_id: uuid.UUID,
    payload: PermissionUpdate,
    x_creator_key: str | None = Header(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = _require_object(db, object_id)
    _require_creator(obj, user, payload, x_creator_key)
    perm = db.execute(
        select(Permission).where(Permission.cultural_object_id == object_id)
    ).scalars().first()
    if perm is None:
        perm = Permission(cultural_object_id=obj.id)
        db.add(perm)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(perm, field, value)
    create_provenance_event(
        db, obj.id, ProvenanceEventType.PERMISSION_CHANGED, actor=user.email,
        description="Permissions updated by the creator.",
    )
    db.commit()
    db.refresh(perm)
    return perm


# --- Consents -------------------------------------------------------------
@router.get("/consents", response_model=list[ConsentRead])
def list_consents(
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    obj = _require_object(db, object_id)
    _require_view(user, obj)
    return db.execute(
        select(Consent).where(Consent.cultural_object_id == object_id)
    ).scalars().all()


@router.post("/consents", response_model=ConsentRead, status_code=201)
def create_consent(
    object_id: uuid.UUID,
    payload: ConsentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = _require_object(db, object_id)
    _require_manage(user, obj)
    consent = Consent(cultural_object_id=obj.id, **payload.model_dump())
    db.add(consent)
    db.flush()
    create_provenance_event(
        db, obj.id, ProvenanceEventType.CONSENT_RECORDED, actor=payload.consenting_party,
        description=f"Consent recorded: {payload.consent_type.value}.",
        metadata={"consent_type": payload.consent_type.value},
    )
    db.commit()
    db.refresh(consent)
    return consent


# --- Provenance -----------------------------------------------------------
@router.get("/provenance", response_model=list[ProvenanceEventRead])
def list_provenance(
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    obj = _require_object(db, object_id)
    _require_view(user, obj)
    return db.execute(
        select(ProvenanceEvent)
        .where(ProvenanceEvent.cultural_object_id == object_id)
        .order_by(ProvenanceEvent.created_at.asc())
    ).scalars().all()


@router.post("/provenance", response_model=ProvenanceEventRead, status_code=201)
def add_provenance(
    object_id: uuid.UUID,
    payload: ProvenanceEventCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = _require_object(db, object_id)
    _require_manage(user, obj)
    event = create_provenance_event(
        db, obj.id, payload.event_type, actor=payload.actor, description=payload.description,
        metadata=payload.metadata,
    )
    db.commit()
    db.refresh(event)
    return event


# --- Cultural context -----------------------------------------------------
@router.put("/cultural-context", response_model=dict)
def upsert_cultural_context(
    object_id: uuid.UUID,
    payload: CulturalContextUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models import CulturalContext

    obj = _require_object(db, object_id)
    _require_manage(user, obj)
    ctx = db.execute(
        select(CulturalContext).where(CulturalContext.cultural_object_id == object_id)
    ).scalars().first()
    if ctx is None:
        ctx = CulturalContext(cultural_object_id=obj.id)
        db.add(ctx)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(ctx, field, value)
    db.commit()
    db.refresh(ctx)
    return {"id": ctx.id}


# --- Derivatives ----------------------------------------------------------
@router.get("/derivatives", response_model=list[DerivativeRead])
def list_derivatives(
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    obj = _require_object(db, object_id)
    _require_view(user, obj)
    return db.execute(
        select(Derivative).where(Derivative.cultural_object_id == object_id)
    ).scalars().all()


@router.post("/derivatives", response_model=DerivativeRead, status_code=201)
def create_derivative(
    object_id: uuid.UUID,
    payload: DerivativeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Permission-aware derivative generation.

    The API refuses to create a derivative unless the object's permission matrix
    allows derivative work — enforced in code, not by the AI.
    """
    obj = _require_object(db, object_id)
    _require_manage(user, obj)
    perm = db.execute(
        select(Permission).where(Permission.cultural_object_id == object_id)
    ).scalars().first()
    if perm is None or not perm.derivative_work:
        raise HTTPException(
            status_code=403,
            detail="This Cultural Object does not permit derivative generation.",
        )
    derivative = Derivative(cultural_object_id=obj.id, **payload.model_dump())
    db.add(derivative)
    db.flush()
    create_provenance_event(
        db, obj.id, ProvenanceEventType.DERIVATIVE_CREATED, actor="system",
        description=f"Derivative created ({payload.derivative_type.value}).",
        metadata={"model": payload.model_name},
    )
    db.commit()
    db.refresh(derivative)
    return derivative


# --- Relationships --------------------------------------------------------
@router.get("/relationships", response_model=list[RelationshipRead])
def list_relationships(
    object_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    obj = _require_object(db, object_id)
    _require_view(user, obj)
    rows = db.execute(
        select(CulturalRelationship).where(CulturalRelationship.source_object_id == object_id)
    ).scalars().all()
    result = []
    for rel in rows:
        target = cultural_object_service.get_object_or_404(db, rel.target_object_id)
        result.append(
            RelationshipRead(
                id=rel.id,
                source_object_id=rel.source_object_id,
                target_object_id=rel.target_object_id,
                relationship_type=rel.relationship_type,
                description=rel.description,
                created_at=rel.created_at,
                target_object_code=target.object_code,
                target_title=target.title,
            )
        )
    return result


@router.post("/relationships", response_model=RelationshipRead, status_code=201)
def create_relationship(
    object_id: uuid.UUID,
    payload: RelationshipCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    obj = _require_object(db, object_id)
    _require_manage(user, obj)
    cultural_object_service.get_object_or_404(db, payload.target_object_id)
    rel = CulturalRelationship(
        source_object_id=obj.id,
        target_object_id=payload.target_object_id,
        relationship_type=payload.relationship_type.value,
        description=payload.description,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    target = cultural_object_service.get_object_or_404(db, rel.target_object_id)
    return RelationshipRead(
        id=rel.id,
        source_object_id=rel.source_object_id,
        target_object_id=rel.target_object_id,
        relationship_type=rel.relationship_type,
        description=rel.description,
        created_at=rel.created_at,
        target_object_code=target.object_code,
        target_title=target.title,
    )


def _get_subresource(db: Session, model, object_id: uuid.UUID, sub_id: uuid.UUID):
    item = db.execute(
        select(model).where(model.id == sub_id, model.cultural_object_id == object_id)
    ).scalars().first()
    if item is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return item