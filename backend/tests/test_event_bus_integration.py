import os
import shutil
import subprocess
import time

import pytest
from fastapi.testclient import TestClient

os.environ["SENTINELOPS_EVENT_BUS_ENABLED"] = "1"
os.environ["SENTINELOPS_NATS_URL"] = "nats://127.0.0.1:4223"

from app.main import app  # noqa: E402


@pytest.mark.skipif(shutil.which("nats-server") is None, reason="nats-server binary not available")
def test_ws_events_end_to_end_with_nats():
    proc = subprocess.Popen(["nats-server", "-p", "4223", "-js"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        client = TestClient(app)

        token_resp = client.post(
            "/auth/token",
            data={"username": "secops", "password": "secops123"},
            headers={"X-API-Token": "change-me"},
        )
        assert token_resp.status_code == 200
        token = token_resp.json()["access_token"]
        headers = {"X-API-Token": "change-me", "Authorization": f"Bearer {token}"}

        with client.websocket_connect("/ws/events") as ws:
            for _ in range(3):
                ingest = client.post(
                    "/api/v1/telemetry",
                    headers=headers,
                    json={"source": "sensor-a", "event_type": "auth_failure", "severity": "high", "payload": "count=1"},
                )
                assert ingest.status_code == 200

            got_types = set()
            end = time.time() + 8
            while time.time() < end and not {"telemetry", "correlation_alert"}.issubset(got_types):
                evt = ws.receive_json()
                got_types.add(evt.get("type"))

            assert "telemetry" in got_types
            assert "correlation_alert" in got_types
    finally:
        proc.terminate()
        proc.wait(timeout=5)
