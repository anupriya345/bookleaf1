# BookLeaf Author Support & Communication Portal

A starter full-stack solution for the confidential BookLeaf technical assignment.

## Stack
- Backend: FastAPI, SQLite (easy local demo), SQLAlchemy
- Auth: JWT bearer tokens, hashed passwords
- Frontend: React + Vite
- AI: optional OpenAI-compatible API integration; deterministic fallback works without an API key
- Ticket updates: short polling in the frontend

## Requirements
- Python 3.10+
- Node.js 18+
- Optional LLM API key for AI-generated drafts

## Run locally

### 1. Backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

On macOS/Linux, use `cp .env.example .env` instead of `copy`.

The SQLite database is created automatically in `backend/bookleaf.db` (relative SQLite paths in `DATABASE_URL` are resolved from the backend directory, regardless of where the server is launched). The first startup seeds the 10 authors and 18 books.
Demo password for all seeded accounts: `BookLeaf@123`
Author login: `priya.sharma@email.com`
Admin login: `admin@bookleaf.local`

### 2. Frontend
Open another terminal:
```bash
cd frontend
npm install
npm run dev
```
Open the URL printed by Vite, usually http://localhost:5173.

## Environment
Edit `backend/.env`:
- `SECRET_KEY`: change before deployment
- `OPENAI_API_KEY`: optional; leave blank to use the local fallback
- `OPENAI_MODEL`: defaults to `gpt-4o-mini`
- `FRONTEND_ORIGIN`: frontend URL

Never commit `.env` or real secrets.

## Implemented
- Login and role-aware UI
- Author sees their own books and tickets
- Ticket creation with book or General / Account Level
- Admin queue, filters, assignment, category/priority/status overrides
- AI-assisted category and priority (LLM when configured, rules fallback otherwise)
- AI draft reply grounded in BookLeaf policy text
- Admin reply and private internal notes
- Polling for near-real-time updates
- Swagger docs and seeded sample records

## Production hardening still recommended
- Use PostgreSQL and migrations (Alembic) for production.
- Use secure HttpOnly cookie sessions or carefully configured token storage, CSRF protection where applicable, rate limiting, email verification/password reset, audit logging, and stronger monitoring.
- Add tests, pagination, attachment upload/storage, SSE/WebSockets, and deployment-specific CORS/secret configuration.
- The provided ISBN values contain `X` placeholders. They are preserved as provided for the assignment.
- This is an assessment starter, not a production-ready publishing system.

## Suggested demo walkthrough
1. Log in as `priya.sharma@email.com` / `BookLeaf@123` and inspect books/royalties.
2. Submit a ticket about royalty payment or printing quality.
3. Log in as `admin@bookleaf.local` / `BookLeaf@123`.
4. Filter tickets, inspect the AI classification/priority, generate a draft, edit it and send.
5. Return to the author portal and confirm the response appears.
6. Add a private admin note and verify it is not shown to the author.
