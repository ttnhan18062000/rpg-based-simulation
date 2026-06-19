---
status: open
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260619-P0-CODE-INTEGRITY
phase: open
date: 2026-06-19
tags: [code-integrity, determinism, sort-tiebreaker, import-cycle, test-teardown, phase-0, p0-foundation]
---

# TCK-20260619-P0-CODE-INTEGRITY

## Title
P0-6 · Code Integrity Fixes — Sort tiebreaker, MovementPlanCache injection, test teardown contamination

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Three surgical code fixes found during audit D12/D14/D10 that each independently corrupt test reliability or replay determinism:
1. Missing entity_id tiebreaker in candidate sorts → non-determinism on score ties
2. `MovementPlanCache` constructed inside `core/state.py.__post_init__` → upward import through the most-imported file
3. Teardown mode contamination in `test_registry_bridge.py` → 15 false cognition test failures

Source: `docs/audits/D12_code_quality.md` F1, `docs/audits/D14_test_coverage.md`, `docs/audits/D10_determinism.md` F1.

## Scope
**Fix 1 — Sort tiebreaker:**
- Add `entity_id` as secondary sort key in all candidate/route sorting in `src/systems/world_systems/generator.py` and any selector/scheduler that sorts by score
- Ensures identical scores produce identical ordering regardless of Python's sort stability and dict insertion order

**Fix 2 — MovementPlanCache injection:**
- Move `MovementPlanCache` construction out of `src/core/state.py.__post_init__`
- Inject via pipeline constructor or factory method; `state.py` should not import from the engine layer
- Check `src/engine/movement_cache.py:L13` (`MovementPlanKey`, `MovementPlanCache`) for the import chain

**Fix 3 — Test teardown contamination:**
- Fix teardown mode in `test_registry_bridge.py` so it doesn't leave global registry state affecting subsequent cognition tests
- Pattern: add explicit cleanup in test `teardown` / `@pytest.fixture` scope; or isolate registry state per test

## Out of Scope
- Broader import cycle refactoring beyond this one edge
- Full architecture guard for all state.py imports (separate standard ticket)
- Rewriting the test suite's global state strategy

## Acceptance Criteria
- 1000-tick replay hashes are stable across sort-tie scenarios (two entities with identical scores always produce the same ordering)
- `pytest tests/unit/cognition/` passes with zero teardown-contamination failures (currently 15 false failures)
- `state.py` does not import from `src/engine/` (checked via architecture guard test)

## Related Tickets
- TCK-20260619-P0-DETERMINISM (companion: both affect replay determinism)

## Related Docs
- `docs/audits/D12_code_quality.md`
- `docs/plans/long_term_development_roadmap.md` § P0-6
- `docs/core/state.md` (Fix 2: update to document the import boundary rule — `state.py` must not import from `src/engine/`; this is a non-obvious architectural constraint being enforced here)
- `docs/parity_ledger/substrate.yaml` (determinism — Fix 1 sort tiebreaker affects replay hash entries)
- `docs/parity_ledger/infrastructure.yaml` (Fix 2 MovementPlanCache injection may affect infra entries)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260618-AUDIT-EPIC/`

## Related Code Areas
- `src/systems/world_systems/generator.py:L20` (EntityGenerator — candidate sort)
- `src/engine/movement_cache.py:L13` (MovementPlanKey, MovementPlanCache)
- `src/core/state.py:L981` (AuthoritativeState.__post_init__ — injection point)
- `tests/unit/cognition/` (teardown contamination test files)
- `test_registry_bridge.py` (specific contamination source)

## Assumptions / Open Questions
- Which specific sorter in `generator.py` has the missing tiebreaker? Read the function and check for `key=lambda x: x.score` without `entity_id` secondary key
- Is there a `selector.py` or `scheduler.py` that also sorts? Run graphify query for all callers of sorts on score to be thorough

## Implementation Notes
Fix 1: change `sorted(candidates, key=lambda c: c.score, reverse=True)` to `sorted(candidates, key=lambda c: (c.score, c.entity_id), reverse=True)` (desc score, then asc entity_id for determinism). Fix 2: move `self.movement_plan_cache = MovementPlanCache()` to pipeline init or a factory that wraps state construction. Fix 3: add `@pytest.fixture(autouse=True)` scope cleanup or `yield`-based teardown in the test file.

After implementation: update `docs/parity_ledger/substrate.yaml` — set sort-tiebreaker determinism entry to `verified` with `test_path` pointing to the new tiebreaker test. Run `make knowledge-index-update` if any docs/ files are touched.

## Test Summary
- Run existing `tests/integration/kernel/test_replay_determinism.py::test_transaction_trace_determinism` — verify passes after Fix 1
- Run `pytest tests/unit/cognition/` — verify zero false failures after Fix 3
- New file `tests/unit/engine/test_sort_tiebreaker.py`:
  - `test_sort_tiebreaker_stable()` — create two candidates with identical scores, assert identical ordering across 100 sort calls
  - `test_sort_tiebreaker_deterministic_across_seeds()` — verify ordering matches between two identical-seed runs
- Run `tests/integration/kernel/test_determinism_suite.py` to confirm Fix 2 (MovementPlanCache injection) introduces no replay regressions

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
