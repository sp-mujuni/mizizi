# Mizizi — The Living Memory of Africa

> *So the stories don't disappear.*

**Mizizi** (Swahili for **roots**) is an AI-powered living archive for African oral culture. It
preserves original recordings of stories, songs, riddles and proverbs — never altering the
source — and makes them responsibly discoverable and transmissible across generations.

> **Mizizi Archive** remembers. **Mizizi AI** interprets. **The community** decides.

This repository contains **Mizizi v0** (Alpha), the foundational implementation of the
Mizizi Cultural Object: the atomic, provenance-aware, rights-aware, multimodal digital
representation of one piece of cultural memory.

## Core principles

1. **The original recording is never altered.** Everything the AI produces is a derivative
   layer on top of an immutable source.
2. **Cultural consent is a first-class system.** Permissions, consents and access levels are
   enforced in code, not policy documents.
3. **Provenance is immutable.** Every significant event in an object's life is recorded.
4. **The archive outlives any AI model.** The schema is designed so vector search, knowledge
   graphs and AI pipelines can be added later without rebuilding the core.

## MVP scope (Alpha 0.1)

- **3 languages**: Luganda, Runyankole-Rukiga, Acholi
- **4 content types**: stories, songs, riddles, proverbs
- One complete Cultural Object lifecycle:
  create → upload original → checksum → transcribe → review → translate → permissions →
  provenance → publish → search → adapt (permission-aware)

## Repository layout

```
mizizi/
├── backend/            # FastAPI + SQLAlchemy + Alembic + PostgreSQL
│   └── app/
│       ├── core/       # config, database, storage, enums
│       ├── models/     # SQLAlchemy ORM models
│       ├── schemas/    # Pydantic schemas (API representation)
│       ├── routers/    # API routes
│       ├── services/   # business logic
│       └── seed/       # seed data
├── frontend/           # Next.js (App Router) + React + Tailwind
│   └── src/
│       ├── app/        # / (home), /archive, /record, /object/[id], /review, /ai
│       ├── components/ # navbar, object card
│       └── lib/        # API client + types
└── docker-compose.yml  # PostgreSQL 17 + MinIO (S3-compatible)
```

## Tech stack

| Layer      | Choice                                                            |
|------------|-------------------------------------------------------------------|
| Frontend   | Next.js 16 (App Router), React 19, Tailwind CSS 4              |
| Backend    | FastAPI, Python 3.13, SQLAlchemy 2, Pydantic v2                   |
| Database   | PostgreSQL 17 (+ `pgvector` optional for semantic search)         |
| Storage    | S3-compatible object storage (MinIO locally; boto3 in prod)       |
| Migrations | Alembic                                                           |
| Infra      | Docker Compose (Postgres + MinIO)                                 |

## Quick start

### 1. Infrastructure

```bash
docker compose up -d          # starts PostgreSQL 17 + MinIO
```

> No Docker? Use a locally installed PostgreSQL and set `DATABASE_URL` accordingly.
> The storage layer automatically falls back to a local `data/` directory when
> `STORAGE_BACKEND=local` (default for development).

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # Windows  (cp .env.example .env on Unix)
alembic upgrade head
uvicorn app.main:app --reload   # http://localhost:8000  (docs at /docs)
```

Seed the archive with Ugandan languages, communities, places and sample objects:

```bash
python -m app.seed.seed
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # optional: set NEXT_PUBLIC_API_BASE_URL
npm run dev                  # http://localhost:3000
```

Screens (per the concept-notes blueprint):

| Route            | Purpose                                              |
|------------------|------------------------------------------------------|
| `/`              | Home — "What did your grandmother tell you?"         |
| `/archive`       | Browse & filter the archive, full-text search        |
| `/record`        | Contribute: create object, upload, transcribe, translate |
| `/object/[id]`   | Cultural Object: original media, transcript, translation, provenance timeline, permissions |
| `/review`        | Human-in-the-loop transcription/translation review   |
| `/ai`            | Permission-aware AI adaptation ("Ask Mizizi")        |

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` (the default) to point at the backend.

## Cultural Object model

Every cultural object carries a stable, human-readable identity, e.g.

```
MZ-UG-LGD-STORY-00000001
Mizizi · Uganda · Luganda · Story · #1
```

- `UUID` primary key (database), `object_code` (humans, researchers, citations)
- `status`: draft → processing → review → verified → published → restricted/withdrawn/archived
- `verification_status`: unverified → ai_processed → human_reviewed → community_verified → expert_verified
- **Permissions** (first-class): preservation, public_access, educational_use, ai_analysis,
  ai_training, derivative_work, commercial_use, voice_cloning. **Only the creator** can change
  them: each object stores a SHA-256 hash of a creator key returned exactly once at creation
  (and kept in the contributor's browser). Permission changes require the `X-Creator-Key`
  header; a wrong or missing key is `403`.
- **Consents** with type, scope, grant/expiry/revocation and evidence references
- **Provenance events**: an append-only audit trail per object
- **Media assets**: original file stored immutably with SHA-256 checksum
- **Derivatives**: every AI/derivative work is permanently linked to its source(s)
- `ON DELETE RESTRICT` everywhere — an archive behaves like an archive, not a social app.

## API (excerpt)

| Method | Endpoint                                    | Purpose                       |
|--------|---------------------------------------------|-------------------------------|
| POST   | `/api/v1/cultural-objects`                  | Create a Cultural Object      |
| GET    | `/api/v1/cultural-objects/{id}`             | Fetch one (full representation)|
| POST   | `/api/v1/cultural-objects/{id}/media`       | Upload original recording     |
| POST   | `/api/v1/cultural-objects/{id}/transcriptions` | Generate/attach transcript |
| POST   | `/api/v1/cultural-objects/{id}/translations`   | Generate/attach translation |
| GET    | `/api/v1/search?q=...`                      | Full-text + (optional) vector search |
| POST   | `/api/v1/cultural-objects/{id}/derivatives` | Permission-aware AI adaptation |

Interactive docs: `http://localhost:8000/docs`.

## Roadmap

- **Alpha 0.1** (this codebase): Cultural Object lifecycle, object codes, provenance,
  media upload + checksum, transcription + review, translation, permissions/consents, search.
- **Alpha 0.2**: pgvector semantic search, cultural relationships (knowledge graph).
- **Alpha 0.3**: permission-aware AI adaptation and cultural retrieval service.
- **Beta**: cultural map, collections, institutional access, Mizizi API.

## License

MIT — see [LICENSE](LICENSE). Cultural material remains owned/custodied by the
communities that contributed it, per the consent records in the archive.