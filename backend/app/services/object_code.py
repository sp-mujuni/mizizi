"""Mizizi object-code generation.

Human-readable permanent identifiers:

    MZ-UG-LGD-STORY-00000001
    Mizizi · Uganda · Luganda · Story · #1

Codes are derived from country code + language ISO code + object type + a
sequence. Sequence numbers are allocated transactionally against the archive
table so generation is concurrency-safe (no two objects share a code).
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.cultural_object import CulturalObject

_DEFAULT_COUNTRY = "UG"


def _language_slug(db: Session, language_id: uuid.UUID | None) -> str:
    if language_id is None:
        return "UND"
    from app.models import Language

    lang = db.get(Language, language_id)
    if lang is None:
        return "UND"
    return (lang.iso_639_3 or lang.name)[:3].upper()


def _next_sequence(db: Session, prefix: str) -> int:
    """Next sequence for a given code prefix, computed atomically.

    Uses a row lock on the maximal existing row for the prefix so concurrent
    creations cannot collide.
    """
    # Lock the boundary row so concurrent inserts serialize per prefix.
    boundary = (
        db.execute(
            select(CulturalObject)
            .where(CulturalObject.object_code.like(f"{prefix}-%"))
            .order_by(CulturalObject.object_code.desc())
            .limit(1)
            .with_for_update()
        )
        .scalars()
        .first()
    )
    if boundary is None:
        return 1
    # Parse trailing digits from the most recent code.
    tail = boundary.object_code.rsplit("-", 1)[-1]
    try:
        return int(tail) + 1
    except ValueError:
        # Fallback: count rows (safe only when no concurrent writes are racing).
        return int(db.execute(select(func.count()).select_from(CulturalObject)).scalar() or 0) + 1


def generate_object_code(
    db: Session,
    object_type: str,
    language_id: uuid.UUID | None,
    country: str = _DEFAULT_COUNTRY,
) -> str:
    country_code = country[:2].upper() if country else _DEFAULT_COUNTRY
    lang_slug = _language_slug(db, language_id)
    prefix = f"MZ-{country_code}-{lang_slug}-{object_type.upper()}"
    seq = _next_sequence(db, prefix)
    return f"{prefix}-{seq:08d}"