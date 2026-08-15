"""FastAPI dependencies for authentication and authorization."""

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import ADMIN, REVIEWER, User
from app.services import auth_service

_bearer = HTTPBearer(auto_error=False)


def _resolve_token(creds: HTTPAuthorizationCredentials | None) -> str | None:
    if creds is None:
        return None
    return creds.credentials


def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    token = _resolve_token(creds)
    if not token:
        return None
    return auth_service.get_user_from_token(db, token)


def get_optional_user_anywhere(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    """Resolve a user from either the ``Authorization`` header or a ``?token=``
    query parameter.

    Media streams (``<audio>``/``<video>``) are requested by the browser as a
    plain URL, so the JWT cannot be sent as a header. Only routes that must
    authorize non-fetch media playback should use this dependency.
    """
    raw = creds.credentials if creds is not None else token
    if not raw:
        return None
    return auth_service.get_user_from_token(db, raw)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    token = _resolve_token(creds)
    user = auth_service.get_user_from_token(db, token) if token else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be signed in to do that.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_reviewer(user: User = Depends(get_current_user)) -> User:
    if user.role not in {REVIEWER, ADMIN}:
        raise HTTPException(
            status_code=403,
            detail="Only accepted reviewers can access the review queue.",
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user