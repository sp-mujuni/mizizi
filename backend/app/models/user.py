"""User accounts — the people who record, review and manage cultural material."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# Roles, in ascending privilege.
MEMBER = "member"
REVIEWER = "reviewer"
ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default=MEMBER)
    # Cultural background chosen at registration — record/review surfaces are
    # filtered to these.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    languages: Mapped[list["Language"]] = relationship(
        secondary="user_languages", back_populates="users", lazy="selectin"
    )
    places: Mapped[list["Place"]] = relationship(
        secondary="user_places", back_populates="users", lazy="selectin"
    )
    communities: Mapped[list["Community"]] = relationship(
        secondary="user_communities", back_populates="users", lazy="selectin"
    )
    cultural_objects: Mapped[list["CulturalObject"]] = relationship(back_populates="creator_user")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reviewer_applications: Mapped[list["ReviewerApplication"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="ReviewerApplication.user_id",
    )
    creator_key_requests: Mapped[list["CreatorKeyRequest"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="CreatorKeyRequest.user_id",
    )


class UserLanguage(Base):
    __tablename__ = "user_languages"
    __table_args__ = (UniqueConstraint("user_id", "language_id", name="uq_user_language"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    language_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("languages.id"), nullable=False)


class UserPlace(Base):
    __tablename__ = "user_places"
    __table_args__ = (UniqueConstraint("user_id", "place_id", name="uq_user_place"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    place_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("places.id"), nullable=False)


class UserCommunity(Base):
    __tablename__ = "user_communities"
    __table_args__ = (UniqueConstraint("user_id", "community_id", name="uq_user_community"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    community_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("communities.id"), nullable=False)


class Session(Base):
    """Opaque login session. The plaintext token is handed to the client once;
    only its hash is stored, and sessions expire and can be revoked."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="sessions")


class ReviewerApplication(Base):
    """A member's request to become a reviewer, awaiting (or decided by) an admin."""

    __tablename__ = "reviewer_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    decided_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="reviewer_applications", foreign_keys="ReviewerApplication.user_id")


from app.models.community import Community  # noqa: E402
from app.models.cultural_object import CulturalObject  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.place import Place  # noqa: E402
from app.models.creator_key import CreatorKeyRequest  # noqa: E402