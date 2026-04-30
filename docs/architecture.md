# SentinelOps AI Architecture

## Design Principle

Build backend operational truth first:

**Agent → telemetry → inventory → detection → incident → controlled action → audit trail → AI explanation.**

## Core Services

1. **Sentinel Agent**
   - Linux/Windows endpoint telemetry
   - Services/process/package/user/login events
2. **Network Collector**
   - SNMPv3, syslog, NetFlow/sFlow, ICMP, SSH checks
3. **Application Telemetry SDK**
   - Odoo/Django/Node/API custom events and health probes
4. **Message Bus**
   - NATS/Kafka streams for decoupled ingestion
5. **Storage Layer**
   - PostgreSQL (CMDB, incidents, workflows)
   - Prometheus/TimescaleDB (metrics)
   - OpenSearch/ClickHouse (logs)
6. **Detection + Correlation Engine**
   - Rule-based detection (Sigma/YARA mapping)
   - Temporal correlation and enrichment
7. **SOAR/Automation Engine**
   - Playbooks with approval gates and dry-run mode
8. **AI Copilot Service**
   - Incident summary, root cause hints, risk forecasting

## Backend Boundaries

- **FastAPI ingestion and live APIs**: low latency and websocket streams
- **Django/DRF control plane (future)**: RBAC, approvals, policy, reports, administration

## Security & Governance

- Role-based access control by function (SOC analyst, sysadmin, network admin, auditor)
- Mandatory approval for high-risk actions
- Immutable audit logging for all control and playbook runs
- Vault/KMS-backed credential storage only

## Initial Domain Model (MVP)

- `organizations`, `sites`
- `assets`, `asset_services`, `asset_software`, `asset_metrics`
- `security_events`, `incidents`, `incident_evidence`
- `automation_playbooks`, `automation_runs`
- `ai_recommendations`
- `users`, `roles`, `permissions`, `audit_logs`

## Live Dashboard Data Feeds

- KPI summary stream over websocket
- Incident timeline updates
- Asset health state transitions
- Top risky assets/users rollups
