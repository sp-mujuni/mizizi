"""Accounts, sessions, cultural background and reviewer applications."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models import CulturalObject, ReviewerApplication, User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    ReviewerApplicationRead,
    ReviewerApplyRequest,
    ReviewerDecideRequest,
    UserProfileBrief,
    UserRead,
)
from app.schemas.cultural_object import CulturalObjectRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


def _user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        languages=[UserProfileBrief(id=l.id, name=l.name) for l in user.languages],
        places=[UserProfileBrief(id=p.id, name=p.name) for p in user.places],
        communities=[UserProfileBrief(id=c.id, name=c.name) for c in user.communities],
        created_at=user.created_at,
    )


def _application_read(app: ReviewerApplication) -> ReviewerApplicationRead:
    return ReviewerApplicationRead(
        id=app.id,
        user_id=app.user_id,
        user_email=app.user.email,
        user_display_name=app.user.display_name,
        statement=app.statement,
        status=app.status,
        decided_at=app.decided_at,
        created_at=app.created_at,
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user, token = auth_service.register_user(db, payload)
    return AuthResponse(access_token=token, user=_user_read(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user, token = auth_service.login(db, payload.email, payload.password)
    return AuthResponse(access_token=token, user=_user_read(user))


@router.post("/logout", response_model=dict)
def logout_endpoint(
    creds: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
):
    if creds is None:
        raise HTTPException(status_code=401, detail="Not signed in.")
    auth_service.revoke_session(db, creds.credentials)
    return {"ok": True, "detail": "Signed out."}


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return _user_read(user)


@router.get("/me/objects", response_model=list[CulturalObjectRead])
def my_objects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.execute(
        select(CulturalObject)
        .where(CulturalObject.user_id == user.id)
        .order_by(CulturalObject.created_at.desc())
    ).scalars().all()
    return items


@router.post("/apply-reviewer", response_model=ReviewerApplicationRead, status_code=201)
def apply_reviewer(
    payload: ReviewerApplyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _application_read(auth_service.apply_to_reviewer(db, user, payload.statement))


@router.get("/reviewer-applications", response_model=list[ReviewerApplicationRead])
def list_applications(
    user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    return [_application_read(a) for a in auth_service.list_applications(db)]


@router.post("/reviewer-applications/{application_id}/decide", response_model=ReviewerApplicationRead)
def decide_application(
    application_id: uuid.UUID,
    payload: ReviewerDecideRequest,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _application_read(
        auth_service.decide_application(db, user, application_id, payload.approve)
    )