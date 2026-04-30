from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AssetType(str, Enum):
    server = "server"
    endpoint = "endpoint"
    router = "router"
    switch = "switch"
    camera = "camera"
    printer = "printer"
    application = "application"
    database = "database"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Asset(BaseModel):
    id: int
    name: str
    asset_type: AssetType
    status: str = "online"
    risk_score: int = Field(default=0, ge=0, le=100)
    owner: str | None = None
    location: str | None = None


class AssetCreate(BaseModel):
    name: str
    asset_type: AssetType
    owner: str | None = None
    location: str | None = None


class Incident(BaseModel):
    id: int
    title: str
    severity: Severity
    status: str = "open"
    created_at: datetime
    asset_id: int | None = None
    summary: str | None = None


class IncidentCreate(BaseModel):
    title: str
    severity: Severity
    asset_id: int | None = None
    summary: str | None = None


class TelemetryEventCreate(BaseModel):
    source: str
    event_type: str
    severity: Severity
    payload: str


class TelemetryEvent(BaseModel):
    id: int
    source: str
    event_type: str
    severity: str
    payload: str
    created_at: datetime


class Playbook(BaseModel):
    id: int
    name: str
    trigger: str
    steps: list[str]
    risky: bool = False


class PlaybookRunResult(BaseModel):
    run_id: str
    playbook_id: int
    mode: str
    status: str
    note: str = ""
    requested_by: str
    requires_approval: bool
    approved_by: str | None = None


class ExecutiveSummary(BaseModel):
    cyber_health_score: int
    open_incidents: int
    critical_incidents: int
    offline_assets: int
    vulnerabilities_open: int
    failed_logins_last_hour: int
    patch_compliance_percent: float


class AuditLog(BaseModel):
    id: int
    actor: str
    action: str
    target: str
    details: str | None = None
    created_at: datetime


class UserContext(BaseModel):
    username: str
    role: str
