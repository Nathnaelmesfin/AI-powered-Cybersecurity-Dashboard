from datetime import datetime, timezone

from app.core.db import SessionLocal, init_db
from app.models.entities import TelemetryEventEntity
from app.services import correlation


def test_network_identity_cross_correlation_rule(monkeypatch):
    emitted = []
    monkeypatch.setattr(correlation, "publish_event", lambda et, d: emitted.append((et, d)))
    init_db()
    with SessionLocal() as db:
        db.add(TelemetryEventEntity(source="hq:host-a", severity="high", event_type="port_scan", payload="src=10.0.0.8", created_at=datetime.now(timezone.utc)))
        db.add(TelemetryEventEntity(source="hq:host-b", severity="high", event_type="failed_login", payload="user=admin", created_at=datetime.now(timezone.utc)))
        db.commit()
        correlation.process_telemetry_for_correlation(db, "hq:host-b", "high", "failed_login", "user=admin")

    rules = [d["rule"] for et, d in emitted if et == "correlation_alert"]
    assert "network_identity_cross_correlation" in rules


def test_identity_impossible_travel_rule(monkeypatch):
    emitted = []
    monkeypatch.setattr(correlation, "publish_event", lambda et, d: emitted.append((et, d)))
    init_db()
    with SessionLocal() as db:
        db.add(TelemetryEventEntity(source="branch1:odoo-app", severity="medium", event_type="user_login", payload="user=alice,country=ET", created_at=datetime.now(timezone.utc)))
        db.add(TelemetryEventEntity(source="branch1:odoo-app", severity="medium", event_type="vpn_login", payload="user=alice,country=DE", created_at=datetime.now(timezone.utc)))
        db.commit()
        correlation.process_telemetry_for_correlation(db, "branch1:odoo-app", "medium", "vpn_login", "user=alice,country=DE")

    rules = [d["rule"] for et, d in emitted if et == "correlation_alert"]
    assert "identity_impossible_travel" in rules
