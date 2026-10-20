---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261019-GATE-VALIDITY-CHECKS-FIRE-THROUGH-THE-REAL-KERNEL-AND-V3-SEES-EVERY-STARVATION-DEATH
phase: done
date: 2026-10-19
tags: []
---

# TCK-20261019-GATE-VALIDITY-CHECKS-FIRE-THROUGH-THE-REAL-KERNEL-AND-V3-SEES-EVERY-STARVATION-DEATH

## Title
Every gate validity check has a real-kernel positive, and V3 sees every starvation death

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Designer ruling after the v1 gate: a green that cannot go red is not evidence (V1 and V4 were blind; V5, V6 and V8 read 0 in every gate run). Each of V1-V8 needs one real-kernel positive built through `rpg_gate_run.build_kernel`, with `violations > 0` on the emitted row. V1 and V4 have theirs (Lane B, Lane A). This adds V2, V3, V5, V6, V7, V8. Forcing the V3 positive found a real blind spot: `StarvationRecorder.observe` looked for a death only on entities that had an `EntityUpdate` that tick, but a passive starvation death is applied by the lifecycle step, so a starving entity without an update was never recorded and `starvation_deaths_seen` stayed 0 (nothing in the tally could reveal it). Designer ruling added: V3's `starvation_deaths_seen` must equal O2's STARVATION count (O2 scans every entity), and a mismatch makes the run no-data, never a pass.

## Scope
- `src/observability/starvation_record.py`: `observe` also inspects every entity stamped with this tick's starvation cause.
- `src/observability/rpg_gate_metrics.py` `compute`: raises `GateDataMissingError("starvation tally X != O2 starvation deaths Y")` when the tally disagrees with O2's STARVATION count in the same document (no-data, via the existing channel for inconsistent data).
- `tests/integration/observability/test_gate_validity_checks_fire_through_the_real_kernel.py`: V2, V3 (+ no-rerecord control), V5, V6, V7 (pooled, two real runs fed to the real `pool()`), V8.
- `tests/unit/observability/test_rpg_gate_metrics.py`: the tally-vs-O2 mismatch and match cases; the `_run` helper keeps its synthetic documents consistent.

## Out of Scope
The world (no content or tuning); the report harness (`GateDataMissingError` already makes the document no-data and surfaces it; if the report needs a distinct reason line, that goes to testing-planner). V1 and V4 positives (other lanes).

## Acceptance Criteria
- One real-kernel positive per V-id with `violations > 0` (node ids in the report).
- The V3 positive fails without the recorder fix.
- A starvation death recorded once; an entity that starved earlier is not re-recorded.
- Tally disagreeing with O2: no-data, not a pass; agreeing: V3 reads normally.
- Final state hash identical on 3 worlds x seed 42 (observer-only change), serial.

## Related Tickets
TCK-20261019-MEAT-DECAYED-IS-WRITTEN-FROM-THE-APPLIED-OUTCOME-V2; v1 gate fails (rpg-planner)

## Related Docs
/mnt/data/scratch-rpg-implementer-3/v1_gate_fails_C.md

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
src/observability/starvation_record.py; src/observability/rpg_gate_metrics.py; src/observability/run_ledger.py

## Assumptions / Open Questions
- Each positive forces its violation by seeding state or opening a path (V2: silence the decay sink; V3: shrink the starvation drain; V5: seed positions outside the extent; V6: seed coin between ticks; V8: an unsourced add through the world-dynamics step). V7 fires naturally in short real runs because nobody has used an inn or a node yet; it is a real pooled row from real runs.
- In the 15 v1 gate runs O2 found exactly one starvation death (merchant 37) and V3 recorded it, so no death was missed there (rpg-planner).

## Implementation Notes
V3 positive: a hungry worker is placed beside an inn with the starvation drain shrunk to a one-tick death; the dying entity has no update that tick (confirmed with a hook: 12 updates, the entity not among them). Without the fix the positive fails with the new tally-vs-O2 error (tally 0, O2 1).

## Test Summary
- tests/integration/observability/test_gate_validity_checks_fire_through_the_real_kernel.py: 8 passed (V2 + its control, V3 + once-only control, V5, V6, V7, V8). Unforced 12-tick control run: V1-V6 and V8 read 0. The two V3 tests fail without the recorder fix (error: starvation tally 0 != O2 starvation deaths 1).
- tests/unit/observability/test_rpg_gate_metrics.py 17 passed (adds the tally-vs-O2 mismatch/match test). With tests/unit/tools, tests/simulation_quality/rpg_gate and test_starvation_death_record: 1010 passed. lint-imports 17 kept, 0 broken.
- Hash, 3 worlds x seed 42 x 5000 ticks, audit_mode, PYTHONHASHSEED=0, serial, base origin/main 9b485e83e vs this branch: identical final hash in frontier_living_world (db7ade49...), urban_political (a44bac86...), crowded_frontier (3f967587...).

## Files Changed
src/observability/starvation_record.py; src/observability/rpg_gate_metrics.py; tests/integration/observability/test_gate_validity_checks_fire_through_the_real_kernel.py; tests/unit/observability/test_rpg_gate_metrics.py

## Completion Summary
V3 sees every starvation death and cannot be read when its tally disagrees with O2; V2, V3, V5, V6, V7, V8 each have a real-kernel positive.
