"""Cultural context: rich narrative context that complements, not replaces, tags."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CulturalContext(Base):
    __tablename__ = "cultural_contexts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cultural_object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cultural_objects.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    genre: Mapped[str | None] = mapped_column(String(150), nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    audience: Mapped[str | None] = mapped_column(Text, nullable=True)
    occasion: Mapped[str | None] = mapped_column(Text, nullable=True)
    themes: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-separated, or JSON via UI
    moral_or_lesson: Mapped[str | None] = mapped_column(Text, nullable=True)
    historical_period: Mapped[str | None] = mapped_column(Text, nullable=True)
    cultural_significance: Mapped[str | None] = mapped_column(Text, nullable=True)
    performance_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    collector_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    community_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    researcher_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    cultural_object: Mapped["CulturalObject"] = relationship(back_populates="cultural_context")


from app.models.cultural_object import CulturalObject  # noqa: E402