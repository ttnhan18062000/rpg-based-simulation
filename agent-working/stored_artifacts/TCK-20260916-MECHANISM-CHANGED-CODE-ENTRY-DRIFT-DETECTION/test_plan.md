---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION
artifact_type: test_plan
tags: [architecture, schema, simulation-quality]
---

# Test Plan — TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION

## Normal flow
`check_drift()` reports a mechanism only when a cited file is in the changed set AND the
mechanism's own entry is unchanged — the two-condition core the whole tool exists for.

## Edge cases
- `implemented_by` entries are `path::Symbol` — only the path half must match a changed file path.
- Multiple cited files: only the changed subset is reported, others silently excluded.
- A mechanism with no `implemented_by` at all never produces a finding.
- `check_replacements()`'s own edge case: a first binding (old had none) is never reported as a
  replacement, only an existing citation actually changing value is.

## Failure modes / regression-prone paths
- **AC #3's two required controls** are the load-bearing tests:
  `test_positive_control_does_not_flag_when_entry_changed_too` (code + entry changed together,
  not flagged) and `test_negative_control_flags_code_changed_with_no_registry_change` (code
  changed, entry untouched, flagged).
- **Report-only guarantee**: `main()` exits 0 even when `git diff` itself fails to resolve the
  base ref (a shallow CI checkout missing `origin/main` is a real, expected case, not a crash).
- **SHA fragility avoided deliberately**: no test pins a specific commit SHA from this feature
  branch — see the investigation's own reasoning (squash-merge convention makes that timebomb-y).

## Coverage delivered
12 tests in `tests/unit/tools/test_mechanism_registry_changed_code_check.py`. Full
`tests/unit/tools/` suite: 241 passed.
