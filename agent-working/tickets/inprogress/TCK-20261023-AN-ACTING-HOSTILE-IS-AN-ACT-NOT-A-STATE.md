---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE
phase: inprogress
date: 2026-10-23
tags: []
---

# TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE

## Title
A hostile "acts on" a subject only by an act (an attack or pursuit aimed at it, or a hit that landed), not by a state (wounded, adjacent, closing, outmatched)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
STEP B of the hunger-and-retreat work, built FIRST (designer ruling, confirmed by the user on #715 comment 6356212656). TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE stays as step A and is measured on this ticket's tip (decision 76: each step is measured once, at fold, against its parent).

Owner decision memo row 88 (`docs/plans/systemic_world/owner_decision_memo.md`, commits 03d041abc and the item (5) fixup b845ac76e), verbatim:

> **DECIDED by rpg-designer, confirmed by the user in rpg-designer's terminal, 2026-10-23.** (1) **Acting is an act, not a state.** A hostile is acting on a subject only when the subject perceives it AND (a) the hostile's current task is an attack or pursuit with the subject as its target, or (b) the hostile took hp from the subject by a hit since the subject's previous decision (opportunity hits included). (b) needs a typed last-hit tick next to `CombatComponent.last_attacker_id`. Being wounded, a hostile merely adjacent, a hostile closing without targeting (and `CLOSING` is sticky today: `last_position` is written only on a move), and being outmatched stay AGENCY-07 reasons that flight is warranted. They no longer hold back an escalated need. (2) **Where it applies (shape S1):** the SURV-07 bypass of an escalated need (row 83), the hunger and sleep escalation, the tactical panic hold (under an escalated need a panic retreat and the freeze yield unless a hostile is acting), and the retreat-escalation gate of (3). Resting or eating in place and the cautious safety retreat keep the full AGENCY-07 terms; widening those is a separate question (SURV-06). (3) **Retreat escalates as a need does, with no new constant:** wound = 1 − hp share, whose consequence line is death; `ESCALATION_ONSET` 0.6 and `ESCALATION_FULL` 0.85 put the onset at hp 40% (the existing panic and cover edges) and the full escalation at hp 15% (the existing pure-retreat edge). It is gated on an acting threat: a lone starving, wounded subject still goes to eat (SURV-07). (4) **Order:** the act-based test is its own measured step first; retreat escalation is measured on top of it. (5) **Details, rpg-designer, same day, on Lane A's reader map:** (a) counts only typed work: an attack act (ATTACK, SKILL, HOLD_BETWEEN_BLOWS) or a PURSUE, INTERCEPT or BRACKETING move, each with the subject as target; watching, guarding, kiting, cover and chokepoint holds do not count. An attack task kept current until the hostile's next decision still counts, without a reach test (at most one decision late, like the perception lag of C5). (b)'s window is `NEED_WAKE_CADENCE` (10 ticks) since the last hit, and the last-hit tick belongs to `last_attacker_id`. The panic hold yields only once the need is past its consequence line (hunger 95, sleep debt 98), where the need already takes health and so is itself a present threat (row 83). Below the line an emotional panic flight stands.

Dispatch additions (rpg-planner, 2026-10-23): `BRACKETING` counts only when its typed target is the subject; an attack task kept current until the hostile's next decision still counts, with no reach test (a known property, below); `last_hit_tick` is always emitted and hashed; the panic hold yields only past the need's consequence line (hunger >= 95 or sleep debt >= 98), and the goal-level consumers keep their thresholds and only swap in the act test.

Known property: an ATTACK task stays current until the hostile's next decision (`executor.py` re-sets the payload after execution), so a hostile that attacked and then lost reach counts as acting for at most one decision (the lag class of C5).

Why: v1_disclosure N15 (two owned known reds) and C4 (guard 11 holds in place about 180 ticks, starving, beside a resting raider and a sleeping one). `CLOSING` is sticky: `navigation.last_position` is written only on a successful move.

## Scope
- A typed `last_hit_tick` on `CombatComponent`, written by `CombatPatch.apply` when `damage_taken > 0` (the same place as `last_attacker_id`, `patches.py:329`), added to `to_canonical_dict` (hashed; see plan.md).
- One acting predicate (pure read) used by the SURV-07 bypasses and the panic hold under an escalated need.
- Tests, docs and parity as listed.

## Out of Scope
- Step A (retreat escalation) and the hp line.
- `tactical_rest`, `safety_retreat_warranted`, panic start (cognition.py), engaged retreat, the CLOSING term itself.
- The hunger pull and the tactical order.
- Fixing hash coverage of other state (#593 F1).

## Acceptance Criteria
- A hostile that is only adjacent, closing, outmatching or merely present does not hold back an escalated need or hold a subject in a panic freeze; a hostile whose current task attacks or pursues the subject, or that hit it within the window, still does.
- Rest in place, eat carried, eat at carcass and the safety retreat behave exactly as before.
- `last_hit_tick` is typed, hashed, round-trips, and is written only by CombatPatch on damage.
- The named pins change as listed; the merchant-37 real-kernel test stays green.
- Paired measurement on B's tip passes the stop line, or the result goes to the owner.

## Related Tickets
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE (step A, measured on this tip)
- the V3 step (ii) (SURV-07 row 83)

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-07, rows 83/84/88)
- docs/world_rules/knowledge-agency/agency-decision.md (AGENCY-07)
- docs/mechanics/04_strategic_cognition.md §1
- docs/plans/systemic_world/owner_decision_memo.md row 88

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/tactical_threat.py, src/ai/goals/present_threat.py, src/ai/goals/scorers.py:61-75
- src/engine/tactical.py:203-219
- src/core/state.py CombatComponent, src/engine/patches.py CombatPatch

## Assumptions / Open Questions
- Window anchor and work-kind list: see plan.md, for the designer to confirm.
- Hash change: see plan.md.

## Implementation Notes
Built 2026-10-23 (local, not pushed). Staging: `agent-working/staging_artifacts/TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE/`.
- `CombatUpdate.hit_tick_set` is stamped with `state.tick` at the five damaging producers in `src/engine/combat.py` (resolve_attack, resolve_skill_usage, resolve_multi_attack, resolve_aoe_attack twice); `CombatPatch` writes it to `CombatComponent.last_hit_tick` when `attacker_id` is set and `damage_taken > 0`, the same condition as `last_attacker_id`. The patch has no tick of its own, so the update carries it (the `death_tick_set` pattern).
- `hostile_acts_on` (src/engine/tactical_threat.py, the engine layer so `tactical.py` can read it) and `acting_threat_to` (src/ai/goals/present_threat.py). The goal-level bypasses in scorers.py swap `present_threat_to` for `acting_threat_to`; thresholds unchanged.
- Panic hold: `_panic_holds` (tactical.py) yields past hunger 95 / sleep debt 98 unless a perceived hostile acts.
- Hash (perf ruling PERF-D5 (ii), 2026-10-24, #593 comment 6384425767, #715 6384423281): `last_hit_tick` stays typed durable state (always emitted in `CombatComponent.to_canonical_dict`, pickled in scenario checkpoints) but is excluded from the proof digest only, by name, at `DIGEST_EXCLUDED_COMBAT_KEYS` in `src/engine/checkpoint.py` with a pointer to F1 (`TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS`). `PROOF_DIGEST_SCHEME` stays flat-sha256-v2 and `test_proof_digest_contract` is untouched and green. The PR names the gap: the final hash and paired hash-equality proofs cannot see divergence in `last_hit_tick` until F1; step B's evidence is counters, fates and extinction rows. No read model or debug view shows `last_attacker_id` (searched `src/`: only death records and the patch), so none needed `last_hit_tick`.
- Code-health ratchet kept flat without raising any ceiling: stamps inlined on the `attacker_id` lines, comments reflowed in state.py and updates.py, the panic decision lives in a module-level helper.
- BRACKETING is recognised by its reason string because REPOSITION also carries SEEK_COVER (the one reason-string read).

## Test Summary
Scoped runs (`PYTHONHASHSEED=0`, `-n 0 --resource-budget off`): `tests/unit tests/integration/{kernel,observability,pipeline} tests/certification tests/mechanic_scenarios -m "not slow"`: 9030 passed, 7 failed. Of the 7: four are order-dependent flakes (listed below), one is retired (below); the two digest tests pass unedited under perf's ruling (ii).
New: `tests/unit/engine/test_acting_hostile_is_an_act_not_a_state.py` (23). Health ratchet OK (0 new, 0 worse), mypy gate clean, import contracts 17 kept 0 broken.

Pins that changed meaning (old -> new; the planner's yes covers exactly these):
| Test | Old | New |
|---|---|---|
| unit/ai/test_need_scorers.py::test_a_present_threat_takes_the_escalation_away... (renamed ..._a_hostile_acting_on_the_subject_takes...) | an adjacent monster with no task drops the escalation to the raw hunger | an attacking (ATTACK, target = hero) or pursuing (PURSUE) monster drops it; adjacency alone keeps it (new test); hit window boundary (new test) |
| unit/ai/test_opening_steps.py::test_a_present_threat_outranks_the_pull_to_the_node | monkeypatches `present_threat_to` | monkeypatches `acting_threat_to` (same assertion) |
| unit/ai/test_starvation_is_a_present_threat_weighed_in_goal_selection.py::..._not_past_its_line_still_has_the_pull_dropped_under_a_threat | adjacent hunter drops the hunger-80 pull | hunter targets the merchant (ATTACK) to drop it; a merely adjacent hunter keeps it (new test) |
| ...::test_a_subject_in_the_desperation_band_with_a_hunter_really_attacking... | the monster had no task | the monster's task is ATTACK on the hero (matches the docstring); assertion unchanged |
| unit/tactical/test_held_panic_falls_through.py::..._real_destination_still_flees (renamed ..._flees_a_hunter_that_attacks_it) | an adjacent resting hunter holds a hunger-100 merchant in PANIC_RETREAT | the hunter attacks to hold it; resting: no PANIC_RETREAT; hit within the window: PANIC_RETREAT; hunger 80 resting: PANIC_RETREAT; sleep line: yields (4 new tests) |
| unit/progression/test_species_base_stats_preserved.py::test_every_combat_component_field_survives_to_readonly | sentinel without `last_hit_tick` | sentinel includes `last_hit_tick: 27` |
| integration/observability/test_starving_wounded_merchant_eats_through_the_real_kernel.py::..._with_the_old_threat_gate_does_not_eat | control restores only the row-83 bypass | control also restores the state-based gate (`acting_threat_to` -> `present_threat_to`) |
The main merchant-37 test stays green unchanged.

Retired, awaiting perf, and unrelated failures:
- unit/engine/test_proof_digest_contract.py::test_flat_hash_of_fixed_fixture_is_pinned_under_v2 and ::test_v2_is_v1_without_the_two_removed_keys: schema key added. The fixture digest `41b03d22...` becomes `e26f9383b6f18550ae3235b8c9499d34a241c8c80080e7a7cdebeece0d33d484`; the v1 migration proof needs the new key removed from the rebuilt v1 form. The file says the v2 digest "must never change without a new scheme version", and a bump touches perf docs (benchmark_identity_schema enum, baseline_invalidation_ledger): a perf/#593 F1 call.
- RETIRED (planner yes, 2026-10-23; no xfail): integration/observability/test_an_escalated_need_is_never_refused_for_capacity_through_the_real_kernel.py::test_the_gate_run_blacksmith_gets_a_hunger_project_by_about_hunger_95_and_eats_before_100__pins_current_scoring_not_the_rule. A 2100-tick crowded s45 trajectory pin that declared "PINS CURRENT SCORING, NOT THE RULE". Base: hunger project at t1448 (hunger 72.4), eats, dies t1687. This step: blacksmith 13 is killed at t1449 (AVOID_HOSTILE, hunger 72.4) before any hunger project; the two trajectories split by t901 (hp 13 vs 25) because the step also changes the sleep bypass. The staged tests in the same file (`..._past_the_onset_at_a_full_cap_gets_a_hunger_project_and_eats`, `..._below_the_onset_the_cap_still_refuses`, one project per need, the 600-tick switching bound, the non-current admitted project) still prove the rule. No parity entry or divergence cites the retired test by name: STRAT-286 and 2.137 cite the file, which still holds the staged tests, so nothing was re-pointed. The TOWN-RETURN ticket's tightening note that lived in its docstring goes with it.
- RESOLVED by perf (ii): the two `test_proof_digest_contract` tests stay as they were and pass; nothing re-pinned.
- Order-dependent failures in the wide run, not caused by this step (each passes alone on the base tree and on this one): tests/integration/kernel/test_authoritative_outcome_truth.py::test_replay_sources_from_refined_update, tests/certification/test_envelope_violations.py::test_harness_detects_missing_degradation_mode, tests/certification/test_harness_contract.py::test_certification_detects_semantic_drift, tests/certification/test_resilience_recovery.py::test_harness_catches_failed_recovery. The planner files the flake ticket.

## Files Changed
src/core/state.py, src/core/updates.py, src/engine/patches.py, src/engine/combat.py, src/engine/tactical.py, src/engine/tactical_threat.py, src/ai/goals/present_threat.py, src/ai/goals/scorers.py; tests as above; docs/guidelines/intentional_divergences.md (2.138), docs/parity_ledger/strategic_cognition.yaml (STRAT-287); memo row 88 commits cherry-picked (fd64bad5b, 916d05493).

## Completion Summary
