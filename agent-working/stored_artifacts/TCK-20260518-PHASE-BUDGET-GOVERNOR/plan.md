---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260518-PHASE-BUDGET-GOVERNOR
artifact_type: plan
tags: [phase, budget, governor]
---

# Implementation Plan: Adaptive Phase Budget Governor

## Goals
Implement an adaptive governor layer that translates phase-level performance metrics (rolling p95 latency, tick compute time, work debt) into dynamic candidate budgets and scan policies for the authoritative pipeline.

## Architectural Design
1. **`src/engine/phase_governor.py`**:
   - Define `ScanPolicy` enum/dataclass representing scan rigor (`FULL`, `THROTTLED`, `EXACT_DIRTY`).
   - Define `PhaseBudgets` dataclass containing `candidate_budget`, `strategic_budget`, `movement_budget`, `background_sweep_interval`, `compaction_level`.
   - Implement `PhaseBudgetGovernor` class with `evaluate(profile, signals, status, current_tick) -> PhaseBudgets`.
2. **`src/engine/policy.py`**:
   - Update `GovernorPolicy` to include `phase_budgets: PhaseBudgets`.
   - Update `GovernorPolicy.from_mode` to provide baseline budgets for NORMAL, CONSTRAINED, DEGRADED, SURVIVAL modes.
3. **`src/systems/strategic_systems/work_queue.py`**:
   - Update `StrategicWorkQueue.build(state, update, dirty, budget=50, sweep_interval=1)`:
     - Tier 1-6 (urgent/dirty) are always evaluated.
     - Tier 7 (background sweep) only includes entities if `(state.tick + e_id) % sweep_interval == 0`.
     - Cap the final selection at `budget`.
4. **`src/engine/candidate_selector.py`**:
   - Update `MovementCandidateSelector.select(state, update, candidates, budget=1000, scan_policy="FULL")`:
     - If `scan_policy == "EXACT_DIRTY"`, prioritize dirty movement IDs and urgent blockers.
     - Defer non-urgent wander or long-distance moves if total candidates exceed `budget`.
5. **Correctness Invariance**:
   - Verify that death/lifecycle consistency (`lifecycle`, `biological`, `corpse`), economic transactions (`resource_node`, `economy`), and quest rewards are never skipped regardless of budgets.

## Verification
- Unit test `tests/unit/optimization/test_phase_budget_governor.py`:
  - Assert that elevated phase p95 metrics cause budgets to throttle down.
  - Assert that urgent candidates are preserved despite tight budgets.
  - Assert that budgets recover when latency drops.
- Integration test `tests/integration/optimization/test_degraded_mode_correctness.py`:
  - Run multi-tick simulation under simulated high pressure.
  - Assert that all lifecycle deaths, accepted transactions, and quest finalizations occur deterministically and correctly.
