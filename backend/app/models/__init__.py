"""ORM models package.

Importing this package registers every table on the shared Base metadata, which
is required for Alembic autogenerate and for ``Base.metadata.create_all``.
"""

from app.models.collection import Collection, CollectionItem
from app.models.community import Community
from app.models.consent import Consent
from app.models.contributor import Contributor
from app.models.cultural_context import CulturalContext
from app.models.cultural_object import CulturalObject
from app.models.derivative import Derivative
from app.models.enums import (
    ConsentType,
    CulturalObjectType,
    DerivativeType,
    MediaType,
    ObjectStatus,
    ProvenanceEventType,
    RelationshipType,
    VerificationStatus,
    Visibility,
)
from app.models.language import Language
from app.models.media_asset import MediaAsset
from app.models.permission import Permission
from app.models.place import Place
from app.models.provenance import ProvenanceEvent
from app.models.relationship import CulturalRelationship
from app.models.tag import CulturalObjectTag, Tag
from app.models.transcription import Transcription
from app.models.translation import Translation
from app.models.user import (
    ADMIN,
    MEMBER,
    REVIEWER,
    ReviewerApplication,
    Session,
    User,
    UserCommunity,
    UserLanguage,
    UserPlace,
)

__all__ = [
    "ADMIN",
    "Collection",
    "CollectionItem",
    "Community",
    "Consent",
    "ConsentType",
    "Contributor",
    "CulturalContext",
    "CulturalObject",
    "CulturalObjectTag",
    "CulturalObjectType",
    "CulturalRelationship",
    "Derivative",
    "DerivativeType",
    "Language",
    "MEMBER",
    "MediaAsset",
    "MediaType",
    "ObjectStatus",
    "Permission",
    "Place",
    "ProvenanceEvent",
    "ProvenanceEventType",
    "REVIEWER",
    "RelationshipType",
    "ReviewerApplication",
    "Session",
    "Tag",
    "Transcription",
    "Translation",
    "User",
    "UserCommunity",
    "UserLanguage",
    "UserPlace",
    "VerificationStatus",
    "Visibility",
]