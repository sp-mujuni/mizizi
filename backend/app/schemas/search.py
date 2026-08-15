"""Pydantic schemas for search."""

from pydantic import BaseModel, Field

from app.schemas.cultural_object import CulturalObjectSummary


class SearchResponse(BaseModel):
    query: str
    mode: str
    results: list[CulturalObjectSummary]
    total: int