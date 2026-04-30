from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AssetEntity, AuditLogEntity, IncidentEntity, PlaybookRunEntity, RoleEntity, RolePermissionEntity, TelemetryEventEntity, UserEntity
from app.core.security import hash_password
from app.core.event_bus import publish_event
from app.services.correlation import process_telemetry_for_correlation
from app.schemas.domain import (
    Asset,
    AssetCreate,
    AuditLog,
    ExecutiveSummary,
    Incident,
    IncidentCreate,
    Playbook,
    PlaybookRunResult,
    Severity,
    TelemetryEvent,
    TelemetryEventCreate,
    UserContext,
)

PLAYBOOKS: list[Playbook] = [
    Playbook(id=1, name="Suspicious SSH Attack", trigger=">20 failed SSH logins in 5 minutes", risky=True, steps=["Create incident", "Enrich source IP", "Block IP in firewall", "Notify SOC", "Save evidence"]),
    Playbook(id=2, name="Odoo Service Down", trigger="Odoo down + Nginx 502", risky=False, steps=["Check service", "Inspect logs", "Check DB", "Restart service"]),
]


def seed_defaults(db: Session) -> None:
    if not db.scalar(select(RoleEntity.id).limit(1)):
        roles = [RoleEntity(name=r) for r in ["super_admin", "security_analyst", "system_admin", "network_admin", "auditor", "helpdesk", "ai_operator"]]
        db.add_all(roles)
        db.flush()

        matrix = {
            "assets.read": {"super_admin", "security_analyst", "system_admin", "network_admin", "auditor", "helpdesk"},
            "assets.write": {"super_admin", "system_admin", "network_admin"},
            "incidents.read": {"super_admin", "security_analyst", "system_admin", "network_admin", "auditor"},
            "incidents.write": {"super_admin", "security_analyst", "system_admin"},
            "playbooks.run": {"super_admin", "security_analyst", "system_admin", "network_admin", "ai_operator"},
            "playbooks.approve": {"super_admin", "security_analyst", "system_admin", "network_admin"},
            "audit.read": {"super_admin", "security_analyst", "auditor"},
            "telemetry.ingest": {"super_admin", "security_analyst", "system_admin", "network_admin"},
            "telemetry.read": {"super_admin", "security_analyst", "system_admin", "network_admin", "auditor"},
        }
        role_by_name = {r.name: r.id for r in roles}
        for action, role_names in matrix.items():
            for rn in role_names:
                db.add(RolePermissionEntity(role_id=role_by_name[rn], action=action))

        db.add(UserEntity(username="secops", role_id=roles[1].id, password_hash=hash_password("secops123")))

    if not db.scalar(select(AssetEntity.id).limit(1)):
        db.add_all([
            AssetEntity(name="odoo-prod-01", asset_type="server", risk_score=72, owner="Infra Team", location="HQ"),
            AssetEntity(name="branch-router-03", asset_type="router", risk_score=48, owner="Network Team", location="Branch 3"),
        ])
        db.add(IncidentEntity(title="Repeated SSH login failures", severity="high", asset_id=1, summary="Failed SSH attempts exceeded threshold."))

    db.commit()


def _audit(db: Session, actor: str, action: str, target: str, details: str = "") -> None:
    db.add(AuditLogEntity(actor=actor, action=action, target=target, details=details))
    db.commit()


def list_assets(db: Session) -> list[Asset]:
    return [Asset.model_validate(r, from_attributes=True) for r in db.scalars(select(AssetEntity).order_by(AssetEntity.id)).all()]


def add_asset(db: Session, payload: AssetCreate, actor: str) -> Asset:
    row = AssetEntity(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    _audit(db, actor, "asset.create", f"asset:{row.id}", f"name={row.name}")
    payload = Asset.model_validate(row, from_attributes=True)
    publish_event("asset_update", payload.model_dump())
    return payload


def list_incidents(db: Session) -> list[Incident]:
    return [Incident.model_validate(r, from_attributes=True) for r in db.scalars(select(IncidentEntity).order_by(IncidentEntity.id.desc())).all()]


def add_incident(db: Session, payload: IncidentCreate, actor: str) -> Incident:
    row = IncidentEntity(created_at=datetime.now(timezone.utc), **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    _audit(db, actor, "incident.create", f"incident:{row.id}", row.title)
    payload = Incident.model_validate(row, from_attributes=True)
    publish_event("incident_update", payload.model_dump(mode="json"))
    return payload


def list_playbooks() -> list[Playbook]:
    return PLAYBOOKS


def run_playbook(db: Session, playbook_id: int, ctx: UserContext, dry_run: bool = True) -> PlaybookRunResult:
    pb = next((p for p in PLAYBOOKS if p.id == playbook_id), None)
    if not pb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")

    requires_approval = pb.risky and not dry_run
    row = PlaybookRunEntity(
        run_id=str(uuid4()),
        playbook_id=playbook_id,
        mode="dry-run" if dry_run else "approved-execution",
        status="pending_approval" if requires_approval else "queued",
        requested_by=ctx.username,
        requires_approval=requires_approval,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    _audit(db, ctx.username, "playbook.run", f"playbook:{playbook_id}", f"run_id={row.run_id},status={row.status}")
    publish_event("playbook_run", {"run_id": row.run_id, "status": row.status, "playbook_id": row.playbook_id})
    return PlaybookRunResult.model_validate(row, from_attributes=True, strict=False)


def approve_playbook_run(db: Session, run_id: str, ctx: UserContext) -> PlaybookRunResult:
    row = db.scalar(select(PlaybookRunEntity).where(PlaybookRunEntity.run_id == run_id))
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    if not row.requires_approval:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Run does not require approval")
    row.approved_by = ctx.username
    row.status = "approved"
    db.commit()
    db.refresh(row)
    _audit(db, ctx.username, "playbook.approve", f"run:{row.run_id}")
    publish_event("playbook_run", {"run_id": row.run_id, "status": row.status, "playbook_id": row.playbook_id})
    return PlaybookRunResult.model_validate(row, from_attributes=True, strict=False)


def list_audit_logs(db: Session, limit: int = 100) -> list[AuditLog]:
    rows = db.scalars(select(AuditLogEntity).order_by(AuditLogEntity.id.desc()).limit(limit)).all()
    return [AuditLog.model_validate(r, from_attributes=True) for r in rows]


def summary(db: Session) -> ExecutiveSummary:
    incidents = list_incidents(db)
    assets = list_assets(db)
    return ExecutiveSummary(
        cyber_health_score=78,
        open_incidents=len([i for i in incidents if i.status == "open"]),
        critical_incidents=len([i for i in incidents if i.severity == Severity.critical and i.status == "open"]),
        offline_assets=len([a for a in assets if a.status != "online"]),
        vulnerabilities_open=27,
        failed_logins_last_hour=34,
        patch_compliance_percent=86.4,
    )


def ingest_telemetry(db: Session, payload: TelemetryEventCreate, actor: str) -> TelemetryEvent:
    row = TelemetryEventEntity(created_at=datetime.now(timezone.utc), **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    _audit(db, actor, "telemetry.ingest", f"telemetry:{row.id}", f"{row.source}:{row.event_type}")
    payload = TelemetryEvent.model_validate(row, from_attributes=True)
    publish_event("telemetry", payload.model_dump(mode="json"))
    process_telemetry_for_correlation(payload.source, payload.severity, payload.event_type)
    return payload


def list_telemetry(db: Session, limit: int = 100) -> list[TelemetryEvent]:
    rows = db.scalars(select(TelemetryEventEntity).order_by(TelemetryEventEntity.id.desc()).limit(limit)).all()
    return [TelemetryEvent.model_validate(r, from_attributes=True) for r in rows]
