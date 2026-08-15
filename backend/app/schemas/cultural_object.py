"""Pydantic schemas for Cultural Objects.

The read schema is the canonical JSON representation of a Cultural Object —
never a raw ORM dump. This is what the object page, researchers and the API
consume.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CulturalObjectType
from app.schemas.common import ORMModel


class CulturalObjectCreate(BaseModel):
    object_type: CulturalObjectType
    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    original_language_id: uuid.UUID | None = None
    community_id: uuid.UUID | None = None
    place_id: uuid.UUID | None = None
    contributor_id: uuid.UUID | None = None
    visibility: str = "restricted"


class CulturalObjectUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    original_language_id: uuid.UUID | None = None
    community_id: uuid.UUID | None = None
    place_id: uuid.UUID | None = None
    contributor_id: uuid.UUID | None = None
    visibility: str | None = None


class CulturalObjectStatusUpdate(BaseModel):
    status: str


class LanguageBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    iso_639_3: str | None = None


class CommunityBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class PlaceBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    country: str | None = None
    district: str | None = None


class ContributorBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str | None = None
    anonymous: bool = False


class MediaAssetRead(BaseModel):
    id: uuid.UUID
    media_type: str
    mime_type: str | None = None
    original_filename: str | None = None
    storage_key: str
    file_size: int | None = None
    duration_seconds: float | None = None
    sha256_checksum: str
    is_original: bool
    created_at: datetime


class TranscriptionRead(BaseModel):
    id: uuid.UUID
    language_id: uuid.UUID | None = None
    language: LanguageBrief | None = None
    text: str
    model_name: str | None = None
    model_version: str | None = None
    confidence: float | None = None
    version: int
    verification_status: str
    created_by: str | None = None
    created_at: datetime


class TranslationRead(BaseModel):
    id: uuid.UUID
    source_transcription_id: uuid.UUID | None = None
    source_language: LanguageBrief | None = None
    target_language: LanguageBrief | None = None
    text: str
    model_name: str | None = None
    model_version: str | None = None
    verification_status: str
    created_at: datetime


class PermissionRead(BaseModel):
    id: uuid.UUID
    preservation: bool
    public_access: bool
    educational_use: bool
    ai_analysis: bool
    ai_training: bool
    derivative_work: bool
    commercial_use: bool
    voice_cloning: bool
    updated_at: datetime


class ConsentRead(BaseModel):
    id: uuid.UUID
    consenting_party: str
    consent_type: str
    scope: str | None = None
    granted_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    evidence_reference: str | None = None
    created_at: datetime


class ProvenanceEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    actor: str | None = None
    description: str | None = None
    metadata: dict | None = Field(default=None, validation_alias="event_metadata", serialization_alias="metadata")
    created_at: datetime


class DerivativeRead(BaseModel):
    id: uuid.UUID
    derivative_type: str
    title: str | None = None
    content: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    prompt_hash: str | None = None
    human_reviewed: bool
    created_at: datetime


class CulturalContextRead(BaseModel):
    id: uuid.UUID
    genre: str | None = None
    purpose: str | None = None
    audience: str | None = None
    occasion: str | None = None
    themes: str | None = None
    moral_or_lesson: str | None = None
    historical_period: str | None = None
    cultural_significance: str | None = None
    performance_context: str | None = None
    collector_notes: str | None = None
    community_notes: str | None = None
    researcher_notes: str | None = None


class TagRead(BaseModel):
    id: uuid.UUID
    name: str


class CulturalObjectRead(BaseModel):
    """The canonical representation of a Mizizi Cultural Object."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    object_code: str
    object_type: str
    title: str | None = None
    description: str | None = None
    status: str
    visibility: str
    verification_status: str
    version: int
    created_at: datetime
    updated_at: datetime

    original_language: LanguageBrief | None = None
    community: CommunityBrief | None = None
    place: PlaceBrief | None = None
    contributor: ContributorBrief | None = None

    media_assets: list[MediaAssetRead] = []
    transcriptions: list[TranscriptionRead] = []
    translations: list[TranslationRead] = []
    cultural_context: CulturalContextRead | None = None
    permissions: list[PermissionRead] = []
    consents: list[ConsentRead] = []
    provenance_events: list[ProvenanceEventRead] = []
    derivatives: list[DerivativeRead] = []
    tags: list[TagRead] = []


class CulturalObjectSummary(BaseModel):
    """Lightweight card for archive listings."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    object_code: str
    object_type: str
    title: str | None = None
    status: str
    visibility: str
    verification_status: str
    created_at: datetime
    original_language: LanguageBrief | None = None
    community: CommunityBrief | None = None
    place: PlaceBrief | None = None


class CulturalObjectCreated(BaseModel):
    id: uuid.UUID
    object_code: str
    status: str
    visibility: str
    creator_key: str


class PaginatedCulturalObjects(BaseModel):
    items: list[CulturalObjectSummary]
    total: int
    limit: int
    offset: int