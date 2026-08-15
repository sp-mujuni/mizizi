"""Language entity.

Language is a first-class entity (never a free-text column) so the archive can
eventually grow to 100+ African languages with ISO codes and Glottocodes.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    iso_639_3: Mapped[str | None] = mapped_column(String(10), nullable=True)
    glottocode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    alternate_names: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    cultural_objects: Mapped[list["CulturalObject"]] = relationship(back_populates="original_language")
    users: Mapped[list["User"]] = relationship(secondary="user_languages", back_populates="languages")


from app.models.cultural_object import CulturalObject  # noqa: E402
from app.models.user import User  # noqa: E402