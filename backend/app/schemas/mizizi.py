"""Pydantic schemas for media assets, transcriptions, translations, permissions,
consents, provenance, derivatives and relationships."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ConsentType, DerivativeType, MediaType, RelationshipType
from app.schemas.common import ORMModel


# --- Media ---
class MediaUploadResponse(BaseModel):
    id: uuid.UUID
    media_type: str
    original_filename: str | None = None
    storage_key: str
    file_size: int | None = None
    sha256_checksum: str
    is_original: bool
    created_at: datetime


# --- Transcriptions ---
class TranscriptionCreate(BaseModel):
    media_asset_id: uuid.UUID | None = None
    language_id: uuid.UUID | None = None
    text: str = Field(min_length=1)
    model_name: str | None = None
    model_version: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    verification_status: str = "ai_processed"
    created_by: str | None = None


class TranscriptionUpdate(BaseModel):
    text: str | None = None
    verification_status: str | None = None


# --- Translations ---
class TranslationCreate(BaseModel):
    source_transcription_id: uuid.UUID | None = None
    source_language_id: uuid.UUID | None = None
    target_language_id: uuid.UUID | None = None
    text: str = Field(min_length=1)
    model_name: str | None = None
    model_version: str | None = None
    verification_status: str = "ai_processed"


class TranslationUpdate(BaseModel):
    text: str | None = None
    verification_status: str | None = None


# --- Permissions ---
class PermissionUpdate(BaseModel):
    preservation: bool | None = None
    public_access: bool | None = None
    educational_use: bool | None = None
    ai_analysis: bool | None = None
    ai_training: bool | None = None
    derivative_work: bool | None = None
    commercial_use: bool | None = None
    voice_cloning: bool | None = None


# --- Consents ---
class ConsentCreate(BaseModel):
    consenting_party: str = Field(min_length=1, max_length=255)
    consent_type: ConsentType
    scope: str | None = None
    granted_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    evidence_reference: str | None = None
    notes: str | None = None


# --- Cultural context ---
class CulturalContextUpdate(BaseModel):
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


# --- Provenance ---
class ProvenanceEventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=100)
    actor: str | None = None
    description: str | None = None
    metadata: dict | None = None


# --- Derivatives ---
class DerivativeCreate(BaseModel):
    derivative_type: DerivativeType = DerivativeType.AI_ADAPTATION
    title: str | None = None
    content: str | None = Field(default=None, min_length=1)
    model_name: str | None = None
    model_version: str | None = None
    prompt_hash: str | None = None
    human_reviewed: bool = False


# --- Relationships ---
class RelationshipCreate(BaseModel):
    target_object_id: uuid.UUID
    relationship_type: RelationshipType
    description: str | None = None


class RelationshipRead(BaseModel):
    id: uuid.UUID
    source_object_id: uuid.UUID
    target_object_id: uuid.UUID
    relationship_type: str
    description: str | None = None
    created_at: datetime
    target_object_code: str | None = None
    target_title: str | None = None