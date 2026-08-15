"""Admin and creator-key schemas.

The admin surface exposes moderation data that never appears on the public API:
every user account, every object across all users, the escrowed creator keys,
and the pending key-issue requests.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AdminObjectBrief(BaseModel):
    """A Cultural Object as seen in an admin's user/object listing."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    object_code: str
    object_type: str
    title: str | None = None
    status: str
    visibility: str
    verification_status: str
    created_at: datetime


class AdminUserRead(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None = None
    role: str
    created_at: datetime
    object_count: int
    objects: list[AdminObjectBrief] = []


class AdminObjectRead(AdminObjectBrief):
    """An object with its owning account attached, for moderation."""

    user_id: uuid.UUID | None = None
    user_email: str | None = None
    user_display_name: str | None = None


class AdminObjectList(BaseModel):
    items: list[AdminObjectRead]
    total: int


class AdminUserList(BaseModel):
    items: list[AdminUserRead]
    total: int


class CreatorKeyRead(BaseModel):
    """The administrator's escrowed copy of a creator key."""

    id: uuid.UUID
    cultural_object_id: uuid.UUID
    object_code: str
    object_title: str | None = None
    user_id: uuid.UUID | None = None
    user_email: str | None = None
    key: str
    last_issued_at: datetime | None = None
    created_at: datetime


class CreatorKeyRequestCreate(BaseModel):
    object_id: uuid.UUID


class CreatorKeyRequestRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_email: str
    cultural_object_id: uuid.UUID
    object_code: str
    object_title: str | None = None
    status: str
    decided_at: datetime | None = None
    created_at: datetime


class DeleteResponse(BaseModel):
    ok: bool = True
    detail: str = Field(default="")
    object_id: uuid.UUID | None = None
