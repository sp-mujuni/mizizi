"""The Cultural Object — the atomic unit of the Mizizi archive.

A persistent, provenance-aware, rights-aware, multimodal digital representation
of a culturally significant piece of knowledge, expression, practice or memory.

The original media is never overwritten. Everything else is versioned and
derivative. Deletion is restricted — an archive behaves like an archive.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CulturalObject(Base):
    __tablename__ = "cultural_objects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    object_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    object_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    original_language_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("languages.id"), nullable=True
    )
    community_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("communities.id"), nullable=True)
    place_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("places.id"), nullable=True)
    contributor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("contributors.id"), nullable=True
    )
    # The user account that created this object (nullable for legacy/seed objects).
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    visibility: Mapped[str] = mapped_column(String(50), nullable=False, default="restricted")
    verification_status: Mapped[str] = mapped_column(String(50), nullable=False, default="unverified")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # SHA-256 hash of the creator's secret key. Only the creator (who holds the
    # plaintext returned once at creation) can grant permissions such as public
    # access. The plaintext is never persisted.
    creator_key_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    original_language: Mapped["Language"] = relationship(back_populates="cultural_objects")
    community: Mapped["Community"] = relationship(back_populates="cultural_objects")
    place: Mapped["Place"] = relationship(back_populates="cultural_objects")
    contributor: Mapped["Contributor"] = relationship(back_populates="cultural_objects")
    creator_user: Mapped["User | None"] = relationship(back_populates="cultural_objects")

    media_assets: Mapped[list["MediaAsset"]] = relationship(
        back_populates="cultural_object", cascade="all, delete-orphan"
    )
    transcriptions: Mapped[list["Transcription"]] = relationship(
        back_populates="cultural_object", cascade="all, delete-orphan"
    )
    translations: Mapped[list["Translation"]] = relationship(
        back_populates="cultural_object", cascade="all, delete-orphan"
    )
    cultural_context: Mapped["CulturalContext | None"] = relationship(
        back_populates="cultural_object", cascade="all, delete-orphan", uselist=False
    )
    permissions: Mapped[list["Permission"]] = relationship(
        back_populates="cultural_object", cascade="all, delete-orphan"
    )
    consents: Mapped[list["Consent"]] = relationship(
        back_populates="cultural_object", cascade="all, delete-orphan"
    )
    provenance_events: Mapped[list["ProvenanceEvent"]] = relationship(
        back_populates="cultural_object", cascade="all, delete-orphan"
    )
    derivatives: Mapped[list["Derivative"]] = relationship(
        back_populates="cultural_object", cascade="all, delete-orphan"
    )
    collection_items: Mapped[list["CollectionItem"]] = relationship(
        back_populates="cultural_object", cascade="all, delete-orphan"
    )
    tags: Mapped[list["CulturalObjectTag"]] = relationship(
        back_populates="cultural_object", cascade="all, delete-orphan"
    )


from app.models.collection import CollectionItem  # noqa: E402
from app.models.community import Community  # noqa: E402
from app.models.consent import Consent  # noqa: E402
from app.models.contributor import Contributor  # noqa: E402
from app.models.cultural_context import CulturalContext  # noqa: E402
from app.models.derivative import Derivative  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.media_asset import MediaAsset  # noqa: E402
from app.models.permission import Permission  # noqa: E402
from app.models.place import Place  # noqa: E402
from app.models.provenance import ProvenanceEvent  # noqa: E402
from app.models.tag import CulturalObjectTag  # noqa: E402
from app.models.transcription import Transcription  # noqa: E402
from app.models.translation import Translation  # noqa: E402
from app.models.user import User  # noqa: E402