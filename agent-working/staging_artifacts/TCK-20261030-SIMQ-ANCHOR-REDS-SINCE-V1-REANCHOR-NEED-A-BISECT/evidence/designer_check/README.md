# Designer's bounded check on the #769 s42 rows (rpg-designer ruling 2026-10-31, relayed in ruling 6/7; slot go: one instrumented urban_political s42 2000t pair plus one short P1 re-run)

Measurement only, read-only logging in scratch; no fix shape. Wrapper as in the sweep (`systemd-run ... MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`, PYTHONHASHSEED=0, audit_mode, MemAvailable >= 3 GB, sequential). Runs: D4_a (a25619971, 217 s) and D4_d (d914bace7, 218 s) of `urban_political_seed42_2000t` via `tools/evaluate_simq.py --scenario`, then one P1 re-run at d914bace7 (49 s). Scripts here: `probe4.py` (the 2000t probe), `probe5.py` (entity 10), `designer_counts.py` (check 1), `first_record.py` (ruling 7), `g.sh` (the launch order).

## Ruling 7 wording
State equality inside the prefix is inferred from the event stream, not hashed. The binding confirmation of the prefix check is that the longer run's first difference is the same record as the probe's: `first_record_output.md` shows it for s42 (index 700, t64, cooperation_event, entity 18) at 200t, 500t, 1000t and 2000t and for s123 (index 1687, t111, decision_diverged_by_belief, entity 10) at 500t and 1000t, identical to the probe pairs P3 and P1 (event_id and run_id excluded). For the repeat test the equal final state hash 0bd536588c14d9c5 stands as the binding check.

## Re-anchor reason form for P1, P2 and P4 (ruling 7)
"path starts at retreat_pull, tX entity N": P1 t75 entity 5; P2 t41 entity 19; P4 t42 entity 18. P1's ECONOMY gap from t111 to t435 stays recorded as untraced. COGNITION is not part of this check.

## Check 1: RESULT = PASS RULE NOT MET (reported as a STOP to rpg-planner)
Definitions used (cited in `designer_counts.py`): threat present = `acting_threat_to` (`src/ai/goals/present_threat.py:34`, `hostile_acts_on` in `src/engine/tactical_threat.py:114`) OR a perceived hostile orthogonally adjacent (decision 32, `LegalityServiceV2.is_adjacent`); hp line = hp ratio 0.5 (`CombatRetreatScorer`, `src/ai/goals/scorers.py:230-231`: `hp_ratio >= 0.5 and not emotion.is_fleeing` gives utility 0). Retreat-active = the entity's current project id is a combat_retreat project.
Positive control (entity 18, t42): acting True, adjacent True, hp ratio 0.25, one retreat_pull record (84.519 to 123.399), classified "threat, hp<0.5": the classifier fires on the known case.

d914bace7, s42 2000t, after t452 (full tables in `D4_d_counts.md`):

| | ticks | threat, hp<0.5 | threat, hp>=0.5 | no threat, hp<0.5 | no threat, hp>=0.5 |
|---|---|---|---|---|---|
| retreat-active project ticks, all entities (only entity 18) | 950 | 0 | 0 | 208 | 742 |
| ticks with a retreat_pull call that changes a score | 0 | 0 | 0 | 0 | 0 |
| ticks where COMBAT_RETREAT is the top raw score of a scoring call | 0 | 0 | 0 | 0 | 0 |

Retreat project spans (whole run): entity 18 only: proj_combat_retreat_42 at t43-52 and t63-1402 (replaced by proj_fatigue_1402 at t1403). No retreat span is open at the last tick; the project does end (t1402). So the second part of the pass rule (no project that never ends) is met, and the first part is not: 742 ticks with no threat present and hp at or above 0.5 (and 208 more with no threat and hp below 0.5). Entity 18 reaches town_center (25,25) by t200, then stays within a few tiles of it with hp rising from 10 (t200) to 95 (t1200); the project is still its current project at t1402. After t452 there is no retreat_pull call and no tick where retreat is the top raw score, so the pull is not what keeps the project; what holds it, and what ends it at t1402, is not traced. Parent a25619971 (`D4_a_counts.md`): no entity holds a combat_retreat current project at any tick of the run; COMBAT_RETREAT is the top raw score on 10 ticks after t452 (entities 5, 6, 14; 9 with no threat and hp<0.5, 1 with a threat) and never becomes a project.

## Check 2: what started the parent's t1666 wave (`D4_wave_t1666.md`)
Engagement: entity 14 (bandit_company GUARD) meets entity 1 (town_council WORKER) at (44,28)/(44,29) on t1665; opportunity attacks both ways at t1666 (CAUGHT_FLEEING). Preconditions at the parent: both alive; bandit_company/town_council diplomatic state TENSE since t417 (tension 0.51). At d914bace7: entity 14 died at t452 (killed by entity 8; in the parent it survives to t1809) and pair tension stays 0.31 (never TENSE), so neither precondition exists. Shown: the absence of both. Not shown: why entity 14 dies at t452 at d914bace7 (a further split after the t42 retreat, untraced); that the parent's engagement needs the TENSE state (hostility is catalog-driven; TENSE co-occurs, it is not demonstrated to be required).

## Check 3: P1 entity 10 (`P1_entity10_path.md`)
No preemption or bypass. After `ScoreModifierSystem.apply_modifiers` (`src/ai/score_modifiers.py:32-68`) COMBAT_RETREAT is 121.8 and RESOLVE_BLOCKER 100.7; `intelligence.py:1586-1593` takes the highest modified score; `evaluate_project_switch` with no current project (`intelligence.py:1072`) adopts it. The parent's retreat (88.3 raw, about 76.8 modified, computed not run) stays below 100.7. The pull is gated on `acting_threat_to` (`scorers.py:238`). It does not fire on retreat_pull outside the normal score comparison. The raw order I compared earlier was before the modifiers.
