"""Derivative: any AI/derivative work, permanently linked to its source(s).

Derivatives are never confused with traditional material — they carry their
generating model, prompt hash and human-review flag, and a clear derivative type.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Derivative(Base):
    __tablename__ = "derivatives"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cultural_object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cultural_objects.id", ondelete="RESTRICT"), nullable=False
    )
    derivative_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prompt_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    human_reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cultural_object: Mapped["CulturalObject"] = relationship(back_populates="derivatives")


from app.models.cultural_object import CulturalObject  # noqa: E402