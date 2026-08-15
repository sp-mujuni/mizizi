"""Authentication and authorization service."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import security
from app.models import (
    ADMIN,
    MEMBER,
    REVIEWER,
    ReviewerApplication,
    Session as AuthSession,
    User,
    UserCommunity,
    UserLanguage,
    UserPlace,
)
from app.schemas.auth import RegisterRequest

SESSION_TTL = timedelta(days=30)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_session(db: Session, user: User) -> str:
    token, token_hash = security.new_session_token()
    db.add(
        AuthSession(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=_now() + SESSION_TTL,
        )
    )
    db.commit()
    return token


def get_user_from_token(db: Session, token: str) -> User | None:
    if not token:
        return None
    session = (
        db.execute(
            select(AuthSession)
            .where(
                AuthSession.token_hash == security.hash_token(token),
                AuthSession.expires_at > _now(),
            )
        )
        .scalars()
        .first()
    )
    if session is None:
        return None
    return db.get(User, session.user_id)


def revoke_session(db: Session, token: str) -> None:
    session = (
        db.execute(
            select(AuthSession).where(AuthSession.token_hash == security.hash_token(token))
        )
        .scalars()
        .first()
    )
    if session is not None:
        db.delete(session)
        db.commit()


def register_user(db: Session, payload: RegisterRequest) -> tuple[User, str]:
    existing = db.execute(select(User).where(func.lower(User.email) == payload.email.lower())).scalars().first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    if not payload.language_ids:
        raise HTTPException(
            status_code=422,
            detail="You must choose at least one language from your cultural background.",
        )

    user = User(
        email=payload.email,
        password_hash=security.hash_password(payload.password),
        display_name=payload.display_name,
        role=MEMBER,
    )
    db.add(user)
    db.flush()

    for lid in payload.language_ids:
        db.add(UserLanguage(user_id=user.id, language_id=lid))
    for pid in payload.place_ids:
        db.add(UserPlace(user_id=user.id, place_id=pid))
    for cid in payload.community_ids:
        db.add(UserCommunity(user_id=user.id, community_id=cid))
    db.flush()
    db.commit()
    db.refresh(user)
    return user, create_session(db, user)


def login(db: Session, email: str, password: str) -> tuple[User, str]:
    user = db.execute(select(User).where(func.lower(User.email) == email.lower())).scalars().first()
    if user is None or not security.verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return user, create_session(db, user)


def apply_to_reviewer(db: Session, user: User, statement: str) -> ReviewerApplication:
    if user.role in {REVIEWER, ADMIN}:
        raise HTTPException(status_code=400, detail="You are already a reviewer.")
    pending = (
        db.execute(
            select(ReviewerApplication).where(
                ReviewerApplication.user_id == user.id,
                ReviewerApplication.status == "pending",
            )
        )
        .scalars()
        .first()
    )
    if pending is not None:
        raise HTTPException(status_code=409, detail="You already have a pending application.")
    app = ReviewerApplication(user_id=user.id, statement=statement, status="pending")
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def list_applications(db: Session) -> list[ReviewerApplication]:
    return list(
        db.execute(
            select(ReviewerApplication).order_by(ReviewerApplication.created_at.asc())
        )
        .scalars()
        .all()
    )


def decide_application(db: Session, admin: User, application_id: uuid.UUID, approve: bool) -> ReviewerApplication:
    app = db.get(ReviewerApplication, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    if app.status != "pending":
        raise HTTPException(status_code=409, detail="Application already decided.")
    app.status = "approved" if approve else "rejected"
    app.decided_by = admin.id
    app.decided_at = _now()
    if approve:
        user = db.get(User, app.user_id)
        if user is not None:
            user.role = REVIEWER
    db.commit()
    db.refresh(app)
    return app