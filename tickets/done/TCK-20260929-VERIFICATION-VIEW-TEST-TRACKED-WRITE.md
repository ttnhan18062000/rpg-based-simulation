---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-VERIFICATION-VIEW-TEST-TRACKED-WRITE
phase: done
date: 2026-09-29
tags: [testing]
---

# TCK-20260929-VERIFICATION-VIEW-TEST-TRACKED-WRITE

## Title
Stop `test_make_target_generates_verification_view` rewriting the tracked mechanism verification view

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Running the fast tiers on a clean checkout modified the tracked
`docs/brainstorm/mechanism_verification_view.md`. Writer identified:
`tests/unit/tools/test_mechanism_registry.py::test_make_target_generates_verification_view` ran the real
`make mechanism-verification-view` (write mode) and then `--check`d the result, so the check could not fail
and hid that the committed view was already stale on `origin/main` (registry changed in #254 without
regenerating the view).

Child of `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY` (Epic A), criterion 4.

## Scope
- The test runs `make -n` (recipe printed, nothing written) and keeps the read-only `--check` against the real files.
- Regenerate the committed view once, deliberately, so the now-meaningful check passes.

## Out of Scope
- The other tracked-file writers found in the same run (`docs/REGISTRY.yaml`, `tickets/working_log.csv`;
  attributed to `tests/tools/test_done_checker_static.py` and `tests/tools/test_monitoring_consolidation.py`);
  reported to agent-working-design.
- The optional advisory guard.

## Acceptance Criteria
1. The view is byte-identical before and after running the mechanism-registry test files.
2. The test fails while the committed view is stale and passes after regeneration.

## Related Tickets
- `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY`

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §3

## Related Stored Artifacts
None.

## Related Code Areas
`tests/unit/tools/test_mechanism_registry.py`; `tools/mechanism_registry/generate_mechanism_verification_view.py` (read-only); `docs/brainstorm/mechanism_verification_view.md`.

## Assumptions / Open Questions
- Attribution of the two other writers is file-level only (hash before/after per file).

## Implementation Notes
See Request Summary.

## Test Summary
Before regeneration the test failed (stale view). After regeneration the three mechanism-registry test
files give 113 passed and the view's sha256 is unchanged across the run (`bbf4043c750f`).

## Files Changed
`tests/unit/tools/test_mechanism_registry.py`; `docs/brainstorm/mechanism_verification_view.md` (regenerated from the registry).

## Completion Summary
Writer was test_make_target_generates_verification_view running the real make target. Replaced with make -n plus the read-only --check, and regenerated the stale committed view. Other tracked-file writers found (docs/REGISTRY.yaml, tickets/working_log.csv, agent-monitoring shards; tests/tools/test_done_checker_static.py and test_monitoring_consolidation.py) are out of scope and reported to agent-working-design. Consequence for other work: `test_make_target_generates_verification_view` is now a real staleness check, so any change to `registries/mechanisms.yaml` must regenerate the view (`make mechanism-verification-view`) in the same change or the fast suite fails. Previously the test regenerated the view silently, which is how it went stale after #254. Gate note: the bare done_checker_static CLI reports [precheck] and docs_to_update_coverage FAILs after closure; these are known false positives tracked in TCK-20260929-DONE-CHECKER-POST-CLOSURE-FALSE-FAILS. `--part finalize` passes.
