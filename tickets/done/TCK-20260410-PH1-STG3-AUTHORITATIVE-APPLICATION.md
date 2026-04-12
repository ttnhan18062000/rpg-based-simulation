# Ticket TCK-20260410-PH1-STG3-AUTHORITATIVE-APPLICATION
## Phase 1 Stage 3: Authoritative Application

### Request Summary
Implementation of the authoritative update pipeline for strategic state mutations.

### Scope
- [x] Defined `StrategicUpdate` intent model in `src/actions/base.py`.
- [x] Implemented authoritative dispatch in `ActionSystem._apply_updates`.
- [x] Developed deterministic merge logic for directives, projects, concerns, obligations, and contracts in `src/systems/gameplay/action_system.py`.
- [x] Enforced ID-based replacement to prevent duplicate records.

### Acceptance Criteria
- [x] Strategic mutations are processed only through the authoritative action pipeline.
- [x] Merging logic handle adds/updates/removals correctly by ID.

### Status
DONE
