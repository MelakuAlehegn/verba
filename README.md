<div align="center">

# Verba

**Chat with your documents — answers grounded in your own files, with citations.**

Upload documents, ask questions in plain language, and get streamed answers that
cite the exact passages they came from. A multi-tenant, self-hostable RAG
application built backend-first.

</div>

---

## Overview

Verba is a Retrieval-Augmented Generation (RAG) app. You upload your files; Verba
parses, chunks, and embeds them into a vector store, then answers your questions
**only from your documents** — refusing to guess when the answer isn't there — and
shows the source passages behind every answer.

- **Grounded answers** — responses are constrained to retrieved context, with a
  relevance threshold so off-topic questions get an honest "I don't know."
- **Citations you can verify** — each answer links back to the source document and
  the exact passage used.
- **Multi-tenant by design** — every query is scoped to the authenticated user;
  no cross-tenant access.
- **Streaming chat** — answers stream token-by-token over Server-Sent Events.
- **Async ingestion** — parsing/embedding runs on a background worker, so uploads
  never block the API.

## How it works

```
Upload ─▶ Object storage (raw file)
       └▶ Postgres (document row, status=queued) ─▶ Celery worker
                                                      │ parse → chunk → embed
                                                      ├▶ Qdrant   (vectors)
                                                      └▶ Postgres (chunks, status=ready)

Ask ─▶ embed question ─▶ Qdrant similarity search (tenant + score filtered)
                       └▶ fetch chunk text from Postgres ─▶ prompt the LLM
                                                          └▶ stream answer + citations (SSE)
```

Postgres is the source of truth; Qdrant is a derived, rebuildable index.

## Tech stack

| Layer | Technology |
| --- | --- |
| **Backend** | FastAPI (Python 3.11+), SQLAlchemy 2.0, Alembic |
| **Database** | PostgreSQL (relational source of truth) |
| **Vector store** | Qdrant (similarity search, payload-filtered per tenant) |
| **Queue / worker** | Redis + Celery (async document ingestion) |
| **Object storage** | S3-compatible (MinIO locally) |
| **AI** | Google Gemini — embeddings (`gemini-embedding-001`) + generation (`gemini-2.5-flash`) |
| **Auth** | Google OAuth 2.0 + email/password, HttpOnly session cookies (bcrypt) |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query, React Router |

## Repository structure

```
verba/
├─ backend/            FastAPI app (routes → services → crud → models), Alembic, Celery worker, tests
├─ frontend/           Vite + React + TypeScript SPA (features/, pages/, components/)
├─ docker-compose.yml  Full local stack: api + worker + postgres + qdrant + redis + minio
├─ commands.md         Day-to-day run commands
└─ Makefile            Backend shortcuts (test, lint, run, migrate)
```

The backend follows a strict **route → service → crud → model** layering; the
frontend is organized by feature (`auth`, `chats`, `documents`, `settings`).

## Getting started

### Prerequisites

- Docker + Docker Compose
- A Google API key (for Gemini) and, optionally, Google OAuth credentials
- For local (non-Docker) development: Python 3.11+ and Node.js 18+

### 1. Configure environment

```bash
cp backend/.env.example backend/.env
```

Set at minimum:

| Variable | Purpose |
| --- | --- |
| `GOOGLE_API_KEY` | Gemini embeddings + generation |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google sign-in (optional; email/password works without it) |
| `SESSION_SECRET` | Session cookie signing |

Other settings (database, Qdrant, Redis, S3, chunk size, retrieval `top_k` and
score threshold, models) have sensible defaults in `.env.example`.

### 2a. Run the whole stack with Docker Compose

```bash
docker compose up --build
```

This boots Postgres, Redis, Qdrant, MinIO, the API, and the Celery worker, and runs
database migrations automatically. The API is available at `http://localhost:8000`
(interactive docs at `/docs`).

### 2b. Run for development (hot reload)

Run the infrastructure in containers and the app as local processes so code changes
apply instantly. See **[commands.md](commands.md)** for the exact sequence — in short:

```bash
# infra (containers)
docker compose up -d postgres redis qdrant minio

# backend API (Terminal 1)
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload                                   # :8000

# ingestion worker (Terminal 2) — required for uploads to process
celery -A app.workers.celery_app.celery_app worker --loglevel=info

# frontend (Terminal 3)
cd frontend && npm install && npm run dev                       # :8080
```

Then open **http://127.0.0.1:8080**.

> Use `127.0.0.1` (not `localhost`) so the app and API share the same site and the
> session cookie is sent on requests.

## Testing & quality

```bash
# Backend: lint (ruff) + tests (pytest)
cd backend && make check

# Frontend: typecheck, lint, build
cd frontend && npx tsc --noEmit && npm run lint && npm run build
```

CI runs ruff + pytest on every push and pull request.

