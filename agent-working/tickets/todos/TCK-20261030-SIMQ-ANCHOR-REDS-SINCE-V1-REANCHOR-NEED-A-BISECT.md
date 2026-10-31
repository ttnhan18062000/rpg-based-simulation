---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT
phase: open
date: 2026-10-30
tags: [simulation-quality, regression, determinism]
---

# TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT

## Title
A SimQ grade-stability test went red on main after the v1 re-anchor: urban_political_selfmodel_probe seed42 200t WORLD is 0.25 against anchor 0.32. Bisect it to the commit and mechanism that moved the score.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
codebase-implementer measured these on a clean `git archive` of origin/main de5a223ca, with no M7 code; codebase-planner relayed them on 2026-10-30. rpg-planner-ubuntu checked them against `tools/test_architecture/slow_known_reds.yaml` and `tests/simulation_quality/fixtures/grade_anchors.json`. Two `@pytest.mark.slow` tests in `tests/unit/worldassembly/test_corpus_diversity.py` fail, and neither is registered:

1. ~~`test_urban_political_seed123_500t_cognition_grade_stability`~~ REMOVED from this ticket on 2026-10-30. codebase-implementer's log shows a `TypeError` at line 680 (`sum(trial_scores)` over a `None` score) AFTER the band assertion passed. So the live pillar is no-data, which matches its no-data anchor. It is a test defect from #747, not drift. Moved to the hotfix TCK-20261030-CORPUS-GRADE-GUARD-AVERAGES-A-NO-DATA-SCORE.
2. `test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability`. WORLD scores 0.25 against anchor B 0.32 (-22%, past the shared 20% tolerance).

A third red, `test_hero_guild_routing_seed42_1000t_cognition_grade_stability`, is already a known red under TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE. Its measured 2.6506 equals the v1 value that entry names, so it is out of scope here.

These tests run under `audit_mode`, so host load cannot move the scores. codebase-planner saw both reds on 33da13604 as well. So the change landed between #747 (cb4f95015) and 33da13604; it is not, or not only, #785 or #790.

rpg-planner ruled on 2026-10-30, relayed via lead-planner-u24 and lead-planner: file this as a SEPARATE measurement-only ticket in the ubuntu queue, cross-linked to the held-rows ticket. Report to rpg-planner-ubuntu first, then to rpg-planner, which rules re-anchor or fix with the designer.

## Scope
1. Positive control: run test 2 at cb4f95015 and confirm it passes there (the anchor commit). Then run it at de5a223ca and confirm WORLD 0.25.
   - If it does not pass at cb4f95015, STOP and report: the window is wrong.
2. Bisect over the src commits in `cb4f95015..33da13604`. Test the candidates first:
   - 3533fde71 (#753 hostile acts by an act, not a state)
   - 35e80fb56 (#751 hostility lookups indexed)
   - 6e3ffea3f (#757 semantic foundation batch 1)
   - 2afdba653 (#760 dead systems classes deleted)
   - 792a6b439 (#762 unknown craft recipe refused)
   - 957caf8f6 (#758 proof digest)
   - f34d8254d (#765 squad group_id hash)
   - d914bace7 (#769 retreat step A)
   - dc059c49e (#771 cooperation candidates per tick)
   Use `git log --oneline cb4f95015..33da13604 -- src/` as the full list. Name the first commit where the WORLD score moves.
3. For each named commit, give the mechanism: which events or pillar inputs change, with event counts for the pillar before and after on that world, seed and tick count. Give the WORLD inputs behind 0.32 -> 0.25.
4. Report the table to rpg-planner-ubuntu, which relays it to rpg-planner. rpg-planner rules re-anchor (intended behaviour, via testing's re-anchor tool) or fix (a separate ticket with the designer).

Run settings: `PYTHONHASHSEED=0`, `audit_mode` as the tests set it, and an explicit `RPG_MEASURE_CACHE` on ubuntu. Run sequentially on an idle host, and only in a heavy slot granted through lead-planner.

## Out of Scope
- Changing any anchor, test or tolerance. The test-2 known-red entry was added with this ticket (owner rpg-planner, expiry 2026-11-13, measured values in `note`). Deleting or re-dating them follows the ruling at close.
- Finding for testing-planner, recorded and not filed (rpg-planner, 2026-10-30): `slow_known_reds.yaml` has no field that bounds a value, so a known red hides further drift until it expires. A possible fix is an optional enforced `expected` field.
- The 36 held rows of TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE, including hero_guild_routing_seed42_1000t.
- Any src fix.

## Acceptance Criteria
1. The positive control is recorded: test 2 passes at cb4f95015 and fails at de5a223ca, with the measured values.
2. The first moving commit, its PR, the measured score at its parent and at the commit, and the mechanism with event counts.
3. Every run records its commit, world, seed, ticks, PYTHONHASHSEED and wall time.
4. The report reaches rpg-planner-ubuntu, and the ruling (comment id) is recorded here before closure.
5. Run data written by this ticket is cleaned by run id.
6. Compensating control (rpg-planner ruling, 2026-10-30): the `slow_known_reds.yaml` entry for test 2 can't bound a value. So at close, re-measure test 2 on the then-current main and compare them with the values in the entries' notes. Any further drift is reported together with the bisect result, and the re-anchor must not absorb it.

## Related Tickets
- TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE (held rows; separate scope)
- TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1 (#747, the anchor commit cb4f95015)

## Related Docs
- docs/simulation_quality/eval_matrix_results.md
- docs/guidelines/intentional_divergences.md (if the mover carries a divergence)

## Related Stored Artifacts
- none

## Related Code Areas
- tests/unit/worldassembly/test_corpus_diversity.py
- tests/simulation_quality/fixtures/grade_anchors.json
- tools/test_architecture/slow_known_reds.yaml
- src/ (whatever the bisect names)

## Assumptions / Open Questions
- Owner DISPATCH GO, as narrowed, and the heavy-slot order: #715 comment 6518908366. The order is perf overnight, the corpus hotfix slow run, THIS bisect, B's runs, then (b) hunger part 1. Each run still needs lead-planner's explicit go against the gate. It goes to rpg-implementer-ubuntu's fresh session after its /clear.
- Assumed: the slow job runs both tests. Confirm in the slow-regression report.

## Implementation Notes
### Run plan (written 2026-10-30; no run has been made; every run waits for lead-planner's slot go through rpg-planner-ubuntu)
Method: one clean `git archive` per commit under a real path (not /tmp), checked out at the commit, with the test file and `grade_anchors.json` held at de5a223ca's copy so only `src/` moves. Command per run: `PYTHONHASHSEED=0 RPG_MEASURE_CACHE=<explicit dir> pytest tests/unit/worldassembly/test_corpus_diversity.py -k urban_political_selfmodel_probe_seed42_200t_social_world -m slow` under `systemd-run --user --scope -p MemoryMax=3G`, sequential, idle host. Record commit, world, seed, ticks, PYTHONHASHSEED, wall time and the WORLD score per run.

Order:
1. Positive control A: cb4f95015 (expect pass, WORLD about 0.32). If it fails, STOP: the window is wrong.
2. Positive control B: de5a223ca (expect fail, WORLD 0.25).
3. Binary search over the 14 `src/`-touching merge commits in `cb4f95015..33da13604`, oldest first: 35e80fb56 (#751), 3533fde71 (#753), 002bc317c (#735), 6e3ffea3f (#757), 2afdba653 (#760), 792a6b439 (#762), 957caf8f6 (#758), f34d8254d (#765), 7b4bf7a30 (#768), d914bace7 (#769), dc059c49e (#771), ea755bf43 (#776), fdfc5f9fd (#780), 1d8eef91f (#779). First probe 957caf8f6 (the middle), then halve: at most 4 runs (log2 14), plus 1 to confirm the parent of the first mover. Candidates named in Scope 2 are checked by the halving, not run one by one; if the halving lands on a doubtful commit, run its parent and itself.
4. Mechanism (Scope 3): for the first mover and its parent, one more run each that dumps the WORLD pillar inputs and event counts by type (same world, seed 42, 200t). That is 2 runs.

Count: 2 controls + at most 5 bisect + 2 mechanism = at most 9 runs. Wall time per run: not yet measured. The 500t sibling took 49 s, so 200t is estimated at 25 to 60 s plus checkout and import, about 1.5 to 2 min each; estimate 15 to 20 min for the whole plan. The first control run gives the real figure, and the estimate is replaced by it.
Slot ask: one heavy slot of about 30 min, sequential, after the perf overnight window.
This PR carries the known-red entry in `tools/test_architecture/slow_known_reds.yaml` (taken from rpg-planner-ubuntu's seat branch 1d3448c4d; the only diff against origin/main is that one entry). The PR body must name lead-planner-u24 as the testing-domain reviewer for that file (authorised by the u24 owner, #715 6519647030; reviewer named in #715 6520942711).
Compensating control (AC6): at close, one more run on the then-current main.


### Results (run 2026-10-30, slot go from lead-planner via rpg-planner-ubuntu; 7 runs of the 9 allowed)
Every run: world urban_political, seed 42, 200 ticks, PYTHONHASHSEED=0, audit_mode, 1 trial, `RPG_MEASURE_CACHE=/data/vboxuser/Work/simq_bisect/cache`, wrapped `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`, sequential, clean `git archive` at the commit with the test file and `grade_anchors.json` held at de5a223ca's copy, MemAvailable 3.9 to 4.5 GB before each run. The runner executes the test body (`_run_engine`, quality hub replay, the test's own `_anchor`, `_snap_failure`, `_within_score_tolerance`) as a script, so the verdict is the test's, and prints the score on a pass too.

| # | commit | PR | WORLD score (events) | SOCIAL | WORLD vs anchor 0.32 | wall (total) |
|---|---|---|---|---|---|---|
| 1 | cb4f95015 | #747 anchor | 0.32 (23) | 37.48 | pass (control 1) | 22 s |
| 2 | de5a223ca | main | 0.25 (17) | 38.255 | FAIL (control 2) | 27 s |
| 3 | 957caf8f6 | #758 | 0.32 (23) | 37.48 | pass | 40 s |
| 4 | dc059c49e | #771 | 0.25 (17) | 38.255 | fail | 23 s |
| 5 | 7b4bf7a30 | #768 | 0.32 (23) | 37.48 | pass | 23 s |
| 6 | d914bace7 | #769 | 0.25 (17) | 38.255 | fail | 20 s |
| 7 | a25619971 (parent of d914bace7) | | 0.32 (23) | 37.48 | pass | 19 s |

**First moving commit: d914bace7 (#769, TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE, step A: retreat escalates with the wound on the need scale, only against a hostile that acts).** Its parent a25619971 gives WORLD 0.32 (23 events); d914bace7 gives 0.25 (17). The `src/` diff between 7b4bf7a30 and a25619971 is empty, so the earlier good point and the true parent agree. The src change in #769 is `src/ai/goals/scorers.py` (4 lines, `CombatRetreatScorer`) and `src/engine/need_pull.py` (7 lines). The scores at d914bace7 and dc059c49e, and at 7b4bf7a30 and a25619971, are identical, so nothing after #769 and before de5a223ca moves this world.

**Mechanism (urban_political seed 42, 200t, parent vs d914bace7):** the WORLD pillar counts `hazard_drain_applied` 17 to 12, `region_trauma_delta` 3 to 2, `ecology_cycle_completed` 3 to 3 (23 to 17). The run trajectories first differ at tick 84 (SOCIAL: entity 18 `contract_expired_offer`, `group_expelled` for entities 18 and 30). Entity 3 takes no hazard drain after tick 111 (5 fewer, parent last at 189). Entity 18 is killed at tick 172 in the parent and survives in d914bace7, so `entity_killed` 2 to 1, `combat_resolved` 3 to 2, and the tick-172 `bandit_road` trauma delta is gone. Other pillars move too: SOCIAL 2032 to 2080 events, COMBAT 14 to 12, ECONOMY 15 to 13, NARRATIVE 35 to 30, PROGRESSION 7 to 6, COGNITION 5623 to 5662. That reads as the intended behaviour change (a wounded entity now retreats earlier from an acting hostile, so fewer entities stay in hazard regions and fewer die), not noise: both arms ran under audit_mode and are repeatable (controls 1 and 7 give identical numbers at two different commits). The WORLD inputs behind 0.32 to 0.25 are the 6 lost events: 5 hazard drains and 1 trauma delta. The ruling re-anchor or fix is rpg-planner's.

AC6 re-measure at close on the then-current main is still to do. Run data: the per-commit archives under `/data/vboxuser/Work/simq_bisect/<sha>/` (each holding its one run dir) are removed after this record; the `.out` files are kept.

### Trace pair (run 2026-10-31, rpg-planner ruling 2 option b, ruling file in this ticket's staging dir)
Full chain, probe and key rows: `agent-working/staging_artifacts/TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT/evidence/trace/chain.md`.
- (i) Shown. At tick 42 entity 18's inputs are identical in a25619971 and d914bace7 except COMBAT_RETREAT: 84.5188 against 123.3988, because `CombatRetreatScorer.score` (`src/ai/goals/scorers.py:238-239`) calls `retreat_pull` (`src/engine/need_pull.py`) when `acting_threat_to` is true. 123.40 beats REGION_STABILIZATION (100) and 84.52 does not, so from tick 43 the target is (25,25) `combat_retreat` against (70,50) `stabilize`.
- (ii) Shown to the first group-objective difference (corrected after the planner's verification; full text in chain.md). **t63:** entity 18 holds a current `combat_retreat` project in d914bace7 (created t42, current from t43, SUSPENDED by t53 and through t62, ACTIVE and current again at t63), so `update_groups` issues `group_obj_10006_30` (COMBAT_RETREAT) to entity 30 for t63 to t83 (21 rows); the parent has no retreat project, an empty current project, and issues none. Ticks 0 to 62 are identical (146 rows). Why the parent's arbiter does not materialise a retreat project at t62 despite retreat 136.45 against 100 is not traced. **t84:** 10006 dissolves in d914bace7 because the cohesion check (the loop skips the leader, groups.py:124-128, so only 30 is tested) measures member 30 against `group.anchor` (the previous tick's midpoint): squared distance 98.0 at t83, 105.25 at t84, limit 100; parent 6.5. **t104:** first id split, (12,19) is 10005 in the parent (4 + 1 pending) and 10004 in d914bace7 (4 + 0). **t123:** the (3,28) group is 10006 in the parent (only there) and 10007 in d914bace7 (5 + 1 against 5 + 2 pending), directive ids differ from t124. Observed lead, not traced: entity 3's objective runs t124 to t143 in the parent and t124 to t199 in d914bace7, and the vanished drains are entity 3 at t185 to t189; whether the id difference matters is not established.
- Planner verification files: `evidence/trace/planner_verify/`.

## Test Summary
## Files Changed
## Completion Summary
