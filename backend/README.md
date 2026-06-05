# Backend

This folder is the first backend slice for the `document-qa-rag` project.

## What exists now

- FastAPI app factory in `app/main.py`
- Versioned API router in `app/api/v1/`
- Typed settings and JSON logging helpers in `app/core/`
- A basic health endpoint at `GET /api/v1/healthz`

## Run locally

After installing the Python dependencies, start the API with:

```bash
uvicorn app.main:app --reload --app-dir backend
```

## Test

From the `backend/` directory:

```bash
pytest
```

