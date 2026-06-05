# document-qa-rag

A multi-tenant RAG application for asking questions against your own documents and getting grounded, cited answers.

Currently a Vite + React + TypeScript frontend (shadcn/ui + Tailwind). See [docs/ARCHITECTURE_AND_PRODUCT_PLAN_claude.md](docs/ARCHITECTURE_AND_PRODUCT_PLAN_claude.md) for the full architecture and the plan to evolve it into a production-grade product (FastAPI backend, Postgres, Qdrant, Google OAuth, document ingestion, persistent chat).

## Getting started

```bash
npm install
npm run dev      # http://localhost:8080
```

Other scripts: `npm run build`, `npm run preview`, `npm run lint`.
