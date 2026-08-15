"""Translation: a derived representation, never a replacement.

Translations are linked to their source transcription and record the generating
model/version, giving research-grade provenance.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Translation(Base):
    __tablename__ = "translations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cultural_object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cultural_objects.id", ondelete="RESTRICT"), nullable=False
    )
    source_transcription_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("transcriptions.id", ondelete="RESTRICT"), nullable=True
    )
    source_language_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("languages.id"), nullable=True)
    target_language_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("languages.id"), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), nullable=False, default="ai_processed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cultural_object: Mapped["CulturalObject"] = relationship(back_populates="translations")
    source_transcription: Mapped["Transcription | None"] = relationship()
    source_language: Mapped["Language | None"] = relationship(foreign_keys=[source_language_id])
    target_language: Mapped["Language | None"] = relationship(foreign_keys=[target_language_id])


from app.models.cultural_object import CulturalObject  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.transcription import Transcription  # noqa: E402