---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING
phase: open
date: 2026-10-03
tags: [determinism, economy, engine, bug]
---

# TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING

## Title
Remove wall-clock compute time from `global_salience` so host speed no longer changes shop prices (PERF-D1 amendment A1)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY` found, and perf-planner confirmed by reading the code on 2026-10-03, that measured wall-clock time reaches authoritative gameplay. `Kernel` builds `compute_ratio = tick_compute_ms / max_tick_budget_ms` from the previous tick's measured compute time, adds it to `debt_ratio` to form `global_salience` (capped at 2.0), and writes it into the `StateUpdate` as `pressure_signals_set` (`src/engine/kernel.py`, around lines 661-678). `apply.py` stores it in `AuthoritativeState.pressure_signals`. `DynamicPriceService.calculate_buy_price` (`src/systems/economy_systems/economy.py:27`) multiplies the price by `1 + salience`. `ShopService.buy_item` (`src/town/shop.py:35-41`) uses that price for the gold-sufficiency check and the cost, and is reached from the live intent path (`src/engine/intent/action_intent.py:246`). So the same seed on a slower or busier host produces higher prices, different purchase outcomes, and a different world. `audit_mode` zeroes the signal, which hides the problem from audited runs.

The owner decided on 2026-10-03 (PERF-D1 amendment A1, `docs/architecture/performance_optimization_decisions.md`): a game-facing signal may be computed only from deterministic inputs, in both the Canonical and Live contracts. `compute_ratio` is removed from `global_salience`; the work-debt term stays.

## Scope
- Remove the `compute_ratio` term from `global_salience` in the kernel; salience is derived from deterministic inputs only (the work-debt ratio). Decide, with evidence, whether `compute_ratio` stays in `pressure_signals` as an observability-only value (then no system may read it; add a test that enforces this) or is removed from the dict
- Confirm no other reader of `pressure_signals` uses a wall-clock-derived value (current readers: `economy_systems/economy.py`, `observability/reporting/metric_recorder.py`, `testing/scenario_runner.py`)
- Tests: same seed, same state, injected `tick_compute_ms` values of 0 and well above budget give identical salience, identical buy prices, and identical proof digests over a short run with a purchase; a regression test that `DynamicPriceService` output does not change with host timing
- Record the gameplay change in `docs/guidelines/intentional_divergences.md` (rationale class: Bug Fix or Intentional Gameplay Change, with a verification test path); update `docs/mechanics/03_economic_laws.md` if it describes buy-price pressure, and the relevant parity ledger entry (`town_resource.yaml` or `world_dynamics.yaml`)
- Update `docs/engine/contracts/resource_governor_contract.md` "Pressure Signal Semantics" to say `tick_compute_ms` is a control signal, not a gameplay input

## Out of Scope
- The three other PERF-D1 inputs (governor mode choice, mid-tick cutoff, end-of-tick drop) and the Canonical proxy set; those are PERF-M1 work
- Adding `pressure_signals` to the proof digest (a PERF-D5 coverage question; record it as a finding here, do not change the digest)
- Rebalancing shop prices beyond removing the timing term
- Any change to `audit_mode` behavior

## Acceptance Criteria
- [ ] `global_salience` has no input derived from wall-clock time or host resources; a test injects extreme `tick_compute_ms` and shows identical salience and prices
- [ ] No system reads a wall-clock-derived value from `AuthoritativeState.pressure_signals` (enforced by a test)
- [ ] `intentional_divergences.md`, the mechanics chapter (if affected), the parity ledger entry, and the governor contract are updated in the same change
- [ ] Scoped economy, engine, and determinism tests pass; SimQ economy calibration is checked for drift and any drift is reported, not tuned away

## Related Tickets
- TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY (evidence)
- TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC (program)
- TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2, TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION (other wall-clock consequences)
- TCK-20260619-E33D-REP-DISCOUNTS (shop buy path history)

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D1, amendment A1; PERF-D5)
- `docs/performance/wall_clock_inventory.md`
- `docs/mechanics/03_economic_laws.md` §4, `docs/engine/contracts/resource_governor_contract.md`, `docs/engine/deterministic_execution.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY/` (after that ticket closes)

## Related Code Areas
- `src/engine/kernel.py`, `src/engine/apply.py`, `src/systems/economy_systems/economy.py`, `src/town/shop.py`, `src/engine/intent/action_intent.py`, `src/core/state.py`

## Assumptions / Open Questions
- **Unblocked by the owner, 2026-10-04 (PR #312, `docs/plans/design_enhancement/performance_optimization/rpg_core_handoff.md`):** a determinism break, so a hard RPG bug under memo row 7 (`docs/plans/systemic_world/owner_decision_memo.md`), raised to P1 and placed in the RPG-core hard-bug queue. The RPG-core track implements it; perf-planner reviews. It lands before the no-touch window on `state.py`/`apply.py`/`pipeline.py`/`kernel.py` opens (it edits three of the four). Was BLOCKED behind the RPG-core entry gate and the Code Craft `src/` freeze from 2026-10-03 to 2026-10-04
- Note for the implementer (perf-planner, 2026-10-04): the work-debt term that stays is always 0 in production, because nothing in `src/` ever increases `state.work_debt` (`TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`). After this fix `global_salience` is 0 in ordinary play and the buy-price multiplier is 1. That is still the correct determinism fix; record the economic effect in the divergence entry instead of describing salience as live
- Add a regression test that fails with `audit_mode=False`: `audit_mode` zeroes the signal and hides the defect from audited runs
- Whether economy calibration worlds were tuned while salience moved with host timing is unknown; calibration drift after the fix is expected to be small because the compute term is near zero on fast hosts, but this is unmeasured

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
