"""Mizizi API — FastAPI application entry point.

Exposes the Cultural Object archive, its provenance, permissions and search.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.routers import (
    admin,
    auth,
    collections,
    creator_keys,
    cultural_object_resources,
    cultural_objects,
    reference,
    search,
)

app = FastAPI(
    title=f"{settings.app_name} API",
    description=(
        "The Living Memory of Africa. "
        "An AI-powered living archive for African oral culture. "
        "Original recordings are preserved immutably; everything else is a "
        "rights-aware, provenance-linked derivative."
    ),
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={"detail": "Conflict: resource already exists."})

api = settings.api_v1_prefix

app.include_router(auth.router, prefix=api)
app.include_router(admin.router, prefix=api)
app.include_router(creator_keys.router, prefix=api)
app.include_router(reference.languages_router, prefix=api)
app.include_router(reference.communities_router, prefix=api)
app.include_router(reference.places_router, prefix=api)
app.include_router(reference.contributors_router, prefix=api)
app.include_router(cultural_objects.router, prefix=api)
app.include_router(cultural_object_resources.router, prefix=api)
app.include_router(collections.router, prefix=api)
app.include_router(search.router, prefix=api)


@app.get("/", tags=["meta"])
def root():
    return {
        "name": settings.app_name,
        "mission": "No generation should be the last generation to remember a story.",
        "docs": "/docs",
        "version": "0.1.0",
    }


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}