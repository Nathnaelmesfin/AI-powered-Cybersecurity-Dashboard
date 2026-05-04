# SentinelOps AI

## Implemented
- FastAPI backend with SQLAlchemy persistence
- JWT login (`/auth/token`) + API token gate
- Optional OIDC token validation mode (`SENTINELOPS_AUTH_MODE=oidc`)
- DB-driven role permissions (`role_permissions`) enforced per action
- Playbook approval workflow and audit logs
- Telemetry ingestion and query APIs
- WebSocket live summary feed
- Alembic migrations (`0001`, `0002`)
- Frontend stubs: static SOC page + multi-page Next.js starter app

## Backend Run
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Default seeded user:
- username: `secops`
- password: `secops123`

## Auth Modes
### Local (default)
1. Include `X-API-Token: change-me`
2. Request token from `POST /auth/token`
3. Use `Authorization: Bearer <token>` for `/api/v1/*`

### OIDC
Set:
- `SENTINELOPS_AUTH_MODE=oidc`
- `SENTINELOPS_OIDC_ISSUER`
- `SENTINELOPS_OIDC_AUDIENCE`
- `SENTINELOPS_OIDC_JWKS_URL`

## Frontend
- Static MVP page: `frontend/index.html`
- Next.js app pages:
  - `/dashboard`
  - `/incidents`
  - `/assets`
  - `/playbooks`
  - `/topology`
