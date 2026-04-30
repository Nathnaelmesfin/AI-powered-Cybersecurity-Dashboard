from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_permission, require_token
from app.schemas.domain import (
    Asset,
    AssetCreate,
    AuditLog,
    Incident,
    IncidentCreate,
    Playbook,
    PlaybookRunResult,
    TelemetryEvent,
    TelemetryEventCreate,
    UserContext,
)
from app.services import store

router = APIRouter(prefix="/api/v1", tags=["sentinelops"], dependencies=[Depends(require_token)])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    return store.summary(db)


@router.get("/assets", response_model=list[Asset])
def list_assets(db: Session = Depends(get_db), _: UserContext = Depends(require_permission("assets.read"))) -> list[Asset]:
    return store.list_assets(db)


@router.post("/assets", response_model=Asset)
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    ctx: Annotated[UserContext, Depends(require_permission("assets.write"))] = None,
) -> Asset:
    return store.add_asset(db, payload, actor=ctx.username)


@router.get("/incidents", response_model=list[Incident])
def list_incidents(db: Session = Depends(get_db), _: UserContext = Depends(require_permission("incidents.read"))) -> list[Incident]:
    return store.list_incidents(db)


@router.post("/incidents", response_model=Incident)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    ctx: Annotated[UserContext, Depends(require_permission("incidents.write"))] = None,
) -> Incident:
    return store.add_incident(db, payload, actor=ctx.username)


@router.post("/telemetry", response_model=TelemetryEvent)
def ingest_telemetry(
    payload: TelemetryEventCreate,
    db: Session = Depends(get_db),
    ctx: Annotated[UserContext, Depends(require_permission("telemetry.ingest"))] = None,
) -> TelemetryEvent:
    return store.ingest_telemetry(db, payload, actor=ctx.username)


@router.get("/telemetry", response_model=list[TelemetryEvent])
def get_telemetry(limit: int = 100, db: Session = Depends(get_db), _: UserContext = Depends(require_permission("telemetry.read"))) -> list[TelemetryEvent]:
    return store.list_telemetry(db, limit)


@router.get("/playbooks", response_model=list[Playbook])
def list_playbooks() -> list[Playbook]:
    return store.list_playbooks()


@router.post("/playbooks/{playbook_id}/run", response_model=PlaybookRunResult)
def run_playbook(
    playbook_id: int,
    dry_run: bool = True,
    db: Session = Depends(get_db),
    ctx: Annotated[UserContext, Depends(require_permission("playbooks.run"))] = None,
) -> PlaybookRunResult:
    return store.run_playbook(db=db, playbook_id=playbook_id, ctx=ctx, dry_run=dry_run)


@router.post("/playbook-runs/{run_id}/approve", response_model=PlaybookRunResult)
def approve_playbook_run(
    run_id: str,
    db: Session = Depends(get_db),
    ctx: Annotated[UserContext, Depends(require_permission("playbooks.approve"))] = None,
) -> PlaybookRunResult:
    return store.approve_playbook_run(db=db, run_id=run_id, ctx=ctx)


@router.get("/audit-logs", response_model=list[AuditLog])
def get_audit_logs(limit: int = 100, db: Session = Depends(get_db), _: UserContext = Depends(require_permission("audit.read"))) -> list[AuditLog]:
    return store.list_audit_logs(db, limit=limit)
