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
OPEN

## Tier
standard

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
Full findings are in `docs/plans/architecture_boundary_hardening_epic.md`. Concrete scope, all
reusing the AST-visitor pattern `test_api_read_model_guard.py`/`test_phase_domain_permissions.py`
already establish:
- Rewrite `test_phase18_import_boundaries.py` and `test_phase19_observability_boundaries.py` from
  substring-grep to AST inspection.
- Add the two missing boundary tests: `domains ↛ observability` internals, `systems ↛ engine`
  internals.
- Lower priority within this ticket: a Tier-3→Tier-0 `docker-compose.yml` startup-dependency
  linter (motivated by Epic A's RabbitMQ finding) — a compose-file concern needing a different
  mechanism than an architecture test.

## Out of Scope
- Building a general machine-readable subsystem-ownership manifest for all 38 `src/` packages —
  a larger initiative than hardening 4 existing/missing boundary tests.
- The Tier-3→Tier-0 `docker-compose.yml` startup-dependency linter — a compose-file concern
  motivated by a different epic's finding (Epic A), needs a different mechanism, lower priority
  within this epic.

## Acceptance Criteria
- [ ] The two weak boundary tests use AST inspection, not substring matching.
- [ ] `domains ↛ observability` and `systems ↛ engine` each have an enforced boundary test.
- [ ] Each new/upgraded test is confirmed to actually fail against a deliberately-introduced
      violation (not just pass trivially because nothing violates it yet).

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
- **Downgraded from epic to standard tier (2026-08-18):** one of 10 sub-epics under
  `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`; four items mechanically reusing one already-
  proven in-repo pattern against a handful of test files — cohesive, one standard ticket.
  `staging_artifacts/TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC/` not yet created.

## Implementation Notes
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
