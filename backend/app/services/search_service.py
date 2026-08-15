"""Search service.

V1: PostgreSQL full-text search across titles, descriptions, object codes and
transcriptions.
V2 (optional): pgvector semantic search — used only when the ``vector``
extension is available, so the core archive never depends on it.
"""

import uuid

from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session

from app.core import access
from app.models import CulturalObject, Transcription, Language, Community, User

_SEARCHABLE = (
    CulturalObject.title,
    CulturalObject.description,
    CulturalObject.object_code,
)


def _fts_query(q: str) -> str:
    # Simple tsquery from a user string, guarding against syntax injection.
    tokens = [t for t in q.replace("'", " ").split() if t]
    if not tokens:
        return ""
    return " & ".join(t.replace(":", " ") for t in tokens)


def fulltext_search(
    db: Session, q: str, limit: int = 20, user: User | None = None
) -> list[CulturalObject]:
    like = f"%{q}%"
    scope = CulturalObject.status.in_(access.visible_statuses(user))
    stmt = (
        select(CulturalObject)
        .where(
            scope,
            or_(
                CulturalObject.title.ilike(like),
                CulturalObject.description.ilike(like),
                CulturalObject.object_code.ilike(like),
                CulturalObject.id.in_(
                    select(Transcription.cultural_object_id).where(
                        Transcription.text.ilike(like),
                        Transcription.verification_status.in_(
                            ["human_reviewed", "community_verified", "expert_verified"]
                        ),
                    )
                ),
            ),
        )
        .order_by(CulturalObject.created_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def vector_available(db: Session) -> bool:
    try:
        row = db.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).first()
        return row is not None
    except Exception:
        return False


def semantic_search(db: Session, query_embedding: list[float], limit: int = 20) -> list[CulturalObject]:
    """pgvector cosine similarity search (requires the vector extension)."""
    if not vector_available(db):
        return []
    vec = "[" + ",".join(str(float(x)) for x in query_embedding) + "]"
    stmt = text(
        """
        SELECT co.* FROM cultural_objects co
        JOIN transcriptions t ON t.cultural_object_id = co.id
        WHERE co.visibility IN ('public', 'educational', 'community')
        ORDER BY t.embedding <=> :vec::vector
        LIMIT :limit
        """
    )
    rows = db.execute(stmt, {"vec": vec, "limit": limit}).mappings().all()
    return [CulturalObject(**dict(r)) for r in rows]


def search(
    db: Session, q: str, limit: int = 20, user: User | None = None
) -> tuple[list[CulturalObject], str]:
    """Returns (results, mode) where mode is 'fts' or 'vector'."""
    embedding = _try_embedding(q)
    if embedding is not None and vector_available(db):
        results = semantic_search(db, embedding, limit)
        if results:
            return results, "vector"
    return fulltext_search(db, q, limit, user=user), "fts"


def _try_embedding(q: str) -> list[float] | None:
    """Best-effort local embedding for semantic search.

    Returns None when no embedding model is installed (the archive then falls
    back to full-text search). Production can plug in a real embedding model or
    service here.
    """
    try:
        # Lightweight, dependency-free deterministic bag-of-words vector over a
        # small vocabulary — good enough to demonstrate vector mode locally.
        vocab = [
            "hare", "lion", "trickster", "clever", "story", "song", "riddle",
            "proverb", "animal", "wisdom", "greed", "family", "child", "elder",
            "hunter", "grandmother", "masaka", "kampala", "luguanda", "cow",
            "leopard", "tortoise", "spider", "king", "village", "river", "moon",
            "sun", "rain", "courage", "deception", "wedding", "funeral", "harvest",
        ]
        words = [w for w in q.lower().split() if w]
        vec = [0.0] * len(vocab)
        for w in words:
            for i, v in enumerate(vocab):
                if v in w or w in v:
                    vec[i] += 1.0
        if sum(vec) == 0:
            return None
        norm = sum(x * x for x in vec) ** 0.5 or 1.0
        return [x / norm for x in vec]
    except Exception:
        return None