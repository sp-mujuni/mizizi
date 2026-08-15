"""Pydantic schemas for languages."""

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ORMModel


class LanguageBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    iso_639_3: str | None = Field(default=None, max_length=10)
    glottocode: str | None = Field(default=None, max_length=20)
    alternate_names: str | None = None
    description: str | None = None


class LanguageCreate(LanguageBase):
    pass


class LanguageUpdate(LanguageBase):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    iso_639_3: str | None = None
    glottocode: str | None = None
    alternate_names: str | None = None
    description: str | None = None


class LanguageRead(LanguageBase, ORMModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID