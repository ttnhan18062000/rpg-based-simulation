---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260902-HOTFIX-TEST-SCOPE-COVERAGE-AI-SYSTEMS-ALLOWLIST-GAP
phase: done
date: 2026-09-02
tags: []
---

# TCK-20260902-HOTFIX-TEST-SCOPE-COVERAGE-AI-SYSTEMS-ALLOWLIST-GAP

## Title
test_scope_coverage_static.py's src/ subsystem allowlist doesn't recognize src/ai/ or src/systems/

## Status
DONE

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
**Revised after investigation (see Implementation Notes) — the originally-filed scope below assumed
a mechanical `_SRC_UNIT_SUBSYSTEMS` addition would close the gap; real evidence shows that would
create a *wrong* signal, not fix one, so the scope changed to match what the evidence actually
supports.**

Investigation confirmed `src/ai/` and `src/systems/*_systems/` have no reliable single owning
`tests/unit/<x>/` directory the way every other `_SRC_UNIT_SUBSYSTEMS` entry does — real test
coverage for both is genuinely scattered across many directories (e.g. `coming_of_age.py`'s own
test lives in `tests/unit/strategic/`, not `tests/unit/ai/`; `economy_systems/` is tested only
under `tests/integration/scenarios/` and `tests/architecture/`, not `tests/unit/` at all). Forcing
either into the flat 1:1 map would make the static backstop require the WRONG directory for many
real tickets, actively worse than the current silent `None`/skip.

Revised scope:
- Extend `tools/gate_checks/test_scope_coverage_static.py`'s module docstring/comment to explicitly
  document `ai` and `systems` as deliberately excluded from `_SRC_UNIT_SUBSYSTEMS`, with the
  investigation evidence, so a future reader sees a disclosed design boundary rather than an
  apparent oversight.
- Fix the real, confirmed gap this investigation found in `.claude/agents/test-scoper.md`: its
  cross-cutting-expansion trigger list (`## Scoping Rules`) already correctly names `src/systems/`
  as shared infrastructure requiring the grep-based expansion step, but omits `src/ai/` even
  though the evidence shows it is at least as scattered (real coverage found across
  `tests/unit/strategic/`, `tests/unit/ai/`, `tests/unit/ai/goals/`, `tests/unit/domains/adventure/`,
  `tests/unit/observability/`, and more). Add `src/ai/` to that trigger list.
- Add a regression test asserting `expected_test_dirs_for()` returns `None` for a representative
  `src/ai/` and `src/systems/*_systems/` file, with a comment citing this ticket — guards against
  someone "fixing" this back to a wrong flat mapping without re-reading the reasoning.

## Out of Scope
- Any change to the actual test scoping behavior of `test-scoper` agents themselves beyond the one
  documented cross-cutting-expansion trigger-list fix above.
- Building a real per-subpackage or content-based mapping mechanism for `src/systems/`'s 5
  sub-packages (`lifecycle_systems/`, `strategic_systems/`, `world_systems/`, `social_systems/`,
  `economy_systems/`) — each maps to a different, sometimes multi-directory set of real owners;
  designing a correct multi-directory-aware version of this check is a real, separate undertaking,
  not a hotfix-sized change, and is deferred.

## Acceptance Criteria
- [x] `_SRC_UNIT_SUBSYSTEMS`'s deliberate exclusion of `ai`/`systems` is documented in the module's
      own docstring with the real investigation evidence (not a silent gap).
- [x] `.claude/agents/test-scoper.md`'s cross-cutting-expansion trigger list includes `src/ai/`
      alongside `src/core/`, `src/systems/`, `src/engine/`.
- [x] A regression test confirms `expected_test_dirs_for()` returns `None` for both `src/ai/` and
      `src/systems/*_systems/` paths, with a comment explaining why this is correct, not a gap.

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
Investigation (real grep/import-scan evidence, not assumption) found the originally-filed scope
would have been actively wrong: `src/ai/coming_of_age.py`'s own real test lives in
`tests/unit/strategic/`, not `tests/unit/ai/`; `src/systems/economy_systems/` is tested only under
`tests/integration/scenarios/` and `tests/architecture/`, never `tests/unit/`; the other 4
`*_systems/` sub-packages each span a different multi-directory set (e.g. `lifecycle_systems/`
spans `tests/unit/world/`, `tests/unit/strategic/`, `tests/unit/progression/`). Unlike `domains/`
(also multi-subpackage, but safely mapped because `tests/unit/domains/<subpkg>/` nests every real
subpackage under one parent), `systems/` has no structural equivalent. Revised scope and ACs to
match (see `## Scope`) rather than implement a mapping known to be wrong. Implemented:
- `tools/gate_checks/test_scope_coverage_static.py`: extended the `_SRC_UNIT_SUBSYSTEMS` comment
  block with the full investigation evidence for why `ai`/`systems` are deliberately absent.
- `.claude/agents/test-scoper.md`: added `src/ai/` to the `## Scoping Rules` cross-cutting-
  expansion trigger list (alongside the already-correct `src/core/`, `src/systems/`,
  `src/engine/`), with a note explaining why the naming convention alone misses it.
- `tests/tools/test_test_scope_coverage_static.py`: new
  `test_ai_and_systems_deliberately_unmapped_not_a_silent_gap` asserting `expected_test_dirs_for()`
  returns `None` for `src/ai/coming_of_age.py`, `src/systems/lifecycle_systems/lifecycle.py`, and
  `src/systems/economy_systems/market.py` — guards against a future "fix" reintroducing the wrong
  mapping without re-reading the reasoning.

Out of scope, disclosed not fixed: a real per-subpackage or content-based multi-directory-aware
version of this static check for `src/systems/`'s 5 sub-packages — a genuine, separate undertaking
per the ticket's own `## Out of Scope`, not a hotfix-sized change.

## Test Summary
`/home/u24desktop/Working/venv/bin/python3 -m pytest tests/tools/test_test_scope_coverage_static.py -v`
— 16 passed, 0 failed (including the new regression test).
Full `tests/tools/` suite: 2569 passed, 5 failed, 47 skipped, 1 xfailed. All 5 failures
root-caused directly (not assumed) as pre-existing local-environment gaps unrelated to this
ticket's diff: `ModuleNotFoundError: No module named 'mcp'` (optional package not installed in
this venv) and `"error": "index not found"` (local knowledge-search index not built in this
environment) — both in `test_kgmcp_*`/`test_knowledge_gateway_*` files that have no import or
runtime relationship to `test_scope_coverage_static.py` or `test-scoper.md`. None of this ticket's
3 changed files appear anywhere in any failing test's traceback.

## Files Changed
- `tools/gate_checks/test_scope_coverage_static.py` (comment-only: documented the deliberate `ai`/`systems` exclusion with evidence)
- `.claude/agents/test-scoper.md` (added `src/ai/` to the cross-cutting-expansion trigger list)
- `tests/tools/test_test_scope_coverage_static.py` (new regression test)
- `tickets/done/TCK-20260902-HOTFIX-TEST-SCOPE-COVERAGE-AI-SYSTEMS-ALLOWLIST-GAP.md` (this file)

## Completion Summary
Investigated the gap this ticket was filed for and found the mechanical fix originally proposed
(add `ai`/`systems` to `_SRC_UNIT_SUBSYSTEMS` as flat 1:1 entries) would have created a wrong
signal, not fixed one — neither subsystem has a single reliable owning test directory the way
every other entry in that allowlist does. Revised scope to match the evidence: documented the
deliberate exclusion in the static checker's own comments, closed the one real gap the
investigation found (`src/ai/` missing from `test-scoper.md`'s cross-cutting-expansion trigger
list, even though `src/systems/` was already correctly listed there), and added a regression test
guarding against a future incorrect "fix." A genuine per-subpackage multi-directory mapping
mechanism for `src/systems/` is disclosed as a separate, deferred undertaking, not attempted here.
