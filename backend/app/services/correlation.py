from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from app.core.event_bus import publish_event

_RECENT = defaultdict(lambda: deque(maxlen=80))
_LAST_ALERT_AT: dict[tuple[str, str], datetime] = {}
_SUPPRESSION_WINDOW = timedelta(minutes=10)


# source convention: site:host (for cross-host/site reasoning)
def _split_source(source: str) -> tuple[str, str]:
    if ":" in source:
        site, host = source.split(":", 1)
        return site, host
    return "default", source


def _emit_with_suppression(source: str, rule: str, payload: dict) -> None:
    now = datetime.now(timezone.utc)
    key = (source, rule)
    last = _LAST_ALERT_AT.get(key)
    if last and now - last < _SUPPRESSION_WINDOW:
        return
    _LAST_ALERT_AT[key] = now
    publish_event("correlation_alert", payload)


def process_telemetry_for_correlation(source: str, severity: str, event_type: str, payload: str = "") -> None:
    now = datetime.now(timezone.utc)
    site, host = _split_source(source)
    q = _RECENT[site]
    q.append((now, source, host, severity, event_type, payload))

    window_start = now - timedelta(minutes=5)
    recent = [e for e in q if e[0] >= window_start]
    recent_host = [e for e in recent if e[1] == source]
    recent_high = [e for e in recent_host if e[3] in {"high", "critical"}]

    # Rule 1: burst high severity (host-level)
    if len(recent_high) >= 3:
        _emit_with_suppression(source, "burst_high_severity_events", {
            "source": source,
            "rule": "burst_high_severity_events",
            "count": len(recent_high),
            "window_minutes": 5,
            "recommended_action": "create_incident_and_investigate_source",
        })

    # Rule 2: identity + endpoint (host-level)
    host_events = [e[4] for e in recent_host]
    auth_failures = sum(1 for e in host_events if e in {"auth_failure", "ssh_failed_login", "failed_login"})
    cpu_spike = any(e in {"cpu_spike", "high_cpu", "suspicious_process"} for e in host_events)
    if auth_failures >= 2 and cpu_spike:
        _emit_with_suppression(source, "auth_burst_plus_endpoint_anomaly", {
            "source": source,
            "rule": "auth_burst_plus_endpoint_anomaly",
            "auth_failures": auth_failures,
            "endpoint_anomaly": True,
            "window_minutes": 5,
            "recommended_action": "check brute-force + process anomalies and isolate if needed",
        })

    # Rule 3: dedup noisy repeated same event type
    type_counts = defaultdict(int)
    for _, _, _, _, et, _ in recent_host:
        type_counts[et] += 1
    noisy = [et for et, c in type_counts.items() if c >= 5]
    if noisy:
        _emit_with_suppression(source, "noisy_repeated_event_dedup", {
            "source": source,
            "rule": "noisy_repeated_event_dedup",
            "event_types": noisy,
            "window_minutes": 5,
            "recommended_action": "deduplicate alerts and prioritize correlated indicators",
        })

    # Rule 4: network + identity cross-correlation (site-level)
    site_events = [e[4] for e in recent]
    has_scan = any(e in {"port_scan", "lateral_scan", "network_scan"} for e in site_events)
    has_identity_attack = any(e in {"failed_login", "auth_failure", "privilege_escalation_attempt"} for e in site_events)
    affected_hosts = {e[2] for e in recent if e[4] in {"port_scan", "lateral_scan", "network_scan", "failed_login", "auth_failure"}}
    if has_scan and has_identity_attack and len(affected_hosts) >= 2:
        _emit_with_suppression(site, "network_identity_cross_correlation", {
            "source": site,
            "rule": "network_identity_cross_correlation",
            "affected_hosts": sorted(list(affected_hosts)),
            "window_minutes": 5,
            "recommended_action": "block scanning source, enforce MFA resets, isolate impacted endpoints",
        })

    # Rule 5: impossible-travel style identity anomaly (site-level simplified)
    geo_markers = [p for *_, et, p in recent if et in {"user_login", "vpn_login"} and "country=" in p]
    countries = {m.split("country=")[-1].split(",")[0].strip() for m in geo_markers}
    if len(countries) >= 2 and len(geo_markers) >= 2:
        _emit_with_suppression(site, "identity_impossible_travel", {
            "source": site,
            "rule": "identity_impossible_travel",
            "countries": sorted(list(countries)),
            "window_minutes": 5,
            "recommended_action": "challenge login sessions and rotate user credentials",
        })
