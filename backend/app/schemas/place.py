"""Pydantic schemas for places."""

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ORMModel


class PlaceBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    country: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=200)
    district: str | None = Field(default=None, max_length=200)
    county: str | None = Field(default=None, max_length=200)
    subcounty: str | None = Field(default=None, max_length=200)
    village: str | None = Field(default=None, max_length=200)
    latitude: float | None = None
    longitude: float | None = None
    historical_names: str | None = None
    description: str | None = None


class PlaceCreate(PlaceBase):
    pass


class PlaceUpdate(PlaceBase):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    country: str | None = None
    region: str | None = None
    district: str | None = None
    county: str | None = None
    subcounty: str | None = None
    village: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    historical_names: str | None = None
    description: str | None = None


class PlaceRead(PlaceBase, ORMModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID