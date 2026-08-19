---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT
phase: open
date: 2026-08-19
tags: [testing]
---

# TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT

## Title
Split src/lab/workflows.py (2,695 lines, 9 pipeline-stage classes) into one file per workflow

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
`src/lab/workflows.py` is the single largest file in `src/` (2,695 lines) — item 1 of
`TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC`, extracted into its own ticket once concretely
investigated. AST-level structural parsing (no full-file read) confirms it holds 8
milestone-numbered (M96-M102 + Revert), independently-sized (104-507 line) workflow classes
forming a sequential pipeline (Generate → Prepare → Register → Compact → Investigate → Propose →
Update → Revert) plus one shared helper function — a "9 stages in one file" organization smell,
not a god-class. Mechanical, low-risk split.

## Scope
Full investigation and step-by-step plan are in `staging_artifacts/` for this ticket. Concrete
scope:
- Convert `src/lab/workflows.py` into a `src/lab/workflows/` package, one file per class (see
  plan.md for exact target layout).
- `src/lab/workflows/__init__.py` re-exports every class so all 10 existing import sites
  (`src/lab/__init__.py` + 9 test files) continue to work unchanged.
- Move the shared `safe_path_resolution()` helper to its own module (used by `src/lab/audit.py`
  too, not workflow-specific).
- Delete the original flat file once the package fully replaces it.

## Out of Scope
- Any behavioral change to the 9 workflow classes.
- Renaming any public class or changing its public API.

## Acceptance Criteria
- [ ] `src/lab/workflows.py` no longer exists as a single 2,695-line file.
- [ ] Every existing import of the 9 classes (10 call sites) still resolves unchanged — zero
      call-site edits required.
- [ ] Pre-split and post-split `tests/integration/lab_agent` + `tests/unit/lab_agent` pass/fail
      counts match exactly.

## Related Tickets
- TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC (item 1 extracted from here; epic remains open
  for its other 2 items — pipeline.py/tactical.py coverage verification, tests/helpers/
  under-utilization; item 2, the observability/mining/ naming investigation, was resolved
  directly within the epic itself rather than spun into a separate ticket — see that epic's
  Status update)
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic of the wider audit line)

## Related Docs
- docs/audits/D24_codebase_health_observatory.md (§D, §F — original source finding)
- docs/plans/codebase_navigability_hygiene_epic.md

## Related Stored Artifacts
staging_artifacts/TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT/

## Related Code Areas
- src/lab/workflows.py
- src/lab/__init__.py
- src/lab/audit.py
- tests/integration/lab_agent/, tests/unit/lab_agent/

## Assumptions / Open Questions
- Whether any workflow class has a module-level import or private helper beyond
  `safe_path_resolution()` that's shared with another workflow class (not just imported from
  elsewhere) wasn't fully ruled out — investigation.md's AST parse covers class/function
  signatures, not full import-statement bodies; a final check before splitting is prudent.

## Implementation Notes
(pending — implementation by a separate agent, per this ticket's own scope)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
