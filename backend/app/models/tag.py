"""Tags: lightweight structured labels (complement cultural context)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cultural_object_links: Mapped[list["CulturalObjectTag"]] = relationship(
        back_populates="tag", cascade="all, delete-orphan"
    )


class CulturalObjectTag(Base):
    __tablename__ = "cultural_object_tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cultural_object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cultural_objects.id", ondelete="RESTRICT"), nullable=False
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cultural_object: Mapped["CulturalObject"] = relationship(back_populates="tags")
    tag: Mapped["Tag"] = relationship(back_populates="cultural_object_links")


from app.models.cultural_object import CulturalObject  # noqa: E402