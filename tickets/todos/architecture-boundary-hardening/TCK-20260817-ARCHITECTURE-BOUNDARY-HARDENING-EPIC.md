---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC
phase: open
date: 2026-08-17
tags: [testing, architecture]
---

# TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC

## Title
Upgrade weak substring-based import-boundary tests to AST; add missing domains/systems boundaries

## Status
EPIC_SCOPED

## Tier
epic

## Type
refactor

## Priority
P2

## Request Summary
Two architecture boundary tests (`test_api_read_model_guard.py`, `test_phase_domain_permissions.py`)
are genuinely strong, AST-based checks. Two more
(`test_phase18_import_boundaries.py`, `test_phase19_observability_boundaries.py`) are plain
substring-grep checks, defeatable via `importlib`, aliasing, or an indirect import chain. No
boundary test exists at all for `domains ↛ observability` or `systems ↛ engine` internals. The
fix reuses a pattern already proven in this repo — no new technique to introduce.

## Scope
- Scope-only epic: full findings and proposed remediation steps are in
  `docs/plans/architecture_boundary_hardening_epic.md`. Detailed, investigated child tickets are
  not created yet.
- When work begins: run `create-tickets` against a proposal document scoped to this epic's items
  (AST-ify the two weak tests, add the two missing boundary tests), producing investigated child
  tickets in `tickets/todos/architecture-boundary-hardening/`.

## Out of Scope
- Building a general machine-readable subsystem-ownership manifest for all 38 `src/` packages —
  a larger initiative than hardening 4 existing/missing boundary tests.
- The Tier-3→Tier-0 `docker-compose.yml` startup-dependency linter — a compose-file concern
  motivated by a different epic's finding (Epic A), needs a different mechanism, lower priority
  within this epic.

## Acceptance Criteria
- [ ] `docs/plans/architecture_boundary_hardening_epic.md` is reviewed and its scope confirmed accurate.
- [ ] Child tickets are created via `create-tickets` once this epic is chosen for action.
- [ ] This epic is not closed until its child tickets (once created) reach `tickets/done/`.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)
- TCK-20260817-DEAD-INFRA-REMOVAL-EPIC (motivates this epic's lower-priority compose-linter item)

## Related Docs
- docs/plans/architecture_boundary_hardening_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D24_codebase_health_observatory.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tests/architecture/test_api_read_model_guard.py
- tests/architecture/test_phase_domain_permissions.py
- tests/architecture/test_phase18_import_boundaries.py
- tests/architecture/test_phase19_observability_boundaries.py

## Assumptions / Open Questions
- Whether `domains ↛ observability` or `systems ↛ engine` violations currently exist wasn't
  checked in either source audit — this affects whether the new tests start red or green, and
  needs confirming before implementation.

## Implementation Notes
(pending — scope-only epic)

## Test Summary
(pending — no direct tests; each future child ticket will carry its own)

## Files Changed
(pending)

## Completion Summary
(pending)
