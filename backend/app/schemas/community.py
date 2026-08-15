"""Pydantic schemas for communities."""

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ORMModel


class CommunityBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    country: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=200)
    preferred_names: str | None = None
    description: str | None = None
    cultural_notes: str | None = None


class CommunityCreate(CommunityBase):
    pass


class CommunityUpdate(CommunityBase):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    country: str | None = None
    region: str | None = None
    preferred_names: str | None = None
    description: str | None = None
    cultural_notes: str | None = None


class CommunityRead(CommunityBase, ORMModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID