from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from app.core.event_bus import publish_event

_RECENT = defaultdict(lambda: deque(maxlen=20))


def process_telemetry_for_correlation(source: str, severity: str, event_type: str) -> None:
    now = datetime.now(timezone.utc)
    q = _RECENT[source]
    q.append((now, severity, event_type))

    window_start = now - timedelta(minutes=5)
    recent_high = [e for e in q if e[0] >= window_start and e[1] in {"high", "critical"}]
    if len(recent_high) >= 3:
        publish_event(
            "correlation_alert",
            {
                "source": source,
                "rule": "burst_high_severity_events",
                "count": len(recent_high),
                "window_minutes": 5,
                "recommended_action": "create_incident_and_investigate_source",
            },
        )
