---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE
phase: done
date: 2026-10-20
tags: []
---

# TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE

## Title
Put both survival pressures on one escalation scale: combat_retreat gets the need-pull escalation once hp is in its own consequence band

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
**Raised to P1, first rpg item after v1 (designer, 2026-10-21).** This shape is behind two of the three v1 owned known reds (v1_disclosure N15), recorded under the user's v1 cutoff of 2026-10-21. In both, a starving subject at near-death hp keeps fleeing a present catalog-hostile (Tier 1, correct by design) until it starves, because hunger and flight are not on one escalation scale.
- crowded_frontier s46, raider 38 (orc_clan), STARVATION at t3778, step 2 f9b21b55b:
  - hp 3-7%, 0 gold, no food;
  - PANIC_RETREAT from leader 30 (goblin_warband, hp 131, 2-13 tiles away) on 131 of 198 ticks between t3580 and t3777, while the hunger project is current;
  - an unthreatened open way existed in 9 of 9 retreat samples (the inn in 6 of 9).
- frontier_living_world s44, worker 2 (town_council), STARVATION at t3736:
  - hp 0.1-1.4%; PANIC_RETREAT from leader 30, predator_hunter 34 and alpha 49 (all catalog-hostile) on 150 of 236 ticks;
  - town_return (about 163.5) beats hunger (160) only through TownScorer's low-hp term (about 59): a wound-driven return to safety, also Tier 1;
  - an unthreatened open way existed in 13 of 19 retreat samples.
- Probes: /mnt/data/scratch-rpg-implementer/probes_hs/ways_probe.py and tick_log.py; data in /mnt/data/scratch-rpg-implementer/paired_en2/wp_raider38.json, wp_worker2.json and paired_en/v3btr/.
- The parked safe-route step (TCK-20261020-PARKED-HUNGER-SAFE-ROUTE-STEP-AFTER-V1) moves only the objective, so it cannot clear a tactical panic. The design here has to put the two pulls on one scale.
- Related: worker 2's goblin leader sits 2-11 tiles away for about 200 ticks without engaging, which is C4's shape (a hunter beside a subject without engaging, decision 47).

This is backlog, parked by the designer on 2026-10-20. Build it only if data shows a subject eating into a fatal attack.

V3 step (ii), on rpg-v3-starvation-threat at 70402779d, keeps the escalated hunger pull under a present threat once hunger is past STARVING_LINE (95). At the goal level, that pull is 155-160: raw hunger plus ESCALATION_AMPLITUDE 60 (need_pull.py). CombatRetreatScorer is 100·(1−hp_ratio) + 50·panic − 30·bravery, with a ceiling of 150, so the starving pull beats every reachable retreat score. The designer ruled the weighing is by immediacy: an acting threat still pre-empts in the tactical pass. The long-run unification it noted is to escalate retreat the same way, so both pressures saturate on one scale and the appraised threat decides.

## Scope
- Apply the existing ESCALATION_AMPLITUDE and smoothstep to combat_retreat once hp is past its consequence line. No new constant.
- Measure it as its own step: paired 3 × 42-46, crowded first. Retreat changes in every world.

## Out of Scope
- Any change to the hunger pull or to tactical ordering.

## Acceptance Criteria
- At hunger 95+, a strong enough appraised threat makes retreat outscore hunger, pinned by a unit test.
- The paired measurement passes the stop line, or the result goes to the owner.

## Related Tickets
- the V3 step (ii) ticket on rpg-v3-starvation-threat (SURV-07, memo row 83)

## Related Docs
- docs/mechanics/04_strategic_cognition.md §1
- docs/world_rules SURV-07

## Related Stored Artifacts
- none

## Related Code Areas
- src/ai need_pull.py (ESCALATION_AMPLITUDE, smoothstep)
- scorers.py CombatRetreatScorer (~213-240)

## Assumptions / Open Questions
- Design point to rule here (designer, 2026-10-21): "a hostile acting on the subject" (owner_decision_memo rows 83 and 84, N3) is read today by `present_threat_to` (src/ai/goals/present_threat.py:23-26), whose terms in src/engine/tactical_threat.py:60-78 are states: WOUNDED (hp < 0.7), ADJACENT (≤ 1.0), CLOSING, OUTMATCHED (≥ 1.5×) or TARGETED. Any one term counts. So a hostile resting beside a wounded subject counts as acting.
  - Evidence: crowded s43 guard 11 on step 2 (f9b21b55b). present_threat_to is True on every sample from t1984 to t2140 with only WOUNDED, ADJACENT and OUTMATCHED held, while raider 35 rests and raider 37 sleeps. The guard holds in place for about 180 ticks, starving (hunger 100, -1 hp per 24 ticks), and its hunger project is never served (probe probes_hs/ptt_probe.py).
  - The designer will rule here that "acting" becomes an act (targeted, attacking or moving at the subject), not a state. The tactical hold (tactical.py:209) and the goal-level weighing (SURV-07 (ii)) must share that one definition.
  - Disclosed in v1 in C4's row.
- The trigger is evidence of a fatal eat-under-attack. Without it, this stays parked.

## Implementation Notes
After v1, only if the trigger is seen.
- 2026-10-23, rpg-planner brief: this ticket is STEP A only, the retreat escalation in CombatRetreatScorer, measured as its own paired step (`--base 341f700d0`, seeds 42-46, 3 worlds, 5000 ticks, crowded first, after the planner says the host is free). It does not touch `present_threat_to`, `tactical_threat.py` or `tactical.py:209`. STEP B, "acting" meaning an act and not a state, is its own ticket on this branch, filed after the designer rules, and is measured with step A's tip as its parent.
- 2026-10-27, paired run 8d76615ba vs 3533fde71 STOPPED (frontier_living_world: blacksmiths 2 to 0, merchants 15 to 21 dead, worker HAZARD 5 to 10). Offline attribution (`/mnt/data/scratch-rpg-implementer/stepA/attr/SUMMARY.md`): divergence always starts at the first COMBAT_RETREAT flight, and the deaths cascade through hostile leader id30 (seeds 42, 43). Context for the ruling (`attr/flight_context.txt`, a proxy: hp trend plus nearest kinds, faction guessed; present_threat_to is not in the files): of 75 flights in the 5-seed, 3-world probe, 65 were issued with no acting hostile, and 58 of those came while the subject was regenerating with same-side kinds adjacent. Only 7 had lost hp in the 30 ticks before. Flights re-issued every 20-100 ticks per entity.
- 2026-10-27, rpg-designer ruling option (i) via rpg-planner, reversing "no acting gate": the COMBAT_RETREAT flight is issued only on a brain decision tick where `acting_threat_to` holds, and a held one ends at the first brain decision tick where it does not (read on decision ticks only). No present-threat gate; CombatRetreatScorer unchanged. Built in `combat_retreat_flight.py` (the act is passed as a thunk from `intelligence.py`, so it is read only when a COMBAT_RETREAT project or flight is in play). Docs: 2.139 "Flight" bullet, parity STRAT-289. The Bible 02 §7 CONFLICT-04 sentence is with the designer for wording. A new paired run on the gated build replaces the stopped one.
- Review note (health, 2026-10-27): the gate first raised one NEW row (ruff PLR0913, 6 params on `combat_retreat_flight_update`) and made intelligence.py one line longer (an import). Both were fixed structurally, with no baseline edit: the module derives the current project id itself (the same expression as `intelligence.py`, `strat_up` is not reassigned in between; covered by a new test), and `acting_threat_to` is re-exported from `src.ai.goals` onto the existing import line. Health: 0 new, the same 3 recorded "worse" rows on intelligence.py as at 8d76615ba (override already recorded).
- Review note (wide scope on 00e4645fa, 2026-10-27): 9162 passed. Four failures are ORDER-DEPENDENT, each passing alone: `tests/integration/kernel/test_authoritative_outcome_truth.py::test_replay_sources_from_refined_update`, `tests/certification/test_envelope_violations.py::test_harness_detects_missing_degradation_mode`, `tests/certification/test_harness_contract.py::test_certification_detects_semantic_drift`, `tests/certification/test_resilience_recovery.py::test_harness_catches_failed_recovery`. The fifth, the pinned mechanism-registry count (66 vs 65), is this ticket's: per #593 6420327798 (rpg-planner-ubuntu agreed) the step A PR carries both bindings. `strategic_intelligence_core` += `combat_retreat_flight_update`, and `tactical_decision` += `hostile_acts_on`, `acting_threat_to`. The pins move as the check reports: total_targets 65 to 66, bound 53 to 54, unbound 8; wider unbound_files 251 to 250 (present_threat.py now bound). Registry validate OK (107); generated views unchanged. If #757 has merged by push time and conflicts: take main's file plus these bindings.
- 2026-10-27, gated paired run 85515ca12 vs 3533fde71 STOPPED again: frontier_living_world 123->146 (+23, SE 2.11), blacksmith extinct; urban_political 60->74 (+14, not past 2·SE); crowded_frontier +2. Report: `/mnt/data/scratch-rpg-implementer/stepA/paired_gated.log`. Attribution (`stepA/gate/SUMMARY.md`; arms base, G = gated, R = flight made a no-op at runtime; frontier s42/s43, urban s45): G has 1-4 flights per seed, all issued under an acting hostile. Its first divergence is always a flight, and the drift cascades through a hostile that base kills early (leader 30 in frontier, scouts 15/16 in urban). R also drifts in frontier s43 (26->40 deaths, blacksmith killed by leader 30). Churn (lapse-end then re-issue) is rejected: 1 lapse-end in total, no re-issue.
- KNOWN LABEL GAP (rpg-designer ruling via rpg-planner, 2026-10-27): a held COMBAT_RETREAT flight keeps the subject's existing movement_mode (REGROUP 38, PURSUE 8, HOLD 1, RETREAT 0 entity-ticks in the attribution runs), though by meaning it is a retreat. It is NOT relabelled in step A, because movement_mode is read for decisions:
  - speed factor (`src/engine/movement.py` `_move_speed_mult`: RETREAT 1.5, REGROUP 1.0, PURSUE 1.2, HOLD 0);
  - the EVASIVE opportunity-attack skip (`src/engine/movement.py:287`, RETREAT only);
  - the acting test (`src/engine/tactical_threat.py` `_task_acts_on`, PURSUIT_MODES);
  - the tracked-move target refresh and the WANDER admission cadence (`src/engine/candidate_selector.py`);
  - `resolve_move`'s mode (`src/engine/pipeline_phases/movement.py:238`);
  - HOLD resting (`src/engine/apply.py:165`), the HOLD swap block (`pipeline_phases/movement.py:326-328`, `src/engine/movement.py:91`) and the social appraisal (`src/systems/social_systems/appraisal.py:272-275`);
  - the flee/pursuit counters (`src/observability/run_ledger.py`).
  The relabel is its own measured step after M1. In the gated run, the two first-step deaths (frontier s42 raider 27 at t115, base t121; urban s45 worker 5 at t217, base t225) both happened at REGROUP speed 1.0 with the opportunity attack paid.
- 2026-10-27, arm R paired run. R is 358f4cb7f: 85515ca12 with the flight made a no-op, on the local scratch branch, never pushed. Base is 3533fde71. Report: `/mnt/data/scratch-rpg-implementer/stepA/paired_R_report.md`.
  - frontier_living_world: 123->139 (+16, SE 2.48). The death count alone shows no drift. It is a STOP on the extinction rule: scout 2->0 and wild_creature 6->0 alive, summed over seeds.
  - urban_political +2, crowded_frontier -2, no drift in either. Self-check spread 0.
  - So frontier's STOP is not specific to the flight. It goes to the owner as an extinction-sensitivity question.
  - Seed 43's last wild_creature (id52) died at t1349 in COMBAT, killed by worker 2. Neither entity ever had a COMBAT_RETREAT project or decision, so the death is cascade only. Per rpg-planner, the other extinctions fall in s44 and s46, from cached fates.
- 2026-10-27, capacity-refusal confirm runs: R and base, frontier s42 to t531 and s43 to t326. Data: `stepA/confirm/`, probe `stepA/confirm_probe.py`, all-status dump `stepA/proj_dump.py`.
  - Every COMBAT_RETREAT capacity check is refused: R 19/19, base 13/13. `escalated_need_wins` (src/ai/goals/escalation.py:18-29) is True only for HUNGER and FATIGUE.
  - A refusal (`intelligence.py:1773-1776`) returns an empty `StrategicUpdate`. On every refusal tick, current project and live set are unchanged, so no live project is dropped.
  - R first diverges at s42 t530 guard 11 and s43 t326 scout 15. On those ticks base's winner, combat_engage, gets past the full cap. `intelligence.py:1610` takes `existing` as the first same-kind project of ANY status, and here it is COMPLETED or ABANDONED. So `:1612` does not resume one of the three SUSPENDED engages, and `:1773`'s `not existing` skips the capacity check.
  - Base therefore creates a new ACTIVE engage. The capacity trim then evicts its oldest SUSPENDED sibling.
  - A first-time kind like COMBAT_RETREAT gets no such bypass and is refused. Whether that is a bug, and of which ticket, is with rpg-designer. Nothing is coded.
- 2026-10-27, counters (approved by rpg-planner and rpg-designer): `combat_retreat_flight_ticks` and `combat_retreat_flight_episodes` in `RunLedger._count_modes`.
  - Keyed on the task: an ENTITY_MOVE with payload reason COMBAT_RETREAT, whatever movement_mode it holds. An episode is a tick that enters it.
  - The flee and pursuit counters are unchanged. `tools/rpg_measure/paired.py` reports both new counters.
  - The ledger counters are in neither the canonical hash nor the replay fingerprint. Both read only `AuthoritativeState`: `CanonicalStateHasher.get_hash(state)` via `CanonicalHashScheduler.compute_digest` (kernel `_phase_persistence`), and `StateFingerprinter.get_fingerprint(state)` (src/replay/fingerprint.py). `RunLedger` keeps class-level counters and only emits events through `extract_events`, writing nothing to the state.
  - Tests: 3 new in `tests/unit/observability/test_run_ledger_behaviour.py`. Observability and tools unit scope: 2259 passed.
  - Health: 0 new; the same 3 recorded "worse" rows on intelligence.py.
- 2026-10-28, OWNER DECISION (#715 issuecomment-6458811768, memo row 91; read on the owner's account): land R only. R is the acting-gated retreat_pull without the flight.
  - The flight is parked on the local branch `rpg-hunger-retreat-flight-parked` (5318f71e0, never pushed). It returns as the post-M1 regroup-to-retreat relabel step, together with the COMBAT_RETREAT escalated-need capacity exemption.
  - The extinction rule is unchanged. R's frontier STOP (scout, wild_creature) is accepted as known.
  - The capacity-lookup defect (`intelligence.py:1610`) is TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED, after step A.
- 2026-10-28, strip (5a992936f): src/ is byte-identical to 61648f417, the pre-flight step A (`git diff 61648f417 5a992936f -- src` is empty).
  - Registry: `combat_retreat_flight_update` is dropped. The `tactical_decision` citations `hostile_acts_on` and `acting_threat_to` are kept, because the retreat_pull gate reads them.
  - Part of step A: the CONFLICT-04 no-freeze invariant measure fix (designer ruling 2026-10-26, a measure fix, not a re-pin; it came in with 761fad2b1). On R the raw longest blocked run is 19 (entity 6, the stored-target shape) and the longest run with no decision is 10 (bound 11). The original measure fails on R (19 > 11).
- 2026-10-28, merged origin/main through #758 (924ee21fd). Conflicts: divergences (2.140 from main, kept beside 2.139) and the mechanism pin test (main's dead-class note and wider 249; with present_threat.py bound, wider 248; 14 passed).
  - Proof that the landed src is R, accepted by rpg-planner with no neutral run: `git diff origin/main 924ee21fd -- src` has hunks identical to `git diff 3533fde71 61648f417 -- src` (need_pull.py `retreat_pull` and scorers.py, same hunk headers; only the scorers.py blob ids differ, from main's docstring edit).
  - `git diff 61648f417 358f4cb7f -- src` (R as measured) is only the no-op flight module (early `return ent_upd`, so the acting_threat_to lambda is never evaluated), its call and import, FlightReason/DECIDED_FLIGHT_REASONS, and COMBAT_RETREAT in two reason sets that nothing in R issues.
- 2026-10-28, equivalence proof (rpg-planner's optional check). Run: frontier_living_world s43, 5000t, at 5a992936f (pre-merge, digest scheme v2), arm child 72320cac via `paired.prepare_tree`/`run_one`.
  - Matches the cached R arm `358f4cb7fa18-72320cac-5000/frontier_living_world_43.json` on final_hash (8f46ae0e...), start_hash, audit_mode, signals_zeroed, counters and final fates.
  - Output: `/mnt/data/scratch-rpg-implementer/stepA/hashproof/`.
- 2026-10-28, docs (rpg-designer wording, relayed by rpg-planner; numbers checked against the code at 5a992936f):
  - Bible 02 §7 sentence (R: stored target, no step, until the flight step after M1).
  - Bible 04 §1: the escalation list names CombatRetreatScorer; a new "A wound escalates like a need" paragraph covering the act test, bravery F1 (memo row 91), no capacity exemption, and CONFLICT-04; the row 83 ceiling sentence.
  - Divergence 2.139: "No flight" bullet, the starving-retreat sentence, Measured, and the held-flight note.
  - STRAT-288 support_boundary updated; STRAT-289 removed.
  - SURV-07 clause on bravery.
- 2026-10-28, health: the 3 "worse" rows on intelligence.py recorded at 8d76615ba (override) went away with the flight call. On the landed tip health is OK (0 new, 0 worse), so that override no longer applies.
- 2026-10-28, merged origin/main at fc040dee4 (#765 F4 stable_hash, #767) as 002f68566. The only conflict was the wider unbound pin: main's 250 (+stable_hash.py), and our present_threat.py binding gives 249. The byte proof is repeated against the new main, and the hunks are identical.
- The hp consequence line and the threat gate are proposed in `agent-working/staging_artifacts/TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE/plan.md`. No code is written until the designer confirms them.

## Test Summary
- New: `tests/unit/ai/test_retreat_escalates_on_the_need_scale.py` (7 tests): acting hostile at hp <= 15% puts retreat above the starving pull; the non-acting scene is unchanged (<= 150); no escalation at hp >= 40%; monotone between 0.6 and 0.85; nothing in view leaves it unchanged.
- Changed: `tests/mechanic_scenarios/test_conflict04_movement_layer.py`, the no-freeze invariant measured per decision (designer ruling 2026-10-26). On R the raw longest blocked run is 19 and the no-decision run is 10 (bound 11). Mechanism pins: `tests/unit/tools/test_mechanism_registry_completeness_check.py` (wider unbound 249 after main's 250).
- Unchanged and green: the retreat-ceiling pin (`test_starvation_is_a_present_threat_weighed_in_goal_selection.py`) and the merchant-37 real-kernel test.
- Wide scope on 24f083cb3 (unit, integration/{kernel,observability,pipeline}, certification, mechanic_scenarios, -m "not slow"): 9164 passed, 11 skipped, 1 xfailed, 4 failed. The 4 are the known order-dependent failures, and each passes alone (4 passed):
  - `tests/integration/kernel/test_authoritative_outcome_truth.py::test_replay_sources_from_refined_update`
  - `tests/certification/test_envelope_violations.py::test_harness_detects_missing_degradation_mode`
  - `tests/certification/test_harness_contract.py::test_certification_detects_semantic_drift`
  - `tests/certification/test_resilience_recovery.py::test_harness_catches_failed_recovery`
- After the fc040dee4 merge: the scoped tests touched by the merge pass (stable_hash, faction/perception hashseed, step A, CONFLICT-04, retreat-ceiling, merchant-37, tests/unit/tools).
  - `tests/codebase` cannot run in the project venv: its tool tests need ruff, mypy and ast-grep. It was covered instead by the gates in the deps venv: health OK (0 new, 0 worse), mypy clean, import contracts 17 kept.
- Equivalence: frontier_living_world s43, 5000t, at 5a992936f gives a final_hash identical to the measured R build 358f4cb7f.

## Files Changed
- `src/engine/need_pull.py` (`retreat_pull`), `src/ai/goals/scorers.py` (`CombatRetreatScorer`, gated on `acting_threat_to`)
- `tests/unit/ai/test_retreat_escalates_on_the_need_scale.py` (new), `tests/mechanic_scenarios/test_conflict04_movement_layer.py`, `tests/unit/tools/test_mechanism_registry_completeness_check.py`
- `registries/mechanisms.yaml` (`tactical_decision` cites `hostile_acts_on`, `acting_threat_to`)
- `docs/mechanics/02_combat_laws.md` §7, `docs/mechanics/04_strategic_cognition.md` §1, `docs/guidelines/intentional_divergences.md` 2.139, `docs/parity_ledger/strategic_cognition.yaml` STRAT-288, `docs/world_rules/life-body/survival-needs.md` SURV-07
- Ticket, staging artifacts, monitoring shards, `docs/REGISTRY.yaml`

## Completion Summary
Step A lands R only (owner decision #715 6458811768, memo row 91): the goal-level retreat score escalates with the wound on the need scale (+60 smoothstep between damage fractions 0.6 and 0.85), and only while a hostile acts on the subject.
- A chosen retreat stays a stored target that takes no step (CONFLICT-04).
- Measured R against step B (3533fde71), 3 worlds × 5 seeds × 5000t: no death-count drift. frontier_living_world has an extinction STOP (scout, wild_creature), accepted as known.
- The landed src is equivalent to the measured build: by argument, by byte proof against main, and by a final-hash match on frontier s43.
- Held and not landed: the decided COMBAT_RETREAT flight (G: frontier +23 STOP), on the local parked branch `rpg-hunger-retreat-flight-parked`, with the CR capacity exemption, for the post-M1 relabel step.
- Separate: the capacity-lookup defect is TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED.
