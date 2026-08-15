"""Creator-key escrow and key requests.

The creator key is the credential that unlocks ``public_access`` on a Cultural
Object. The plaintext key is returned to the creator exactly once and, in
addition, **escrowed with the Mizizi Administrator** so it can be recovered if
the contributor loses it.

- :class:`CreatorKeyEscrow` — the administrator's copy of the plaintext key.
  Only administrators can read it (via the admin endpoints) or issue it.
- :class:`CreatorKeyRequest` — a contributor's request to have their key emailed
  back to their registered address. An administrator reviews and issues it.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CreatorKeyEscrow(Base):
    """The administrator's stored copy of an object's creator key.

    The plaintext is deliberately held out of the public object representation;
    it is only reachable through the admin-only endpoints.
    """

    __tablename__ = "creator_key_escrows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cultural_object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cultural_objects.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    key: Mapped[str] = mapped_column(Text, nullable=False)
    # last_issued_at records the most recent time the key was emailed out.
    last_issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cultural_object: Mapped["CulturalObject"] = relationship(back_populates="creator_key_escrow")


class CreatorKeyRequest(Base):
    """A contributor asking the administrator to email their creator key back."""

    __tablename__ = "creator_key_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cultural_object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cultural_objects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending|sent|declined
    decided_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="creator_key_requests", foreign_keys="CreatorKeyRequest.user_id")
    cultural_object: Mapped["CulturalObject"] = relationship(back_populates="creator_key_requests")


from app.models.cultural_object import CulturalObject  # noqa: E402
from app.models.user import User  # noqa: E402
