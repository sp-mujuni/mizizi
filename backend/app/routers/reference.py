"""Reference-data routers: languages, communities, places, contributors."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Community, Contributor, Language, Place
from app.schemas.community import CommunityCreate, CommunityRead, CommunityUpdate
from app.schemas.contributor import ContributorCreate, ContributorRead, ContributorUpdate
from app.schemas.language import LanguageCreate, LanguageRead, LanguageUpdate
from app.schemas.place import PlaceCreate, PlaceRead, PlaceUpdate


def _get_or_404(db: Session, model, item_id: uuid.UUID):
    item = db.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return item


def _router(model, schema_read, schema_create, schema_update, route_name: str, singular: str):
    router = APIRouter(prefix=f"/{route_name}", tags=[route_name.capitalize()])

    @router.get("", response_model=list[schema_read])
    def list_all(db: Session = Depends(get_db)):
        return db.execute(select(model).order_by(model.name)).scalars().all()

    @router.post("", response_model=schema_read, status_code=201)
    def create(payload: schema_create, db: Session = Depends(get_db)):
        item = model(**payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @router.get("/{item_id}", response_model=schema_read)
    def read(item_id: uuid.UUID, db: Session = Depends(get_db)):
        return _get_or_404(db, model, item_id)

    @router.patch("/{item_id}", response_model=schema_read)
    def update(item_id: uuid.UUID, payload: schema_update, db: Session = Depends(get_db)):
        item = _get_or_404(db, model, item_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None or field in ("anonymous",):
                setattr(item, field, value)
        db.commit()
        db.refresh(item)
        return item

    @router.delete("/{item_id}", status_code=204)
    def delete(item_id: uuid.UUID, db: Session = Depends(get_db)):
        item = _get_or_404(db, model, item_id)
        db.delete(item)
        db.commit()

    return router


languages_router = _router(Language, LanguageRead, LanguageCreate, LanguageUpdate, "languages", "language")
communities_router = _router(
    Community, CommunityRead, CommunityCreate, CommunityUpdate, "communities", "community"
)
places_router = _router(Place, PlaceRead, PlaceCreate, PlaceUpdate, "places", "place")
contributors_router = _router(
    Contributor, ContributorRead, ContributorCreate, ContributorUpdate, "contributors", "contributor"
)