"""Creator-key recovery — the contributor-facing side.

When a contributor loses the key that unlocks public access, they open a
request here; an administrator then emails the escrowed key back to their
registered address from the admin console.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.admin import CreatorKeyRequestCreate, CreatorKeyRequestRead
from app.services import creator_key_service

router = APIRouter(prefix="/creator-keys", tags=["Creator keys"])


@router.post("/requests", response_model=CreatorKeyRequestRead, status_code=201)
def request_key(
    payload: CreatorKeyRequestCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ask the Mizizi Administrator to email your creator key back."""
    req = creator_key_service.create_key_request(db, user, payload.object_id)
    obj = req.cultural_object
    return CreatorKeyRequestRead(
        id=req.id,
        user_id=req.user_id,
        user_email=user.email,
        cultural_object_id=req.cultural_object_id,
        object_code=obj.object_code,
        object_title=obj.title,
        status=req.status,
        decided_at=req.decided_at,
        created_at=req.created_at,
    )


@router.get("/requests", response_model=list[CreatorKeyRequestRead])
def my_requests(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Your key requests and their status."""
    result = []
    for req in creator_key_service.list_user_requests(db, user):
        obj = req.cultural_object
        result.append(
            CreatorKeyRequestRead(
                id=req.id,
                user_id=req.user_id,
                user_email=user.email,
                cultural_object_id=req.cultural_object_id,
                object_code=obj.object_code,
                object_title=obj.title,
                status=req.status,
                decided_at=req.decided_at,
                created_at=req.created_at,
            )
        )
    return result
