"""Canonical enumerations for the Mizizi Cultural Object model.

These follow the Mizizi Blueprint: object types, lifecycle statuses and
verification levels are first-class, enumerated values — never arbitrary strings.
"""

from enum import Enum


class CulturalObjectType(str, Enum):
    STORY = "story"
    SONG = "song"
    RIDDLE = "riddle"
    PROVERB = "proverb"
    POEM = "poem"
    CHANT = "chant"
    ORAL_HISTORY = "oral_history"
    LULLABY = "lullaby"
    TONGUE_TWISTER = "tongue_twister"
    TRADITION = "tradition"
    CEREMONY = "ceremony"
    GAME = "game"
    RECIPE = "recipe"
    PERSONAL_MEMORY = "personal_memory"
    OTHER = "other"


class ObjectStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    REVIEW = "review"
    VERIFIED = "verified"
    PUBLISHED = "published"
    RESTRICTED = "restricted"
    WITHDRAWN = "withdrawn"
    ARCHIVED = "archived"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    AI_PROCESSED = "ai_processed"
    HUMAN_REVIEWED = "human_reviewed"
    COMMUNITY_VERIFIED = "community_verified"
    EXPERT_VERIFIED = "expert_verified"


class Visibility(str, Enum):
    """The five access levels defined in the blueprint.

    Level 0 Sacred/Restricted  -> "restricted"
    Level 1 Community          -> "community"
    Level 2 Educational        -> "educational"
    Level 3 Public             -> "public"
    Level 4 Commercial         -> "commercial"
    """

    RESTRICTED = "restricted"
    COMMUNITY = "community"
    EDUCATIONAL = "educational"
    PUBLIC = "public"
    COMMERCIAL = "commercial"


class MediaType(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    DOCUMENT = "document"


class ConsentType(str, Enum):
    PRESERVATION = "preservation"
    PUBLIC_ACCESS = "public_access"
    EDUCATIONAL_USE = "educational_use"
    RESEARCH = "research"
    AI_ANALYSIS = "ai_analysis"
    AI_TRAINING = "ai_training"
    DERIVATIVE_WORK = "derivative_work"
    COMMERCIAL_USE = "commercial_use"
    VOICE_CLONING = "voice_cloning"


class ProvenanceEventType(str, Enum):
    OBJECT_CREATED = "object_created"
    MEDIA_UPLOADED = "media_uploaded"
    TRANSCRIPTION_REQUESTED = "transcription_requested"
    TRANSCRIPTION_GENERATED = "transcription_generated"
    TRANSCRIPTION_REVIEWED = "transcription_reviewed"
    TRANSLATION_GENERATED = "translation_generated"
    TRANSLATION_REVIEWED = "translation_reviewed"
    PERMISSION_CHANGED = "permission_changed"
    CONSENT_RECORDED = "consent_recorded"
    COMMUNITY_VERIFIED = "community_verified"
    DERIVATIVE_CREATED = "derivative_created"
    OBJECT_PUBLISHED = "object_published"
    OBJECT_RESTRICTED = "object_restricted"
    OBJECT_WITHDRAWN = "object_withdrawn"
    STATUS_CHANGED = "status_changed"


class DerivativeType(str, Enum):
    AI_ADAPTATION = "ai_adaptation"
    TRANSLATION = "translation"
    SUMMARY = "summary"
    NARRATION = "narration"
    ANIMATION = "animation"
    OTHER = "other"


class RelationshipType(str, Enum):
    RELATED_TO = "related_to"
    VARIANT_OF = "variant_of"
    DERIVED_FROM = "derived_from"
    TRANSLATION_OF = "translation_of"
    PERFORMED_DURING = "performed_during"
    ASSOCIATED_WITH = "associated_with"
    TOLD_BY = "told_by"
    RECORDED_AT = "recorded_at"
    BELONGS_TO = "belongs_to"
    USES_LANGUAGE = "uses_language"
    LOCATED_IN = "located_in"
    ABOUT = "about"
    SIMILAR_TO = "similar_to"
    CONTRASTS_WITH = "contrasts_with"
    REFERENCES = "references"