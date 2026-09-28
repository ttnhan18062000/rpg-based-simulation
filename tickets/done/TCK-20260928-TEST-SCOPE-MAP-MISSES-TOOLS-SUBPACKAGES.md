---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260928-TEST-SCOPE-MAP-MISSES-TOOLS-SUBPACKAGES
phase: done
date: 2026-09-28
tags: [process-improvement]
---

# TCK-20260928-TEST-SCOPE-MAP-MISSES-TOOLS-SUBPACKAGES

## Title

`expected_test_dirs_for()` returns None for `tools/delivery/`, `tools/mechanism_registry/`,
`tools/semantic_control_plane/` and `tools/perf/`, so the test-scope gate requires nothing for
changes there.

## Status

DONE

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

- Re-verified each of the four subdirs' sole test owner directly against this branch's tree
  before committing (Scope item 1's instruction), not just trusting the survey table:
  `tools/delivery/` → 6 real matches in `tests/tools/`; `tools/mechanism_registry/` and
  `tools/semantic_control_plane/` → both confirmed sole-owned by `tests/unit/tools/` (several
  files reference both subdirs, which is fine since they map to the same target); `tools/perf/`
  → confirmed sole-owned by `tests/static/test_no_hardcoded_venv_interpreter_path.py` (a naive
  grep for `tools[./]perf` also matched `tests.tools.perf_assertions` imports inside
  `tests/perf/*.py` — false positives from the unrelated `tests/tools/perf_assertions.py` module;
  excluded after checking the actual match context).
- Added `_TOOLS_SUBDIR_EXPLICIT_MAP` in `tools/gate_checks/test_scope_coverage_static.py`,
  checked before the flat-`tools/*.py`/`agent-monitoring`/`gate_checks` fallback, so none of the
  four collide with the existing rules.
- Mirrored the same four lines into `.claude/agents/test-scoper.md`'s Test Directory Map, with an
  explicit note that its existing same-name-directory fallback does NOT apply to these four (the
  exact bug Scope item 3 called out: that fallback would have sent `mechanism_registry/` and
  `semantic_control_plane/` to `tests/tools/`, the wrong owner).
- Did not change the None-fails-closed policy for unmapped subdirs (Out of Scope item 1) —
  `tools/eval/`, `tools/search/`, `tools/hooks/` still correctly return `None` (no `.py` modules).

## Test Summary

- `pytest tests/tools/test_test_scope_coverage_static.py -v` — 21 passed (4 new parametrized
  cases for the explicit map, 1 new case confirming an unmapped subdir still returns `None`).
- Direct verification of AC1: `expected_test_dirs_for()` returns the correct owner for a
  representative path in each of the four subdirs.
- Direct verification of AC2: `check_test_scope_coverage(["tools/delivery/pr_render.py"],
  "pytest tests/tools/test_delivery_pr_render.py")` → FAIL;
  `check_test_scope_coverage(["tools/delivery/pr_render.py"], "pytest tests/tools/")` → PASS.
- `pytest tests/tools/` (bare directory, per project rule) — 3145 passed, 25 skipped, 28
  deselected, 1 xfailed, 2 pre-existing failures unrelated to this change and already present on
  `origin/main` (see the sibling ticket `TCK-20260928-CLOSED-TICKETS-RESURRECTED-INTO-TODOS`'s
  Test Summary for detail — same batch, same run).

## Files Changed

- `tools/gate_checks/test_scope_coverage_static.py` — new `_TOOLS_SUBDIR_EXPLICIT_MAP` and lookup
  in `expected_test_dirs_for()`.
- `tests/tools/test_test_scope_coverage_static.py` — new parametrized test for the four mappings,
  new test confirming an unmapped subdir still returns `None`.
- `.claude/agents/test-scoper.md` — four new lines in the `tools/` Test Directory Map, plus a note
  that the same-name-directory fallback doesn't apply to them.
- `docs/REGISTRY.yaml` — regenerated (`make docs-registry`) to reflect this batch's tickets/
  changes; no manual edits.

## Completion Summary

All 3 acceptance criteria met. `tools/delivery/`, `tools/mechanism_registry/`,
`tools/semantic_control_plane/`, and `tools/perf/` now each have a required test directory in the
static gate check, matching each one's actual sole test owner re-verified directly against this
branch's tree. `test-scoper.md`'s own map was updated in the same commit so the agent and the
gate agree — without that, the agent's existing directory-name-guessing fallback would have sent
two of the four subdirs to the wrong directory, which the new gate rule would then have blocked.
No known material gap left unstated.
