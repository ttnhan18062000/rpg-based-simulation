---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260825-HOTFIX-CI-BASELINE-DRIFT-MAKEFILE-ARTIFACT-TYPE
phase: done
date: 2026-08-25
tags: [frontmatter, testing]
---

# TCK-20260825-HOTFIX-CI-BASELINE-DRIFT-MAKEFILE-ARTIFACT-TYPE

## Title
Update two pinned-baseline anti-drift tests that PR #76's own legitimate changes caused to drift

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
PR #76's own CI run (job "API / tools / logging") failed with 2 real, non-flaky test failures,
both caused by this session's own already-justified changes tripping a pinned-baseline
anti-drift test whose job is exactly to force a deliberate acknowledgment on change, not to
forbid change forever:
1. `tests/tools/test_dashboard_makefile_targets.py::test_existing_targets_unmodified` --
   `TCK-20260825-HOTFIX-MAKEFILE-DEV-LIVE-MAP-DOC`'s `make dev` help-text/echo update (adding a
   line pointing at the live map) tripped this snapshot, which was captured for a different,
   already-closed ticket (`TCK-20260716-AGENTOPS-BUILD-SERVE`)'s own AC #1 ("existing targets
   unmodified" during THAT ticket's implementation window) -- not a permanent freeze on the
   Makefile.
2. `tests/tools/test_validate_frontmatter.py::TestEnumAntiDrift::test_enum_values_artifact_type`
   -- `TCK-20260821-LIVE-MAP-PERF-VALIDATION`'s Verify phase (round 1) legitimately extended
   `tools/validate_frontmatter.py`'s `ARTIFACT_TYPE_VALUES` from `{investigation, plan,
   test_plan}` to add `report` (the first `staging_artifacts/` deliverable for a
   measurement-and-reporting-only ticket), independently re-verified twice more in that ticket's
   own Verify rounds. This anti-drift test's job is to catch exactly this kind of enum change and
   force a conscious update, not to reject it.

## Scope
- Update `test_dashboard_makefile_targets.py`'s `_EXISTING_RECIPE_SNAPSHOT["dev"]` to match the
  real, intentional `make dev` recipe as of `TCK-20260825-HOTFIX-MAKEFILE-DEV-LIVE-MAP-DOC`.
- Update `test_validate_frontmatter.py::TestEnumAntiDrift::test_enum_values_artifact_type` to
  assert the real, intentional `ARTIFACT_TYPE_VALUES` set including `"report"`.

## Out of Scope
- Any other CI job or finding -- the other 10 jobs on PR #76's run were green.
- Reverting either underlying change (both are real, already-justified, already-tested
  deliverables from this same PR) -- the fix is updating the baseline, not the source.
- Adding a frontend/UI CI job -- flagged separately to the user as a genuine, pre-existing gap
  (CI has zero frontend/vitest/npm coverage today), not fixed as part of this hotfix.

## Acceptance Criteria
- [x] `test_dashboard_makefile_targets.py::test_existing_targets_unmodified` passes with the real
      current `make dev` recipe
- [x] `test_validate_frontmatter.py::TestEnumAntiDrift::test_enum_values_artifact_type` passes
      with the real current `ARTIFACT_TYPE_VALUES`
- [x] No other test in either file regressed (full-file re-run, not just the two fixed tests)

## Related Tickets
- TCK-20260825-HOTFIX-MAKEFILE-DEV-LIVE-MAP-DOC (source of the Makefile drift)
- TCK-20260821-LIVE-MAP-PERF-VALIDATION (source of the artifact_type enum drift, via its Verify
  round 1)

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- tests/tools/test_dashboard_makefile_targets.py
- tests/tools/test_validate_frontmatter.py

## Assumptions / Open Questions
None.

## Implementation Notes
Found via PR #76's own CI run (`gh api .../jobs/97664682180/logs`, job "API / tools / logging"),
not discovered locally -- neither test was in this session's own scoped-test runs for the tickets
that caused the drift, since those tickets correctly scoped their own test runs narrowly rather
than running the full suite (per CLAUDE.md's Testing Rule). This is exactly the kind of gap CI's
full-suite run exists to catch. Both fixes are one-line baseline updates with no logic change.

## Test Summary
`.venv/bin/python3 -m pytest tests/tools/test_dashboard_makefile_targets.py
tests/tools/test_validate_frontmatter.py -q` -- **86/86 passed** (both previously-failing tests
now pass; full-file re-run confirms no other regression).

## Files Changed
- `tests/tools/test_dashboard_makefile_targets.py` -- `_EXISTING_RECIPE_SNAPSHOT["dev"]` updated
  to include the new echo line.
- `tests/tools/test_validate_frontmatter.py` -- `test_enum_values_artifact_type` updated to
  include `"report"`.

## Completion Summary
Both pinned-baseline anti-drift tests updated to reflect PR #76's own already-justified changes
(Makefile live-map doc update, `report` artifact_type addition), found via the PR's real CI run
rather than assumed. 86/86 tests passing in both affected files after the fix.
