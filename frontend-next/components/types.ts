export type Summary = {
  cyber_health_score: number
  open_incidents: number
  critical_incidents: number
  offline_assets: number
  vulnerabilities_open: number
  failed_logins_last_hour: number
  patch_compliance_percent: number
}

export type Asset = { id: number; name: string; asset_type: string; status: string; risk_score: number; owner?: string; location?: string }
export type Incident = { id: number; title: string; severity: string; status: string; created_at: string; asset_id?: number; summary?: string }
export type Playbook = { id: number; name: string; trigger: string; risky: boolean; steps: string[] }
export type Telemetry = { id: number; source: string; event_type: string; severity: string; payload: string; created_at: string }
