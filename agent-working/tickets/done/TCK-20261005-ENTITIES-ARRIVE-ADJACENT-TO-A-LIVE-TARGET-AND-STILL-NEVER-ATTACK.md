---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK
phase: done
date: 2026-10-05
tags: [combat, strategy, cognition]
---

# TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK

## Title
A pursuit move ends when its live target is in attack reach, so entities that arrive adjacent re-enter the decision pass (filed as: entities arrive adjacent to a live target and still never attack)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
**What landed:** entities adjacent to a live target never attacked because the attack was never attempted, not rejected: a pursuit `ENTITY_MOVE` had no completion condition, so the decision pass was never called again. A pursuit now ends when its live target is within attack reach, and strategy writes no stale navigation point for an entity-typed objective. Mutual tile swapping falls by two orders of magnitude on three worlds (975 to 2, 1809 to 1, 978 to 3). Decision-path attacks barely move and no engagement improvement is claimed: the brain cadence, the flee gate and `BRACKETING` moves are the remaining gates, each with its own ticket.

**Filed text (historical, from the first pass; pre-`#344` numbers superseded by `investigation.md`):** **The measurement in this ticket is `rpg-implementer`'s**, taken as the A/B control for
`TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES` and reported to
`rpg-planner` on 2026-10-05. Filed separately because it is not that ticket's defect and would
survive its fix intact — the planner's call, not the implementer's.

`TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` exists because the decision-driven `ATTACK` path
fires 0-2 times per 1000-2000 ticks while the incidental opportunity-attack mechanic fires
181-2177. Its item (1) investigation root-caused that to the dispatch discard: `COMBAT_ENGAGE` won
the goal competition and the win was thrown away. `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND`
(PR #291) fixed the discard and merged 2026-10-04.

**The discard is fixed and the attack count did not move.** Measured at 2000 ticks, seed 42,
`audit_mode`, `LocalSequentialExecutor`, live holders only, both arms of the termination A/B:

| | `crowded_frontier` | `frontier_living_world` |
|---|---|---|
| combat objectives are kind `defeat_enemy` | 6891 / 6891 samples | — |
| navigation within 1 tile of the **live** target | **3779 / 3839** | — |
| `CombatActions.execute_attack` dispatches (control / fixed) | **0 / 0** | **5 / 5** |
| `resolve_attack` calls (control / fixed) | **0 / 0** | **1 / 1** |

So on `crowded_frontier` entities now hold a correctly-kinded objective against a live enemy, resolve
its current position, walk to within one tile of it in 98.4% of samples — and attack **zero** times.

**This is the original "arrived and do nothing" symptom, with the arrival now correct.**
`TCK-20261002`'s own framing was that entities navigate to where the enemy *was* and emit an empty
`EntityUpdate` forever. Fixing the position only moved the failure one step later: they arrive at
where the enemy *is*, and still emit nothing. The terminus is presumably the arrived-noop branch at
`src/engine/tactical.py:297-299` (bare `EntityUpdate(entity_id=…)`) but that is a lead, not a
finding — it has not been traced for this case.

**Second, narrower discrepancy.** On `frontier_living_world`, 5 dispatches produce **1**
`resolve_attack` call. Four of five dispatched attacks do not reach resolution. That ratio is small
enough to trace exactly and may be a different defect from the zero-dispatch case.

## Scope
1. Trace, for one `crowded_frontier` sample where an entity is within 1 tile of its live target and
   holds an `ACTIVE` `defeat_enemy` objective, what the tactical pass actually returns and why no
   attack is dispatched. One traced sample end-to-end beats a survey.
2. Establish whether the zero-dispatch case and the 4-of-5 unresolved-dispatch case are the same
   defect or two. Do not assume.
3. Record which gate rejects the attack — legality, range, posture, cooldown, target eligibility, or
   none of them (i.e. the dispatch is simply never attempted). **"None of them, the branch is never
   reached" is a valid and likely answer**, and distinguishing "rejected" from "never attempted" is
   the main thing this ticket must deliver.
4. Relate the finding to the incidental opportunity-attack mechanic, which fires 181-2177 times in
   the same runs. Whatever lets the incidental path attack is a working positive control for
   whatever blocks the decision path; use it as one rather than reasoning about the decision path in
   isolation.

## Out of Scope
- The entity-target fix and objective termination — `TCK-20261002`. This ticket **assumes that
  landed** and measures what is left.
- Tuning combat volume, XP thresholds or engagement rates. `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME`
  is explicitly blocked until combat volume is not starved, and retuning against a starved path is
  the exact failure that epic warns about twice.
- The incidental opportunity-attack mechanic itself. It is the control, not the subject.
- `src/core/**` and `src/engine/{kernel,governor}.py` — contested, and partly held by `TCK-20261002`
  while that is open. Claim before editing.

## Acceptance Criteria
- [x] One `crowded_frontier` sample traced end-to-end (entity 19 against 15: tactical pass at tick 1, sticky pursuit
      `ENTITY_MOVE` from tick 3, pass never called again, tile swap every tick), with the terminating branch named
      (`DeterministicScheduler.select_work` sticky-task law plus the two `ENTITY_MOVE` dispatchers, `executor.py` and
      `worker_logic.py`); see `investigation.md`. Line numbers are in the investigation at this branch's commit.
- [x] Scope 3 answered: **never attempted**, not rejected. The unmet condition is that `evaluate_entity_intent` is not called
      (1953 of 1953 adjacent-to-live-target samples on clean `origin/main`, readiness at least 100, re-taken post-`#344`).
- [x] Scope 2 answered: two defects. The `OUT_OF_RANGE` sticky `ATTACK` re-dispatch and the friendly-fire verdict mismatch are
      first-pass, pre-`#344` leads, filed as their own tickets by the planner (measure first, not carried as values).
- [x] The decision-path attack count re-measured after the fix on both worlds, reported as measured: `crowded_frontier` 0 to 0,
      `frontier_living_world` 5 to 7 (non-opportunity `resolve_attack` 1 to 3). The count stays at zero on `crowded_frontier`;
      no engagement improvement is claimed.
- [x] Counter scope stated: decision-path `execute_attack` calls, `resolve_attack` split by opportunity or not, and mutual tile-swap
      tick-pairs; the opportunity-attack counter is reported separately and is not total combat volume. Live holders only for
      the adjacency probe.
- [x] Determinism: the wide sweep (certification, regression, architecture, engine, integrity, mechanic_scenarios, scenarios,
      integration, unit core/engine/domains/strategic/combat/tactical/world/systems/tools, `tests/tools`; `-m "not slow"`) ran on
      the tree rebased onto `bfe7b19dc` and gave 4 failed, 8271 passed; the failures were the 60 s conftest timeout on
      `test_behavioral_5k_regression` and `test_long_run_stability` (both red on clean `origin/main`, the latter
      measured), a `REGISTRY.yaml` drift (regenerated), and `test_aggressive_budget_warning` (passes after the rebase onto
      `544b1d341`). No hash was regenerated. The final rebase onto `544b1d341` brought in a comment-only `src/` edit and
      agent tooling, and the three non-timeout tests were re-run on that tree; the whole sweep was not repeated.

## Related Tickets
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — **this sits on the chain's critical path.** The
  chain's own `SEQUENCE.md` records item (1) as having answered the root question; this ticket says
  the answer was incomplete, so that file needs a correction once this is understood. Do not edit
  the sequence file on the strength of this ticket alone.
- `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND` (done, #291) — fixed the
  discard. Its AC6 also landed contradicted; unrelated to this, but the same PR.
- `TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES` — produced this
  measurement as its control arm.
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (done) — the original 181-2177 vs 0-2
  split and the measurement method reused here.
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` — chain item (2), a corpus measurement
  ticket on this same path. Its numbers depend on what this ticket finds.
- `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` — chain item (5), blocked last.

## Related Docs
- `docs/mechanics/02_combat_laws.md` — damage formula, tactical modifiers, victory outcomes
- `docs/engine/contracts/tactical_contract.md` — objective resolution and the tactical pass
- `docs/parity_ledger/combat_movement.yaml`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION/`

## Related Code Areas
- `src/engine/tactical.py:297-299` — the arrived-noop branch, **a lead not a finding**
- `src/domains/combat_engagement/` — `CombatActions.execute_attack`, `resolve_attack`
- `src/engine/legality.py` — a candidate gate
- `src/ai/goals/scorers.py::CombatEngageScorer` — produces the objective

## Assumptions / Open Questions
- Line numbers are from before `TCK-20261002`'s edits to `src/engine/tactical.py`. **Re-derive them**;
  that ticket changes this file substantially.
- `crowded_frontier` shows 0 dispatches and `frontier_living_world` shows 5. Whether that is the same
  defect at two severities or two different things is **open** and is Scope 2.
- Whether the decision-path attack count was ever *expected* to rise from #291 alone is not recorded
  anywhere. #291's own scope was the objective-kind discard, and nobody appears to have predicted a
  specific attack count for after it. So this ticket should not be read as "#291 failed" — it is
  "the chain's symptom is still present and the next cause is unidentified".
- The A/B's two arms differ only by the termination hook, so the identical attack counts across arms
  (0/0, 5/5) are evidence the termination fix neither helps nor harms engagement — **not** evidence
  about what blocks it.

## Implementation Notes
The question's answer is a three-gate chain, now four (`investigation.md`): (1) a sticky pursuit `ENTITY_MOVE` with no completion
condition (fixed here); (2) the 10-tick brain cadence in `scheduler.py` (contested, untouched); (3) the flee gate, regional trauma
fed into panic (own ticket, not changed); (4) `BRACKETING` repositioning moves, which the fix deliberately does not end (own ticket).
Fix: `MovementCandidateSelector.pursuit_reached_attack_range` / `pursuit_completion_update` end a `PURSUE` `ENTITY_MOVE` whose live
target is in attack reach (idle encoding, navigation target cleared), wired into both dispatchers; the strategic redirection writers set
no navigation point for an entity-typed objective (they still claim the navigation). Non-`PURSUE` modes, dead and missing targets
are unchanged. The first-pass measurements were pre-`#344`; every figure cited was re-taken on `origin/main` `544b1d341` and labelled
value or sample. One first-pass claim died on the re-measurement: `PANIC_RETREAT` 143 of 147 (97%) became 141 of 353 (40%) with
194 `BRACKETING`; the planner withdrew "everyone flees" and "dominant gate" accordingly.

## Test Summary
`tests/unit/engine/test_pursuit_completion.py` (13) and `tests/unit/strategic/test_redirection_entity_objective.py` (3), each with a
disabling control; all pass on the rebased tree. Wide sweep as in Acceptance Criteria. Base-red and not caused here:
`test_behavioral_5k_regression` and `test_long_run_stability` (60 s conftest timeout; 60.25 s here, 60.23 s on a clean
`origin/main` worktree).
- FAIL tests/regression/test_behavioral_5k.py::test_behavioral_5k_regression: 60 s conftest timeout, red on clean `origin/main`, not caused here.
- FAIL tests/integration/world/test_long_run_stability.py::test_long_run_stability: 60 s conftest timeout (60.25 s here, 60.23 s on a clean `origin/main` worktree), not caused here, routed by the planner.
- Unexplained, not a failure: opportunity attacks `frontier_living_world` 38 to 644 and `crowded_frontier` 488 to 283; 10 `LAW-OCCUPANCY-COLLISION` errors on both clean and fixed trees (ticket filed by the planner).

Lint tools (ruff, mypy, complexipy, ast-grep, prek) are absent locally; CI is the first lint run.

## Files Changed
`src/engine/candidate_selector.py`, `src/engine/executor.py`, `src/engine/worker_logic.py`,
`src/systems/strategic_systems/intelligence.py`, `src/systems/strategic_systems/redirection.py`;
tests `tests/unit/engine/test_pursuit_completion.py`, `tests/unit/strategic/test_redirection_entity_objective.py`;
docs `docs/engine/contracts/tactical_contract.md`, `docs/engine/kernel.md`, `docs/guidelines/intentional_divergences.md` (2.68),
`docs/parity_ledger/combat_movement.yaml` (`COMB-329`), `docs/plans/rpg_design_roadmap/rpg_implementer_lane_split.md`,
`docs/REGISTRY.yaml` (regenerated); staging artifacts moved to `agent-working/stored_artifacts/`.

## Completion Summary
Entities that reached a live target no longer sit in a pursuit move that never ends: tile-swap tick-pairs fall from 975 to 2
(`crowded_frontier`), 1809 to 1 (`frontier_living_world`), 978 to 3 (`urban_political`), unchanged where there was none to fix.
Decision-path attacks barely move (`frontier_living_world` 5 to 7, `crowded_frontier` 0 to 0), so **no engagement improvement is
claimed**: gates 2 to 4 remain. Unexplained and reported as such: opportunity attacks `frontier_living_world` 38 to 644 and
`crowded_frontier` 488 to 283. Pre-existing on main, not caused here: 10 `LAW-OCCUPANCY-COLLISION` errors on both trees. Follow-ups filed
by the planner: sticky `ATTACK` out of range, hostile-list/legality disagreement, social-contract objective target, the
trauma-to-panic mapping, `BRACKETING` moves, the occupancy-collision hard law.
