---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260928-TEST-SCOPE-MAP-MISSES-TOOLS-SUBPACKAGES
phase: open
date: 2026-09-28
tags: [process-improvement]
---

# TCK-20260928-TEST-SCOPE-MAP-MISSES-TOOLS-SUBPACKAGES

## Title

`expected_test_dirs_for()` returns None for `tools/delivery/`, `tools/mechanism_registry/`,
`tools/semantic_control_plane/` and `tools/perf/`, so the test-scope gate requires nothing for
changes there.

## Status

OPEN

## Tier

hotfix

## Type

bug

## Priority

P2

## Request Summary

`tools/gate_checks/test_scope_coverage_static.py::expected_test_dirs_for()` maps `tools/` paths
through three rules: `_TOOLS_SUBDIR_MIRROR_PREFIXES`, the `agent-monitoring/` + `gate_checks/`
rule, and top-level `tools/*.py`. Every other `tools/<subdir>/` returns None, which the
docstring defines as "not this check's concern". Found while reviewing #252: a
`tools/delivery/pr_render.py` change had no required test directory, although its tests live in
`tests/tools/test_delivery_*.py`.

Survey of `origin/main` @ `9bcae32c5`, counting test files that reference `tools[./]<subdir>`:

| Unmapped subdir | Modules | Real test owner(s) |
|---|---|---|
| `tools/delivery/` | 5 | `tests/tools/` (6 files) — sole owner |
| `tools/mechanism_registry/` | 20 | `tests/unit/tools/` (21 files) — sole owner |
| `tools/semantic_control_plane/` | 4 | `tests/unit/tools/` (4 files) — sole owner |
| `tools/perf/` | 1 | `tests/static/` (1 file) — sole owner |
| `tools/eval/`, `tools/search/`, `tools/hooks/` | 0 `.py` modules | n/a (no Python to map) |

Each of the four has one clean owning directory, unlike the deliberately unmapped `src/ai` and
`src/systems`, whose rationale comment is in the same module. Leaving them unmapped means
the done-checker test-scope condition passes a cherry-picked command for these subpackages.
That is the exact shape the check exists to catch.

## Scope

1. Map the four subpackages in `expected_test_dirs_for()`:
   `tools/delivery/` → `tests/tools/`, `tools/mechanism_registry/` → `tests/unit/tools/`,
   `tools/semantic_control_plane/` → `tests/unit/tools/`, `tools/perf/` → `tests/static/`.
   Before committing, re-verify each owner against the tree on the implementation branch, since
   test locations may have moved since this survey.
2. Extend `tests/tools/test_test_scope_coverage_static.py` with one parametrized case per mapping,
   plus a case confirming an unknown `tools/<new_subdir>/x.py` still returns None, so the
   None-means-unknown contract holds.
3. Add the same four lines to the `tools/` Test Directory Map in `.claude/agents/test-scoper.md`, so
   the agent and the gate agree. This is required. The map's current fallback ("check for a same-name
   directory under `tests/` before falling back to `tests/tools/`") sends `mechanism_registry/`
   and `semantic_control_plane/` to `tests/tools/`. Their real owner is `tests/unit/tools/`,
   so the agent would pick the wrong directory and the new gate rule would then block it.

## Out of Scope

- Making None fail closed for unknown `tools/` subdirs. That is a policy change, and it would
  have flagged `eval/`, `search/` and `hooks/`, which have no Python modules.
- Remapping `src/ai` / `src/systems` (deliberately unmapped, documented in-module).

## Acceptance Criteria

- AC1: `expected_test_dirs_for()` returns the owners above for a representative `.py` path in each
  of the four subdirs.
- AC2: `check_test_scope_coverage(["tools/delivery/pr_render.py"], "pytest tests/tools/test_delivery_pr_render.py")`
  returns FAIL, and returns PASS with `pytest tests/tools/`.
- AC3: `pytest tests/tools/` passes (bare directory).

## Related Tickets

- `TCK-20260902-HOTFIX-TEST-SCOPE-COVERAGE-AI-SYSTEMS-ALLOWLIST-GAP`: the same class for
  `src/`, resolved by documenting why those stay unmapped.
- `TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION` (#252): where the gap was noticed.

## Related Docs

- `.claude/agents/test-scoper.md` (Scoping Rules)

## Related Stored Artifacts

None.

## Related Code Areas

- `tools/gate_checks/test_scope_coverage_static.py`
- `tests/tools/test_test_scope_coverage_static.py`

## Assumptions / Open Questions

- The survey counted textual references, not import graphs. A test that imports a module
  indirectly would be missed, but that could only add owners, not remove the sole owner found.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
