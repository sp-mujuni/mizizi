"""Pydantic schemas for contributors."""

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ORMModel


class ContributorBase(BaseModel):
    display_name: str | None = Field(default=None, max_length=255)
    anonymous: bool = False
    role: str | None = Field(default=None, max_length=100)
    contact_email: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class ContributorCreate(ContributorBase):
    pass


class ContributorUpdate(ContributorBase):
    display_name: str | None = None
    anonymous: bool | None = None
    role: str | None = None
    contact_email: str | None = None
    notes: str | None = None


class ContributorRead(ContributorBase, ORMModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID