"""Search router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_optional_user
from app.models import User
from app.schemas.cultural_object import CulturalObjectSummary
from app.schemas.search import SearchResponse
from app.services import search_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
def search(
    q: str = Query(min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    results, mode = search_service.search(db, q, limit, user=user)
    return SearchResponse(
        query=q,
        mode=mode,
        results=[CulturalObjectSummary.model_validate(o) for o in results],
        total=len(results),
    )