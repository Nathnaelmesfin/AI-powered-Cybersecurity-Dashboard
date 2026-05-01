from app.services import correlation


def test_network_identity_cross_correlation_rule(monkeypatch):
    emitted = []
    monkeypatch.setattr(correlation, "publish_event", lambda et, d: emitted.append((et, d)))

    correlation.process_telemetry_for_correlation("hq:host-a", "high", "port_scan", "src=10.0.0.8")
    correlation.process_telemetry_for_correlation("hq:host-b", "high", "failed_login", "user=admin")

    rules = [d["rule"] for et, d in emitted if et == "correlation_alert"]
    assert "network_identity_cross_correlation" in rules


def test_identity_impossible_travel_rule(monkeypatch):
    emitted = []
    monkeypatch.setattr(correlation, "publish_event", lambda et, d: emitted.append((et, d)))

    correlation.process_telemetry_for_correlation("branch1:odoo-app", "medium", "user_login", "user=alice,country=ET")
    correlation.process_telemetry_for_correlation("branch1:odoo-app", "medium", "vpn_login", "user=alice,country=DE")

    rules = [d["rule"] for et, d in emitted if et == "correlation_alert"]
    assert "identity_impossible_travel" in rules
