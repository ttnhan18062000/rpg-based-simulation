---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260902-HOTFIX-TEST-SCOPE-COVERAGE-AI-SYSTEMS-ALLOWLIST-GAP
phase: open
date: 2026-09-02
tags: []
---

# TCK-20260902-HOTFIX-TEST-SCOPE-COVERAGE-AI-SYSTEMS-ALLOWLIST-GAP

## Title
test_scope_coverage_static.py's src/ subsystem allowlist doesn't recognize src/ai/ or src/systems/

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`tools/gate_checks/test_scope_coverage_static.py`'s `expected_test_dirs_for()` maps a changed
`src/` file to its expected owning test directory via a `_SRC_UNIT_SUBSYSTEMS` allowlist
(around lines 80-84). That allowlist does not include `"ai"` or `"systems"` as recognized `src/`
subsystems, so any changed file under `src/ai/` or `src/systems/` maps to `None` — the check
treats this as "not this check's concern" rather than flagging a real coverage gap. Found during
TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE's Test phase: both of that ticket's changed `src/`
files (`src/ai/coming_of_age.py`, `src/systems/lifecycle_systems/lifecycle.py`) silently fell
through this gap, and the structural backstop's `[]` (zero-FAIL) result was not an active
confirmation of coverage — real coverage assurance had to come from a manual cross-cutting grep
sweep instead. This is a real, silent blind spot in a gate meant to catch missed test-directory
coverage, not just for this one ticket but for every future ticket touching `src/ai/` or
`src/systems/`.

## Scope
- Add `"ai"` and `"systems"` (and audit for any other real `src/` top-level subsystem directories
  missing from the allowlist) to `_SRC_UNIT_SUBSYSTEMS` in
  `tools/gate_checks/test_scope_coverage_static.py`, mapping each to its correct owning
  `tests/unit/<subsystem>/` directory (confirm the real directory name first —
  `src/systems/lifecycle_systems/lifecycle.py` maps to `tests/unit/progression/` and
  `tests/unit/strategic/` in practice, not a literal `tests/unit/systems/`, so this needs a real
  mapping decision, not a mechanical 1:1 rename).
- Re-run the check's own test suite (if any) plus a real changed-file case for each newly-added
  subsystem to confirm it now produces a correct expected-dir list instead of `None`.

## Out of Scope
- Any change to the actual test scoping behavior of `test-scoper` agents themselves — this ticket
  only fixes the structural backstop script's allowlist.

## Acceptance Criteria
- [ ] `src/ai/` and `src/systems/` are recognized subsystems in `_SRC_UNIT_SUBSYSTEMS`, correctly
      mapped to their real owning test director(ies).
- [ ] A test case (new or existing) confirms a changed file under `src/ai/` or `src/systems/` no
      longer maps to `None`.
- [ ] Full audit of `_SRC_UNIT_SUBSYSTEMS` against the real `src/` top-level directory list
      confirms no other subsystem is missing.

## Related Tickets
- TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE (found and disclosed this gap during its own Test
  phase; real coverage was independently confirmed via manual cross-cutting grep instead of relying
  on this check)

## Related Docs
- (none directly; tool docstring is self-documenting)

## Related Stored Artifacts
- stored_artifacts/TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE/ (Test phase findings)

## Related Code Areas
- tools/gate_checks/test_scope_coverage_static.py

## Assumptions / Open Questions
- The correct `tests/unit/<x>/` mapping for `src/systems/` is not a clean 1:1 (its subpackages
  span multiple existing test directories: `tests/unit/progression/`, `tests/unit/strategic/`,
  `tests/unit/world/`, etc., depending on which `src/systems/*_systems/` subpackage is touched) —
  implementation should investigate the real subpackage-to-test-directory mapping before writing
  the allowlist entry, not assume a single directory.

## Implementation Notes
(fill in during implementation)

## Test Summary
(fill in during implementation)

## Files Changed
(fill in during implementation)

## Completion Summary
(fill in during implementation)
