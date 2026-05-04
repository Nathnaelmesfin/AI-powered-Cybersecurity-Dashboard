from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.event_bus import publish_event
from app.models.entities import CorrelationStateEntity, TelemetryEventEntity

_SUPPRESSION_WINDOW = timedelta(minutes=10)


def _split_source(source: str) -> tuple[str, str]:
    if ":" in source:
        return source.split(":", 1)
    return "default", source


def _should_emit(db: Session, source_key: str, rule: str) -> bool:
    state = db.scalar(select(CorrelationStateEntity).where(CorrelationStateEntity.source_key == source_key, CorrelationStateEntity.rule == rule))
    now = datetime.now(timezone.utc)
    if state and now - state.last_alert_at < _SUPPRESSION_WINDOW:
        return False
    if state:
        state.last_alert_at = now
    else:
        db.add(CorrelationStateEntity(source_key=source_key, rule=rule, last_alert_at=now))
    db.commit()
    return True


def _emit(db: Session, source_key: str, rule: str, payload: dict) -> None:
    if _should_emit(db, source_key, rule):
        publish_event("correlation_alert", payload)


def process_telemetry_for_correlation(db: Session, source: str, severity: str, event_type: str, payload: str = "") -> None:
    site, host = _split_source(source)
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=5)

    recent_site = db.scalars(
        select(TelemetryEventEntity).where(
            TelemetryEventEntity.source.like(f"{site}:%"),
            TelemetryEventEntity.created_at >= window_start,
        )
    ).all()
    recent_host = [e for e in recent_site if e.source == source]
    recent_high = [e for e in recent_host if e.severity in {"high", "critical"}]

    if len(recent_high) >= 3:
        _emit(db, source, "burst_high_severity_events", {
            "source": source, "rule": "burst_high_severity_events", "count": len(recent_high), "window_minutes": 5,
            "recommended_action": "create_incident_and_investigate_source",
        })

    host_events = [e.event_type for e in recent_host]
    auth_failures = sum(1 for e in host_events if e in {"auth_failure", "ssh_failed_login", "failed_login"})
    endpoint_anomaly = any(e in {"cpu_spike", "high_cpu", "suspicious_process"} for e in host_events)
    if auth_failures >= 2 and endpoint_anomaly:
        _emit(db, source, "auth_burst_plus_endpoint_anomaly", {
            "source": source, "rule": "auth_burst_plus_endpoint_anomaly", "auth_failures": auth_failures,
            "endpoint_anomaly": True, "window_minutes": 5,
            "recommended_action": "check brute-force + process anomalies and isolate if needed",
        })

    type_counts = defaultdict(int)
    for e in recent_host:
        type_counts[e.event_type] += 1
    noisy = [et for et, c in type_counts.items() if c >= 5]
    if noisy:
        _emit(db, source, "noisy_repeated_event_dedup", {
            "source": source, "rule": "noisy_repeated_event_dedup", "event_types": noisy,
            "window_minutes": 5, "recommended_action": "deduplicate alerts and prioritize correlated indicators",
        })

    site_events = [e.event_type for e in recent_site]
    has_scan = any(e in {"port_scan", "lateral_scan", "network_scan"} for e in site_events)
    has_identity_attack = any(e in {"failed_login", "auth_failure", "privilege_escalation_attempt"} for e in site_events)
    affected_hosts = { _split_source(e.source)[1] for e in recent_site if e.event_type in {"port_scan", "lateral_scan", "network_scan", "failed_login", "auth_failure"}}
    if has_scan and has_identity_attack and len(affected_hosts) >= 2:
        _emit(db, site, "network_identity_cross_correlation", {
            "source": site, "rule": "network_identity_cross_correlation", "affected_hosts": sorted(list(affected_hosts)),
            "window_minutes": 5, "recommended_action": "block scanning source, enforce MFA resets, isolate impacted endpoints",
        })

    geo_markers = [e.payload for e in recent_site if e.event_type in {"user_login", "vpn_login"} and "country=" in e.payload]
    countries = {m.split("country=")[-1].split(",")[0].strip() for m in geo_markers}
    if len(countries) >= 2 and len(geo_markers) >= 2:
        _emit(db, site, "identity_impossible_travel", {
            "source": site, "rule": "identity_impossible_travel", "countries": sorted(list(countries)),
            "window_minutes": 5, "recommended_action": "challenge login sessions and rotate user credentials",
        })
