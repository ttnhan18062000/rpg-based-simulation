---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE
artifact_type: investigation
tags: [strategy, cognition, combat]
---

# Investigation

Probes: `probes/` (the ENTITIES-ARRIVE-ADJACENT probe set plus the variants named below). Config for every
figure: seed 42, `PROD_SMALL` with `max_tick_budget_ms=1e9`, `no_frame_pacing`, `no_replay`, `audit_mode`,
`LocalSequentialExecutor`, 2000 ticks, one simulation at a time, each arm run twice. Every counter was identical
across the two runs of an arm, so these are values.

## 1. Re-measure at `b15fef405` (before the fix; `7daef8075` gave identical numbers)

| | `crowded_frontier` | `frontier_living_world` |
|---|---|---|
| forced calls with a live hostile adjacent | 193 | 232 |
| `ATTACK` / `PANIC_RETREAT` / `BRACKETING` / plain move | 76 / 30 / 41 / 45 | 169 (+3 out of range) / 25 / 1 / 32 |
| fleeing with the trauma term present | 13 of 27 | 20 of 28 |
| trauma alone over the threshold | 3 (`hometown`, trauma 1.9) | 0 |
| `execute_attack` / non-opportunity `resolve_attack` | 41 / 25 | 30 / 18 |
| trauma at tick 2000 | `hometown` 1.9, `bandit_road` 0.85 | `hometown` 0.96 |

Control (trauma forced to 0): fleeing 27 to 18 and 28 to 11. The earlier "97% PANIC_RETREAT" and "everyone
flees" claims did not reproduce; the ticket was corrected and re-prioritised P2 (CORRECTION block).

## 2. After the fix (`regional_dread`, ceiling 0.3)

| | `crowded_frontier` | `frontier_living_world` |
|---|---|---|
| forced calls | 193 | 264 |
| `ATTACK` / `PANIC_RETREAT` / `BRACKETING` / plain move | 81 / 19 / 47 / 45 | 190 (+3) / 22 / 4 / 43 |
| fleeing / trauma alone | 16 / 0 | 19 / 0 |
| `execute_attack` / non-opportunity `resolve_attack` | 32 / 22 | 298 / 22 |

Trauma alone crossing the threshold: 3 before, 0 after. Fleeing 27 to 16 and 28 to 19. Trajectories diverge once
a flee changes, so forced-call totals are not like-for-like across arms.

## 3. Observation, not attributed

`frontier_living_world` after: `execute_attack` 298 against 30 before. `atk_outcomes.py` shows 274 of the 298
are `OUT_OF_RANGE` (10 before) and 267 come from entity 49 re-issuing an ATTACK on target 18 while its position
changes (payload `stale_ticks` 1 and `recent_positions` unchanged across the calls). The only code difference
between arms is the dread term, so this is a trajectory consequence; the cause of the repeated out-of-range
attack was not traced and is reported to the planner as a separate observation.

## 4. SimQ

`tests/simulation_quality/test_grade_regression.py` skips 82 of 89 tests locally on both arms (calibration
reports `data/calibration/*/quality_report.json` absent), so grade-anchor movement is not measured here.
