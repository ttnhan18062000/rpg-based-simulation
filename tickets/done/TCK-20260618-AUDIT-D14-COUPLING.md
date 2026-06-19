---
status: done
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260618-AUDIT-D14-COUPLING
phase: open
date: 2026-06-18
tags: [audit, coupling, domain-boundaries, architecture, imports]
---

# TCK-20260618-AUDIT-D14-COUPLING

## Title
D14 — Coupling Depth Audit

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Audit cross-layer and cross-domain import coupling in the codebase. Identify prohibited patterns, hidden upward dependencies, and tight couplings that create change-cascade risk.

## Scope
- Scan all domain packages for cross-domain imports (prohibited pattern)
- Check `core` for upward imports from `engine` or `domains`
- Check API layer for raw domain model exposure
- Map upper-layer (observability, api, lab) coupling to engine
- Identify structural god nodes

## Out of Scope
- Fixing violations
- Type safety (D13)
- Dead code (D11)

## Acceptance Criteria
- `docs/audits/D14_coupling_depth.md` written with scoring rubric
- `audit_dimensions.md` D14 row updated to `done`
- Working log entry appended
- Agent monitoring records written

## Related Tickets
- TCK-20260618-AUDIT-EPIC (parent)

## Related Docs
- `docs/simulation/domains/domain_ownership_map.md`
- `docs/audits/audit_dimensions.md`

## Related Stored Artifacts
- `staging_artifacts/TCK-20260618-AUDIT-D14/`

## Related Code Areas
- `src/domains/`
- `src/core/`
- `src/engine/`
- `src/api/`
- `src/observability/`

## Assumptions / Open Questions
- Scanner results cover all `.py` files in src/

## Implementation Notes
Scan results:
- Cross-domain violations: 1 (memory→time)
- core→engine lazy imports: 2 (state.py, updates.py)
- observability→engine: 4 files (3× Kernel, 1× WorldIndexService)
- api→engine: 3 imports in engine_manager.py
- API routes: ALL go through read_cache DTOs or StatePresenter — clean
- pipeline.py is the single engine→domain integration point (7 domain imports, clean)

## Test Summary
N/A

## Files Changed
- docs/audits/D14_coupling_depth.md (create)
- docs/audits/audit_dimensions.md (update)
- tickets/working_log.csv (append)
- agent-monitoring/runs.jsonl (append)
- agent-monitoring/events.jsonl (append)

## Completion Summary
D14 audit complete. Import scanner found 3 findings across entire src/. Architecture is clean: 13/14 domains have zero cross-domain imports; API routes all use DTOs; content layer is fully isolated. Top risk: core/state.py→engine.movement_cache upward lazy import (10/15) — AuthoritativeState should not construct engine-layer services. 5 follow-up tickets recommended (2 P1, 3 P2).
