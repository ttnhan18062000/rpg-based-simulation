---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260619-P0-CODE-INTEGRITY
phase: done
date: 2026-06-19
tags: [code-integrity, determinism, sort-tiebreaker, import-cycle, test-teardown, phase-0, p0-foundation]
---

# TCK-20260619-P0-CODE-INTEGRITY

## Title
P0-6 · Code Integrity Fixes — Sort tiebreaker, MovementPlanCache injection, test teardown contamination

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Three surgical code fixes found during audit D12/D14/D10 that each independently corrupt test reliability or replay determinism:
1. Missing kind.value tiebreaker in candidate sorts → non-determinism on score ties
2. `MovementPlanCache` constructed inside `core/state.py.__post_init__` → upward import through the most-imported file
3. Teardown mode contamination in `test_registry_bridge.py` and broken fixture in `test_phase2_knowledge_model_service.py` → 15 false cognition test failures

## Scope
**Fix 1 — Sort tiebreaker:**
- Added `kind.value` as secondary sort key in `ConversionOptionGenerator` and `PersonalityAwareSelector`
- `ConversionKind(str, Enum)` — `.value` is a string literal; alphabetical descending breaks score ties canonically

**Fix 2 — MovementPlanCache import removed:**
- Removed the 3-line lazy import block from `AuthoritativeState.__post_init__` (lines 1056–1058)
- `movement_cache: Any = field(default=None)` was already declared; engine callers already guard with `getattr(state, "movement_cache", None)`

**Fix 3 — Test teardown contamination:**
- `test_registry_bridge.py` teardown fixture: `seed_phase1_content(None)` → `seed_phase1_content(mode=RuntimeContentMode.LEGACY_FALLBACK)`
- `test_registry_bridge.py` two test bodies also called `seed_phase1_content(None)`: fixed to `seed_phase1_content(None, mode=RuntimeContentMode.LEGACY_FALLBACK)` (explicit no-repo, allowed mode)
- `test_phase2_knowledge_model_service.py` module fixture: same fix

## Out of Scope
- Broader import cycle refactoring beyond this one edge
- Full architecture guard for all state.py imports (separate standard ticket)
- Other test files with the same `seed_phase1_content(None)` pattern (pre-existing, tracked separately)

## Acceptance Criteria
- [x] ConversionOption sorts produce canonical ordering on tied scores
- [x] `pytest tests/unit/cognition/` passes with zero teardown-contamination failures (was 15)
- [x] `state.py` no longer imports from `src/engine/`
- [x] Parity ledger updated: SUB-371 (sort tiebreaker), INFRA-204 (import boundary)

## Related Tickets
- TCK-20260619-P0-DETERMINISM (companion: both affect replay determinism)

## Related Docs
- `docs/parity_ledger/substrate.yaml` (SUB-371)
- `docs/parity_ledger/infrastructure.yaml` (INFRA-204)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260618-AUDIT-EPIC/`

## Related Code Areas
- `src/domains/progression/generator.py:94`
- `src/domains/progression/selector.py:69`
- `src/core/state.py:1049` (`__post_init__`)
- `tests/unit/core/test_registry_bridge.py`
- `tests/unit/cognition/test_phase2_knowledge_model_service.py`

## Assumptions / Open Questions
None remaining.

## Implementation Notes
Fix 1 uses `kind.value` (not `entity_id`) because `ConversionOption` has no `entity_id` field; the kind string is the most natural canonical tiebreaker and is stable across runs.

Fix 2 is safe because all engine-side callers guard the cache access and kernel.py initializes it before first use.

Fix 3 root cause: passing explicit `None` as `catalog_repo` bypasses the `_sentinel` auto-discovery path and hits the forbidden-mode check with the default `CATALOG_WITH_COMPATIBILITY` mode. The fix uses `LEGACY_FALLBACK` which is allowed.

## Test Summary
- New: `tests/unit/engine/test_sort_tiebreaker.py` — 5 tests, all pass
- `tests/unit/cognition/test_phase2_knowledge_model_service.py` — 15 tests, 0 errors (was 15 errors)
- `tests/unit/core/test_registry_bridge.py` — 28 tests pass (was 2 failures + teardown errors per test)
- Unit suite: 2567 pass, 44 pre-existing failures (unchanged baseline)

## Files Changed
- `src/domains/progression/generator.py` — add `o.kind.value` tiebreaker
- `src/domains/progression/selector.py` — add `pair[0].kind.value` tiebreaker
- `src/core/state.py` — remove 3-line lazy import block from `__post_init__`
- `tests/unit/core/test_registry_bridge.py` — fix teardown fixture + 2 test bodies
- `tests/unit/cognition/test_phase2_knowledge_model_service.py` — fix module fixture
- `tests/unit/engine/test_sort_tiebreaker.py` — NEW (5 determinism tests)
- `docs/parity_ledger/substrate.yaml` — SUB-371 added
- `docs/parity_ledger/infrastructure.yaml` — INFRA-204 added

## Completion Summary
All three bugs fixed. 15 false cognition test failures resolved. Sort tiebreaker makes progression decisions deterministic on score ties. MovementPlanCache upward import eliminated. Parity ledger updated. Staging artifacts written.
