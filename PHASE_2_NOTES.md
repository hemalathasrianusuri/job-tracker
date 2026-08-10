# Phase 2: Authentication — Complete

## What's built

**Backend (`apps/api`)**
- `modules/auth/` — full domain module: `models.py`, `schemas.py`, `repository.py`, `service.py`, `router.py`, `oauth.py`
- JWT access (15 min) + refresh (14 days) tokens, refresh stored as an **httpOnly cookie**, never touched by frontend JS
- **Refresh token rotation**: every `/auth/refresh` call issues a new refresh token and revokes the old one's `jti` in Redis (`token_blacklist.py`) — a stolen refresh token is single-use
- Google OAuth via Authlib, with **account linking** (a Google login with an email that already has a password account attaches `google_id` rather than creating a duplicate)
- `core/middleware/` — request ID, structured JSON logging (structlog), Redis-backed rate limiting on `/auth/*` — the in-process "gateway concerns" from the Phase 1 revision, no separate gateway service
- `core/settings/` — environment-split config; `ProductionSettings` fails loudly if `SECRET_KEY` or Google credentials are left as dev defaults
- Alembic migration `0001_create_users_table` — run with `alembic upgrade head`
- All Python files verified to compile (`py_compile`, zero syntax errors)

**Frontend (`apps/web`)**
- `lib/api-client.ts` — typed fetch wrapper with automatic 401 → refresh → retry, de-duped against concurrent refresh stampedes
- `lib/stores/auth-store.ts` — Zustand store, **access token kept in memory only**, never localStorage
- `middleware.ts` — edge-level route gating on protected paths (presence check only; real auth is always enforced server-side)
- `app/(auth)/login/page.tsx` — email/password + "Continue with Google"
- `app/(auth)/callback/page.tsx` — reads the access token from the URL **fragment** (never sent to server, never logged) after OAuth redirect
- `app/providers/auth-provider.tsx` — silently re-hydrates the session via `/auth/refresh` on page load

## Local setup

```bash
# Backend
cd apps/api
cp .env.example .env        # fill in SECRET_KEY, Google OAuth creds
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd apps/web
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

You'll need a Postgres instance and Redis running locally (or via the `docker-compose.yml` that lands in the deployment phase). For Google OAuth, create credentials in Google Cloud Console with authorized redirect URI `http://localhost:8000/api/v1/auth/google/callback`.

**Not yet wired (needs the rest of the Next.js app shell, which isn't built yet):** `AuthProvider` needs to be mounted in `app/layout.tsx` around `{children}` — I held off creating `layout.tsx` itself since that belongs to Phase 4 (Frontend), where the overall app shell, ShadCN theme, and dashboard layout get built together rather than piecemeal.

## Security decisions worth knowing about

- Access token: memory only, 15 min. Refresh token: httpOnly + `Secure` (prod) + `SameSite=Lax` cookie, scoped to `/api/v1/auth` path only — it's never sent to non-auth endpoints.
- Login/register error messages are identical for "no such user" and "wrong password" (and for "this email is Google-only") to avoid user enumeration.
- `SessionMiddleware` is added only because Authlib's OAuth flow needs it for CSRF state — it's not used for anything else in this app; real auth state lives in the JWTs.

## Next: Phase 3 — Backend APIs

Jobs module (the core tracker CRUD + status pipeline), Companies, and the Resume upload endpoint — built on the same `modules/<name>/{router,service,repository,schemas,models}` pattern established here.
