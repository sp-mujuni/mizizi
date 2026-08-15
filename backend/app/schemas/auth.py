"""Authentication & authorization schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    display_name: str | None = Field(default=None, max_length=200)
    language_ids: list[uuid.UUID] = []
    place_ids: list[uuid.UUID] = []
    community_ids: list[uuid.UUID] = []


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserProfileBrief(BaseModel):
    id: uuid.UUID
    name: str


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None = None
    role: str
    languages: list[UserProfileBrief] = []
    places: list[UserProfileBrief] = []
    communities: list[UserProfileBrief] = []
    created_at: datetime

    @property
    def is_reviewer(self) -> bool:
        return self.role in {"reviewer", "admin"}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ReviewerApplyRequest(BaseModel):
    statement: str = Field(min_length=10, max_length=2000)


class ReviewerApplicationRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_email: str
    user_display_name: str | None = None
    statement: str
    status: str
    decided_at: datetime | None = None
    created_at: datetime


class ReviewerDecideRequest(BaseModel):
    approve: bool