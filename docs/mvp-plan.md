# SentinelOps AI MVP Plan

## Phase 1: Core Monitoring (Implemented foundation)

- [x] Architecture and module definitions
- [x] API skeleton for assets/incidents/playbooks
- [x] Websocket live status feed
- [x] Containerized local dev stack
- [ ] Persistent database models and migrations
- [ ] Authentication and RBAC

## Phase 2: Network + Device Monitoring

- [ ] SNMP collector service
- [ ] Router/switch/camera/printer adapters
- [ ] Network topology graph APIs
- [ ] Unknown device detection rule

## Phase 3: Security Layer

- [ ] Wazuh integration
- [ ] osquery collection + query broker
- [ ] Vulnerability ingestion (OpenVAS/Nmap)
- [ ] File integrity and failed-login detections

## Phase 4: Automation and Controlled Response

- [ ] Action adapters (service restart, IP block, backup trigger)
- [ ] Approval workflow for risky actions
- [ ] Incident-linked playbook execution
- [ ] Full audit chain and evidence snapshots

## Phase 5: AI SOC Copilot

- [ ] AI incident summaries
- [ ] AI risk forecast service
- [ ] Root cause assistant queries
- [ ] AI-generated playbook drafts (human approval required)
