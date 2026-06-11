---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260412-STRAT-VERIF-FINAL_PLAN
phase: done
date: 2026-04-12
tags: [strat, verif, final_plan]
---

# TCK-20260412-STRAT-VERIF-FINAL

## Goal Description
Finalize the verification of the Strategic Cognition layer by implementing the "Near Death" E2E scenario and closing the remaining Milestone 7 (Final-System CLI path) tasks. This ensures that the reprioritization logic works not just in isolation (unit tests) but also in the full simulation loop.

## User Review Required
> [!IMPORTANT]
> The "Near Death" scenario will be implemented as a deterministic E2E test. It requires forcing an entity's health to a critical level mid-run. This is the last major behavioral validation required for the Strategy Roadmap.

## Proposed Changes

### [Component Name] Verification Harness & E2E Tests

#### [NEW] [test_strategic_reprioritization.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/e2e/test_strategic_reprioritization.py)
A new E2E test that specifically exercises the Milestone 5 reprioritization logic:
- Bootstraps a world via `HeadlessRunner`.
- Identifies a target Hero.
- Injects a "Near Death" status (HP < 10% or explicit event).
- Ticks the world via `WorldLoop`.
- Asserts that the entity's `StrategicState` generates a `THREAT` concern.
- Asserts that the `cognition_graph` shows a project pivot or suspension.

#### [MODIFY] [strategy_implementation_milestone_7.md](file:///home/vboxuser/Work/rpg-based-simulation/strategy_implementation_milestone_7.md)
Update the checklist to reflect that the CLI verification path is now canonical and verified by the E2E suite.

#### [MODIFY] [task.md](file:///home/vboxuser/Work/rpg-based-simulation/task.md)
Update tasks to reflect current progress (unit tests completed) and add the final E2E verification step.

---

## Verification Plan

### Automated Tests
- Run the new E2E test:
  `pytest tests/e2e/test_strategic_reprioritization.py`
- Verify the entire strategic regression suite:
  `pytest tests/e2e/test_strategic_regression.py`

### Manual Verification
- Inspect the generated `cognition_eX.json` to verify the "Near Death" node and its edges in the Cytoscape format.

**Tier:** standard
**Type:** chore
**Priority:** P1
