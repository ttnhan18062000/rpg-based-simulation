---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC
phase: open
date: 2026-08-17
tags: [testing, architecture]
---

# TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC

## Title
Split src/lab/workflows.py; investigate mining/ naming overlap; verify pipeline.py/tactical.py coverage

## Status
EPIC_SCOPED

## Tier
epic

## Type
refactor

## Priority
P3

## Request Summary
Four independent, low-risk navigability/discoverability items surfaced by the codebase health
audit: `src/lab/workflows.py` (2,694 LoC, single largest file in `src/`, 9 workflow classes) is a
mild file-organization smell; `src/observability/mining/` has three similarly-named orchestration
classes whose boundary is unclear from names alone (flagged Suspicious, not confirmed
duplicative); `tests/unit/domains/` vs. flat domains-subpackage test dirs is a naming
inconsistency that could mislead an agent into thinking coverage is missing when it isn't; and
`pipeline.py`/`tactical.py` (both top-5 by churn and centrality) have no exactly-named dedicated
unit test file, plausibly but not confirmed covered indirectly.

- Scope-only epic: full findings and proposed remediation steps are in
  `docs/plans/codebase_navigability_hygiene_epic.md`. Detailed, investigated child tickets are
  not created yet.
- **(2026-08-19)** Item 3 (`tests/unit/domains/` vs. flat domains-subpackage test-dir placement)
  extracted into its own standalone standard-tier ticket,
  `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING`, once the exact split (13 nested / 6 flat) was
  concretely verified — matching the pattern already used for this parent tree's other
  now-downgraded siblings. This epic's remaining scope is the other 3 items only.
- When work begins on the remaining 3 items: run `create-tickets` against a proposal document
  scoped to `src/lab/workflows.py` split, `mining/` targeted read, `pipeline.py`/`tactical.py`
  coverage verification (and `tests/helpers/` under-utilization), producing investigated child
  tickets in `tickets/todos/codebase-navigability-hygiene/`.

## Out of Scope
- Any consolidation of `src/observability/mining/`'s classes without first doing the targeted
  read this epic scopes.
- Writing new tests for `pipeline.py`/`tactical.py` unless the coverage-verification step
  confirms a real gap.

## Acceptance Criteria
- [ ] `docs/plans/codebase_navigability_hygiene_epic.md` is reviewed and its scope confirmed accurate.
- [ ] Child tickets are created via `create-tickets` once this epic is chosen for action.
- [ ] This epic is not closed until its child tickets (once created) reach `tickets/done/`.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)

## Related Docs
- docs/plans/codebase_navigability_hygiene_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D24_codebase_health_observatory.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/lab/workflows.py
- src/observability/mining/
- tests/unit/engine/ (pipeline.py/tactical.py coverage question)
- tests/helpers/

## Assumptions / Open Questions
- Whether `src/observability/mining/`'s three classes are genuinely distinct or partially
  duplicative is unconfirmed — needs a targeted read before any consolidation decision.
- Whether `tests/helpers/` under-utilization reflects hand-rolled duplication or invisible
  `conftest.py`-fixture reuse is unconfirmed.

## Implementation Notes
(pending — scope-only epic)

## Test Summary
(pending — no direct tests; each future child ticket will carry its own)

## Files Changed
(pending)

## Completion Summary
(pending)
