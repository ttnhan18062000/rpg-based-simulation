---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260614-RESOURCE-BUDGET-GATE
phase: open
date: 2026-06-14
tags: [resource-safety, budget, subsystem, governor, performance]
---

# TCK-20260614-RESOURCE-BUDGET-GATE

## Title
Add per-subsystem resource budget gates with pressure state and degradation actions

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`OptimizationProfile` already has `movement_budget`, `strategic_budget`, and `CacheBudgetPolicy` but these cover only the engine/AI layer. Memory-sensitive subsystems — certification, replay, observability, cognition, hashing, worker pool, content loading — have no declared budgets and no pressure reporting. Add `SubsystemBudget` declarations per subsystem so the governor can degrade intelligently instead of waiting for `MemoryError`. Each subsystem reports current usage, budget, pressure state, and available degradation action.

## Scope
- Add `SubsystemBudget` dataclass in `src/config/optimization_profiles.py` (or new `src/engine/resource_budget.py`):
  - Fields: `subsystem: str`, `max_artifact_mb: float | None`, `max_pending_flushes: int | None`, `max_queue_items: int | None`, `max_tracked_entities: int | None`, `max_full_hashes_per_100_ticks: int | None`, `max_inflight_chunks: int | None`, `max_hot_path_loads: int | None`
- Add default `SubsystemBudget` instances for: `certification`, `replay`, `observability`, `cognition`, `hashing`, `worker`, `content`
- Add `SubsystemPressureReport` dataclass: `subsystem`, `current_usage`, `budget`, `pressure_state` (`OK`/`WARN`/`DEGRADED`), `degradation_action: str | None`
- Wire `observability` budget into `EventRecorder` — check `max_queue_items` against queue size at enqueue
- Wire `replay` budget into `ReplayManager` — check `max_pending_flushes` (estimated from executor queue depth or chunk counter)
- Wire `hashing` budget into `CanonicalStateHasher` — add a call counter; refuse full hash if over `max_full_hashes_per_100_ticks` budget (log warning, return last known hash instead)
- Each wired subsystem exposes a `pressure_report() -> SubsystemPressureReport` method
- Extend `OptimizationProfile` with `subsystem_budgets: dict[str, SubsystemBudget] = field(default_factory=dict)` — defaults overridable per profile

## Out of Scope
- Dashboard display (TCK-20260614-RESOURCE-DASHBOARD reads `pressure_report()`)
- Automatic governor degradation decisions (governor integration is a later epic)
- `DEBUG_REFERENCE` profile safety gate (separate concern)

## Acceptance Criteria
- `SubsystemBudget` and `SubsystemPressureReport` dataclasses exist
- Default budgets defined for all 7 subsystems
- `EventRecorder` checks `max_queue_items` at enqueue; returns `pressure_report()` with `WARN` when above 80%, `DEGRADED` at 100%
- `ReplayManager` exposes `pressure_report()` — at minimum reports chunk count vs. budget
- `CanonicalStateHasher` tracks full-hash call count per 100-tick window; `pressure_report()` reports WARN when over budget
- Tests: pressure_report returns correct state at varying usage levels for each wired subsystem
- `DEBUG_REFERENCE` profile is unaffected (its budgets are set to `None` = unlimited)

## Related Tickets
- TCK-20260614-RESOURCE-SAFETY-EPIC (parent)
- TCK-20260614-ARTIFACT-BUDGET-REG (complementary — artifact budgets; this ticket covers runtime subsystem budgets)
- TCK-20260614-RESOURCE-DASHBOARD (reads pressure_report() from each subsystem)
- TCK-20260614-HASH-SCHEDULER (builds on hashing budget gate added here)

## Related Docs
- `docs/engine/contracts/replay_contract.md` — Governor owns replay degradation decisions; the `pressure_report()` output from this ticket feeds the Governor's decision, but the degradation action string must be advisory (the Governor executes it, not the subsystem)
- `docs/engine/performance_contract.md`
- `docs/engine/kernel.md`
- `memory_features.md` (Feature 3)

## Related Code Areas
- `src/config/optimization_profiles.py:34` — `OptimizationProfile`, `CacheBudgetPolicy`
- `src/observability/event_recorder.py:18` — `EventRecorder`, `max_events` field
- `src/engine/replay_manager.py:20` — `ReplayManager`, `ThreadPoolExecutor`
- `src/engine/checkpoint.py:11` — `CanonicalStateHasher`
- `src/engine/kernel.py:34` — `Kernel` (owns all subsystems)

## Assumptions / Open Questions
- `ReplayManager` has no explicit `pending_flushes` counter — use `_current_chunk_id - _chunks_persisted` as an approximation, or add a simple `_inflight` count incremented on submit, decremented in callback
- Tick window for hashing rate: track with `(call_count, window_start_tick)` reset every 100 ticks

## Implementation Notes
- `pressure_report()` is non-blocking and read-only — no locks, no IO.
- Degradation action is a string description, not an auto-executed callback (execution is the governor's job).
- `SubsystemBudget` and `SubsystemPressureReport` placed in `src/config/optimization_profiles.py` per investigation §Best File Placement decision (avoids circular imports with engine layer).
- `BudgetedCanonicalHasher` is a new instance class wrapping static `CanonicalStateHasher` — no changes to existing static class (INFRA-119–130 unaffected).
- `ReplayManager._chunks_persisted` is a plain int (advisory accuracy acceptable for pressure signal, no lock needed).
- `EventRecorder.budget` parameter is independent of `max_events` (checks queue, not in-memory buffer).
- `DEBUG_REFERENCE` subsystem budgets are all-None (unlimited enforcement in parity baseline).
- All 7 profiles (COMBAT_HEAVY, MOVEMENT_HEAVY, RESOURCE_HEAVY, METROPOLIS, LOW_MEMORY, DEFAULT_PROFILE, DEBUG_REFERENCE) explicitly carry subsystem_budgets.
- 19 unit tests written covering OK/WARN/DEGRADED for all three wired subsystems, stale-hash fallback, window reset, and defaults sanity.
- Pre-existing core test failures (test_rpg_math, test_registry_adapters, etc.) confirmed pre-existing on branch baseline — unrelated to this ticket.

## Test Summary
- `tests/unit/engine/test_resource_budget_gate.py` (new):
  - `test_event_recorder_reports_warn_at_80pct_capacity`
  - `test_event_recorder_reports_degraded_at_full_capacity`
  - `test_canonical_hasher_reports_warn_over_budget`
  - `test_subsystem_budget_defaults_are_sane`
- Run: `pytest tests/unit/engine/ tests/unit/core/ -v`

## Files Changed
- `src/config/optimization_profiles.py` — Added `SubsystemBudget`, `SubsystemPressureReport` dataclasses; extended `OptimizationProfile` with `subsystem_budgets`; added 7 default budget constants and `DEFAULT_SUBSYSTEM_BUDGETS` dict; wired into all 7 profiles.
- `src/engine/replay_manager.py` — Added `SubsystemBudget`/`SubsystemPressureReport` import; added `_chunks_persisted` counter; incremented on success in `_execute_persistence()`; added `pressure_report()` method.
- `src/engine/checkpoint.py` — Added imports; added `BudgetedCanonicalHasher` class with `get_hash()` rate-limiter and `pressure_report()`.
- `src/observability/event_recorder.py` — Added imports; added `budget` parameter to `__init__()`; added `pressure_report()` method.
- `tests/unit/engine/test_resource_budget_gate.py` — New file, 19 unit tests.
- `docs/parity_ledger/infrastructure.yaml` — Appended INFRA-194, INFRA-195, INFRA-196.

## Completion Summary
All 7 plan steps implemented. `SubsystemBudget` and `SubsystemPressureReport` dataclasses added to `optimization_profiles.py` with 7 default budget constants injected into all profiles. `EventRecorder`, `ReplayManager`, and `BudgetedCanonicalHasher` each expose advisory `pressure_report()` methods returning OK/WARN/DEGRADED. 19 tests pass. Parity ledger updated with INFRA-194/195/196.
