---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261026-VALIDATE-SPLIT-GLOBS-EXPANDED-ONCE
phase: done
date: 2026-10-26
tags: [process-improvement]
---

# TCK-20261026-VALIDATE-SPLIT-GLOBS-EXPANDED-ONCE

## Title
`tools.sessions.validate` expands each ownership-split glob once, not once per shared file

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found running the full `tests/tools` suite for the graphify and card-fold batch (2026-10-26): `test_real_registry_validates`, `test_committed_files_have_no_drift`, `test_row1_the_roster_validates_with_the_five_twins` and `test_cli_runs...` hit the 60 s `--resource-budget medium` limit. `python -m tools.sessions.validate` took 50 s unprofiled and 235 s under cProfile: `_covered_by_split` called `_files(root, p)` for every shared file, so each split glob was re-expanded about 1,500 times over 18,452 tracked files (pathlib `relative_to` dominated).

## Scope
`tools/sessions/validate.py`: `_check_ownership` keeps one dict of expanded split globs and passes it to `_covered_by_split`. No change to findings.

## Out of Scope
- `tests/tools/test_wall_clock_inventory.py::test_cli_runs_are_byte_identical_and_do_not_import_src`, which parses all of `src/` twice and reaches 60 s on a loaded host without touching the session code.

## Acceptance Criteria
1. `python -m tools.sessions.validate` reports the same findings (0 on main) and runs in seconds.
2. A test bounds the number of glob expansions by the owns patterns plus the distinct split paths.

## Related Tickets
- TCK-20261021-ROLE-CARD-FOLDS-SCATTERED-OWNED-FILES-TO-A-COUNT (the batch that exposed it)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
- `tools/sessions/validate.py`, `tests/tools/test_session_roster.py`

## Assumptions / Open Questions
None.

## Implementation Notes
The cache lives for one `_check_ownership` call (a dict passed down), not module level, so tests that create files under a temporary root and validate twice never see stale glob results.

## Test Summary
`python -m tools.sessions.validate`: 50 s before, 1.3 s after, same output (0 findings, 32 roles). The three session tests that timed out pass. New `test_validation_expands_each_glob_once_not_once_per_shared_file`.

## Files Changed
tools/sessions/validate.py, tests/tools/test_session_roster.py

## Completion Summary
Validation no longer scales with files times shared files; the split globs are expanded once.
