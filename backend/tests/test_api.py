import os

from fastapi.testclient import TestClient

from app.core.db import SessionLocal, init_db
from app.main import app
from app.services import store

if os.path.exists('sentinelops.db'):
    os.remove('sentinelops.db')

init_db()
with SessionLocal() as _db:
    store.seed_defaults(_db)

client = TestClient(app)
API_TOKEN_HEADER = {"X-API-Token": "change-me"}


def auth_headers() -> dict[str, str]:
    token_resp = client.post(
        "/auth/token",
        data={"username": "secops", "password": "secops123"},
        headers=API_TOKEN_HEADER,
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    return {**API_TOKEN_HEADER, "Authorization": f"Bearer {token}"}


def test_health():
    assert client.get('/health').status_code == 200


def test_auth_required():
    assert client.get('/api/v1/assets').status_code == 401


def test_token_login_and_asset_read():
    headers = auth_headers()
    assert client.get('/api/v1/assets', headers=headers).status_code == 200


def test_risky_playbook_requires_approval_flow():
    headers = auth_headers()
    run = client.post('/api/v1/playbooks/1/run?dry_run=false', headers=headers)
    assert run.status_code == 200
    body = run.json()
    assert body['requires_approval'] is True
    assert client.post(f"/api/v1/playbook-runs/{body['run_id']}/approve", headers=headers).status_code == 200


def test_telemetry_ingest_and_read():
    headers = auth_headers()
    assert client.post('/api/v1/telemetry', headers=headers, json={"source": "agent-1", "event_type": "cpu_spike", "severity": "high", "payload": "cpu=97"}).status_code == 200
    read = client.get('/api/v1/telemetry', headers=headers)
    assert read.status_code == 200
    assert any(e['source'] == 'agent-1' for e in read.json())
