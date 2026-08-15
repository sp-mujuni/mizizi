"""Provenance: every important action records an append-only event."""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models import ProvenanceEvent
from app.models.enums import ProvenanceEventType


def create_provenance_event(
    db: Session,
    cultural_object_id: uuid.UUID,
    event_type: str | ProvenanceEventType,
    actor: str | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ProvenanceEvent:
    event = ProvenanceEvent(
        cultural_object_id=cultural_object_id,
        event_type=event_type.value if isinstance(event_type, ProvenanceEventType) else event_type,
        actor=actor,
        description=description,
        event_metadata=metadata,
    )
    db.add(event)
    return event


def list_provenance(db: Session, cultural_object_id: uuid.UUID) -> list[ProvenanceEvent]:
    return (
        db.query(ProvenanceEvent)
        .filter(ProvenanceEvent.cultural_object_id == cultural_object_id)
        .order_by(ProvenanceEvent.created_at.asc())
        .all()
    )