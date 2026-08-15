"""Common schema helpers."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UUIDModel(ORMModel):
    id: uuid.UUID


class TimestampedModel(ORMModel):
    created_at: datetime


class PageMeta(BaseModel):
    total: int
    limit: int
    offset: int


class Page(BaseModel):
    items: list[dict]
    meta: PageMeta