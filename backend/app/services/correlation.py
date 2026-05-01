from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from app.core.event_bus import publish_event

_RECENT = defaultdict(lambda: deque(maxlen=50))
_LAST_ALERT_AT: dict[tuple[str, str], datetime] = {}
_SUPPRESSION_WINDOW = timedelta(minutes=10)


def _emit_with_suppression(source: str, rule: str, payload: dict) -> None:
    now = datetime.now(timezone.utc)
    key = (source, rule)
    last = _LAST_ALERT_AT.get(key)
    if last and now - last < _SUPPRESSION_WINDOW:
        return
    _LAST_ALERT_AT[key] = now
    publish_event("correlation_alert", payload)


def process_telemetry_for_correlation(source: str, severity: str, event_type: str) -> None:
    now = datetime.now(timezone.utc)
    q = _RECENT[source]
    q.append((now, severity, event_type))

    window_start = now - timedelta(minutes=5)
    recent = [e for e in q if e[0] >= window_start]
    recent_high = [e for e in recent if e[1] in {"high", "critical"}]

    # Rule 1: burst high severity
    if len(recent_high) >= 3:
        _emit_with_suppression(
            source,
            "burst_high_severity_events",
            {
                "source": source,
                "rule": "burst_high_severity_events",
                "count": len(recent_high),
                "window_minutes": 5,
                "recommended_action": "create_incident_and_investigate_source",
            },
        )

    # Rule 2: multi-signal auth failures + cpu spike correlation
    events = [e[2] for e in recent]
    auth_failures = sum(1 for e in events if e in {"auth_failure", "ssh_failed_login", "failed_login"})
    cpu_spike = any(e in {"cpu_spike", "high_cpu"} for e in events)
    if auth_failures >= 2 and cpu_spike:
        _emit_with_suppression(
            source,
            "auth_burst_plus_cpu_spike",
            {
                "source": source,
                "rule": "auth_burst_plus_cpu_spike",
                "auth_failures": auth_failures,
                "cpu_spike_detected": cpu_spike,
                "window_minutes": 5,
                "recommended_action": "check brute-force + process anomalies and isolate if needed",
            },
        )

    # Rule 3: dedup noisy repeated same event type
    type_counts = defaultdict(int)
    for _, _, et in recent:
        type_counts[et] += 1
    noisy = [et for et, c in type_counts.items() if c >= 5]
    if noisy:
        _emit_with_suppression(
            source,
            "noisy_repeated_event_dedup",
            {
                "source": source,
                "rule": "noisy_repeated_event_dedup",
                "event_types": noisy,
                "window_minutes": 5,
                "recommended_action": "deduplicate alerts and prioritize correlated indicators",
            },
        )
