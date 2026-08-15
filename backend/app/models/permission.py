"""Permissions: the machine-readable rights matrix for a cultural object.

Every permission is a first-class, enforced column — never a free-text policy.
The API refuses derivative/AI actions when the corresponding permission is not
granted.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cultural_object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cultural_objects.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    preservation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    public_access: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    educational_use: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_analysis: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_training: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    derivative_work: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    commercial_use: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    voice_cloning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    cultural_object: Mapped["CulturalObject"] = relationship(back_populates="permissions")


from app.models.cultural_object import CulturalObject  # noqa: E402