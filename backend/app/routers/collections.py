"""Collections router."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Collection, CollectionItem

router = APIRouter(prefix="/collections", tags=["Collections"])


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class CollectionRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    item_count: int = 0


class CollectionItemAdd(BaseModel):
    cultural_object_id: uuid.UUID


@router.get("", response_model=list[CollectionRead])
def list_collections(db: Session = Depends(get_db)):
    collections = db.execute(select(Collection).order_by(Collection.name)).scalars().all()
    result = []
    for c in collections:
        count = db.execute(
            select(CollectionItem.id).where(CollectionItem.collection_id == c.id)
        ).scalars().all()
        result.append(CollectionRead(id=c.id, name=c.name, description=c.description, item_count=len(count)))
    return result


@router.post("", response_model=CollectionRead, status_code=201)
def create_collection(payload: CollectionCreate, db: Session = Depends(get_db)):
    collection = Collection(name=payload.name, description=payload.description)
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return CollectionRead(id=collection.id, name=collection.name, description=collection.description)


@router.post("/{collection_id}/items", response_model=dict, status_code=201)
def add_item(collection_id: uuid.UUID, payload: CollectionItemAdd, db: Session = Depends(get_db)):
    collection = db.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    from app.services import cultural_object_service

    cultural_object_service.get_object_or_404(db, payload.cultural_object_id)
    db.add(CollectionItem(collection_id=collection_id, cultural_object_id=payload.cultural_object_id))
    db.commit()
    return {"ok": True}