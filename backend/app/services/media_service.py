"""Media service: upload, fingerprint, store, and attach media to an object.

The original file is stored immutably (SHA-256 checksum recorded) and never
overwritten; the DB holds metadata only.
"""

import hashlib
import os
import uuid
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.storage import StorageBackend, build_object_key, get_storage
from app.models import MediaAsset
from app.models.enums import MediaType, ProvenanceEventType
from app.services.provenance_service import create_provenance_event


@dataclass
class UploadedFile:
    filename: str
    content_type: str
    data: bytes
    size: int


def calculate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def detect_media_type(content_type: str | None, filename: str) -> MediaType:
    ct = (content_type or "").lower()
    name = filename.lower()
    if ct.startswith("audio") or name.endswith((".wav", ".mp3", ".ogg", ".m4a", ".flac", ".aac")):
        return MediaType.AUDIO
    if ct.startswith("video") or name.endswith((".mp4", ".mov", ".webm", ".mkv", ".avi")):
        return MediaType.VIDEO
    if ct.startswith("image") or name.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
        return MediaType.IMAGE
    return MediaType.DOCUMENT


def attach_media(
    db: Session,
    object_id: uuid.UUID,
    file: UploadedFile,
    *,
    is_original: bool = True,
    actor: str = "system",
    storage: StorageBackend | None = None,
) -> MediaAsset:
    from app.services import cultural_object_service

    obj = cultural_object_service.get_object_or_404(db, object_id)
    storage = storage or get_storage()

    media_type = detect_media_type(file.content_type, file.filename)
    checksum = calculate_sha256(file.data)
    kind = "originals" if is_original else "derivatives"
    key = build_object_key(obj.object_code, kind, file.filename)

    storage.put(key, file.data, content_type=file.content_type)

    asset = MediaAsset(
        cultural_object_id=obj.id,
        media_type=media_type.value,
        mime_type=file.content_type,
        original_filename=file.filename,
        storage_provider=storage.__class__.__name__,
        storage_key=key,
        file_size=file.size,
        sha256_checksum=checksum,
        is_original=is_original,
    )
    db.add(asset)
    db.flush()

    create_provenance_event(
        db,
        obj.id,
        ProvenanceEventType.MEDIA_UPLOADED,
        actor=actor,
        description=f"Media uploaded: {file.filename} ({media_type.value}).",
        metadata={"storage_key": key, "sha256": checksum, "is_original": is_original},
    )

    # An uploaded original moves the object into processing.
    if is_original and obj.status == "draft":
        obj.status = "processing"
        obj.version += 1
        create_provenance_event(
            db, obj.id, ProvenanceEventType.STATUS_CHANGED, actor=actor, description="Status → processing."
        )

    db.commit()
    db.refresh(asset)
    return asset


def stream_media(object_id: uuid.UUID, asset_id: uuid.UUID, db: Session, storage: StorageBackend | None = None) -> tuple[bytes, str | None]:
    asset = db.execute(
        select(MediaAsset).where(
            MediaAsset.id == asset_id, MediaAsset.cultural_object_id == object_id
        )
    ).scalars().first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Media asset not found")
    storage = storage or get_storage()
    try:
        data = storage.get(asset.storage_key)
    except Exception as exc:  # StorageError / botocore ClientError
        raise HTTPException(status_code=404, detail="Media bytes not found in storage") from exc
    return data, _playable_mime(asset)


_PLAYABLE_MIME = {
    MediaType.AUDIO: "audio/webm",
    MediaType.VIDEO: "video/webm",
    MediaType.IMAGE: "image/jpeg",
}


def _playable_mime(asset: MediaAsset) -> str | None:
    """Return a content type the browser can render.

    ``mime_type`` is trusted when it is a concrete audio/video/image type.
    Uploads that arrive as ``application/octet-stream`` (e.g. a ``.wav`` or
    ``.mp3``) fall back to a canonical type derived from the detected
    ``media_type`` so the player will accept the stream.
    """
    stored = (asset.mime_type or "").strip().lower()
    if any(stored.startswith(prefix) for prefix in ("audio/", "video/", "image/")):
        return asset.mime_type
    return _PLAYABLE_MIME.get(MediaType(asset.media_type)) if asset.media_type else None


def _safe_sync_file_for_upload(path: str, content_type: str) -> UploadedFile:
    with open(path, "rb") as fh:
        data = fh.read()
    return UploadedFile(filename=os.path.basename(path), content_type=content_type, data=data, size=len(data))