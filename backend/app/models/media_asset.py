"""Media asset: the file itself is stored in object storage, never in the DB.

Every original is fingerprinted with a SHA-256 checksum so the archival source
can be cryptographically verified at any time.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cultural_object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cultural_objects.id", ondelete="RESTRICT"), nullable=False
    )
    media_type: Mapped[str] = mapped_column(String(30), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int | None] = mapped_column(nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    is_original: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cultural_object: Mapped["CulturalObject"] = relationship(back_populates="media_assets")


from app.models.cultural_object import CulturalObject  # noqa: E402