---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260619-FIX-PERF-BUDGETS-RESET
phase: done
date: 2026-06-19
tags: [performance, budgets, reset, provider, audit-blocker]
---

# TCK-20260619-FIX-PERF-BUDGETS-RESET

## Title
Fix `PerformanceBudgets` class-level counter: add reset at simulation run start and cap per-tick not per-run

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`PerformanceBudgets` in `src/world/providers/requirements.py` uses class-level integer attributes as shared counters across all entities and all ticks. Two compounding bugs:

1. **Cap at wrong granularity**: `provider_calls_total > 500` causes `ResourceOpportunityProvider.get_opportunities()` to return `[]` for the rest of the run. At 20 entities/tick this budget exhausts at tick 25, coinciding with observed stasis onset. The intent (per `TCK-20260527-COG-PHASE1-BUDGETS`) was to throttle within a single tick evaluation pass, not to cap the entire run.

2. **No reset between runs**: `PerformanceBudgets.reset()` exists but is not called at simulation run start. In any process that runs multiple simulations (sweep, mutation lab, audit runner), the second run starts with counters already at or past the cap, producing zero opportunities from tick 1.

This is a P1 blocker: even after RC1 and RC2 are fixed, stasis would resume at tick 25 in single runs and tick 0 in multi-run processes.

## Scope
- Identify the correct reset boundary: **per-tick** (reset at the start of each `Kernel.tick_once()`) or **per-run** (reset in the `Kernel.__init__()` / run-start sequence). Per-tick is the safer choice: it keeps the throttle protecting individual tick budgets while allowing opportunity provision across the full run.
- Call `PerformanceBudgets.reset()` at the correct boundary.
- Adjust the per-tick cap to be proportionate: 500 calls total for 20 entities = 25 calls/entity/tick, which is reasonable for a per-tick budget. Confirm the 500 cap is intentional at per-tick granularity (not per-run).

## Out of Scope
- Changing the budget numbers themselves unless investigation reveals they are wrong.
- Refactoring `PerformanceBudgets` to use instance state (architecturally cleaner but out of hotfix scope).
- Fixing RC1 or RC2.

## Acceptance Criteria
1. `PerformanceBudgets.reset()` is called at the start of each simulation tick (or at run start if per-run granularity is confirmed as the design intent).
2. A 200-tick sandbox_world run with 20 entities never hits the provider cap before tick 195 (i.e., the cap applies within a tick window, not across the full run).
3. Two sequential simulation runs in the same process both start with `PerformanceBudgets.provider_calls_total == 0`.
4. Existing tests `test_performance_budgets.py` pass without modification.
5. A new test asserts that after calling `PerformanceBudgets.reset()` once per simulated tick loop iteration (2 ticks, 20 entities each), `provider_calls_total` never exceeds the per-tick budget cap at the end of each tick.

## Related Tickets
- TCK-20260527-COG-PHASE1-BUDGETS (original implementation — introduced the class-level counter design)
- TCK-20260619-FIX-ADVENTURE-OPPORTUNITY-WIRING (RC1 — must be fixed first for provider calls to occur at all)
- TCK-20260619-FIX-NEAR-SERVICE-REGION (RC2)

## Related Docs
- `docs/audits/D03_behavioral_emergence.md` — RC3 confirmed
- `stored_artifacts/TCK-20260527-COG-PHASE1-BUDGETS/investigation.md` — original design intent

## Related Stored Artifacts
- `stored_artifacts/TCK-20260527-COG-PHASE1-BUDGETS/`

## Related Code Areas
- `src/world/providers/requirements.py:24-36` — `PerformanceBudgets` class and `reset()` method
- `src/world/providers/resources.py:31-35` — cap check using `provider_calls_total`
- `src/engine/kernel.py` — tick loop entry point where `reset()` call should be inserted
- `tests/unit/strategic/test_performance_budgets.py` — existing budget tests

## Assumptions / Open Questions
- **Per-tick vs per-run**: Confirmed per-tick by original ticket intent ("strict call throttling to protect simulation ticks"). `_phase_init()` is the correct reset site — runs before every domain phase.

## Implementation Notes
Added `PerformanceBudgets.reset()` as the first call in `Kernel._phase_init()` (`src/engine/kernel.py`). Runs before `OccupancySnapshot` and all domain phases each tick, so the 500-call cap is per-tick not per-run. All counters (`provider_calls_total`, `provider_calls_by_kind`, `opportunities_returned_total`, `requirements_evaluated_total`) are reset via the existing classmethod. Added `test_per_tick_reset_prevents_cap_accumulation` to verify non-accumulation over 2 simulated ticks with 20 entities each.

## Test Summary
`pytest tests/unit/strategic/test_performance_budgets.py -x` — 3/3 passed.

## Files Changed
- `src/engine/kernel.py`
- `tests/unit/strategic/test_performance_budgets.py`

## Completion Summary
Called `PerformanceBudgets.reset()` at the start of `Kernel._phase_init()` so the provider budget cap resets each tick rather than accumulating across the run. Added parity entry INFRA-203. One new test confirms multi-tick non-accumulation.
