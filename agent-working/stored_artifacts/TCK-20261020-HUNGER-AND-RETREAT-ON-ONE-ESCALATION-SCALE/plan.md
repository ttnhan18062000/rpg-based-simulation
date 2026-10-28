---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE
tags: []
---

# plan - TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE (step A)

## AS LANDED (2026-10-28; owner decision #715 6458811768, memo row 91)
- Landed: R only, which is the steps below (retreat_pull in CombatRetreatScorer, gated on acting_threat_to) plus the CONFLICT-04 no-freeze invariant measure fix (designer ruling 2026-10-26).
- Not landed: the decided COMBAT_RETREAT flight (built 2026-10-26/27 in 761fad2b1..5318f71e0, measured as G). It is parked on the local branch `rpg-hunger-retreat-flight-parked` for the post-M1 regroup-to-retreat relabel step, with the escalated-need capacity exemption for retreat.
- Measured (R vs 3533fde71) and the accepted frontier extinction STOP are in divergence 2.139. The capacity-lookup defect found on the way is its own ticket (TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED).

## CONFIRMED DESIGN (2026-10-26; supersedes the design points and steps below where they differ)
Confirmed by rpg-designer through rpg-planner (confirmations within memo row 88 (3), not a new ruling); step B (PR #753, `acting_threat_to`) is the base.
1. **Scale:** wound = `1 - hp/max_hp`, on need_pull's `ESCALATION_ONSET` 0.6 / `ESCALATION_FULL` 0.85 / `ESCALATION_AMPLITUDE` 60; the consequence line is death. The code reads the need_pull constants as the single source and does NOT tie to the panic-band constants (0.4, 0.15); their coincidence is noted in the Bible only.
2. **Goal-level term, no tactical-branch special case:** `retreat = min(raw, 150) + 60 * smoothstep(0.6, 0.85, 1 - hp/max_hp)`, added on top of the ceiling the way `need_pull` adds to raw utility, and ONLY when `acting_threat_to(entity, state)` holds. At hp 15% with an acting hostile retreat is about 210, above the starving pull of 155-160. The scorer reads no tactical-branch state.
3. **Target:** the goal-level retreat score only. N15 (the panic flight is decided in the tactical pass before goal scores) is reported, not required to clear.
4. **Pin:** `test_the_starving_pull_exceeds_the_retreat_ceiling...` stays EXACTLY as is (planner ruling); its scene has an adjacent, non-acting hunter. Add its pair: an acting hostile at hp <= 15% makes retreat exceed the starving pull. `test_starving_wounded_merchant_eats_through_the_real_kernel` must stay green.

### Steps (final)
1. `src/engine/need_pull.py`: add `retreat_pull(raw, hp_ratio)` = `raw + ESCALATION_AMPLITUDE * smoothstep(ESCALATION_ONSET, ESCALATION_FULL, 1.0 - hp_ratio)`; no new constant (the "line is death" fraction is the literal 1.0 of the damage fraction, named in the docstring).
2. `src/ai/goals/scorers.py` `CombatRetreatScorer.score`: after the raw utility (the early return at hp >= 0.5 and not fleeing is unchanged), `utility = retreat_pull(utility, hp_ratio) if acting_threat_to(entity, state) else utility`. Target and destination unchanged.
3. Docs in the same change: Bible 04 section 1 (retreat escalation on the need scale, gated on acting; the designer drafts the sentences once the diff exists), SURV-07 world rule ("As built"), `intentional_divergences.md` new 2.x (Intentional Gameplay Change, Measured pending), a new parity entry STRAT-xxx (P1, test_path).
4. Tests: new file `tests/unit/ai/test_retreat_escalates_on_the_need_scale.py`: (a) acting hostile at hp <= 15% -> retreat > 160 (above the starving pull); (b) the same scene non-acting -> retreat <= 150 (unchanged); (c) hp 40% or more with an acting hostile -> no escalation (smoothstep is 0 at the onset); (d) monotone in the damage fraction between 0.6 and 0.85; (e) nothing in view -> unchanged. Existing pins unchanged.
5. Gates: scoped tests, health ratchet, mypy gate, import contracts.
6. Measure on step B's merged tip (or the branch tip if #753 is not yet merged): paired against step B's tip, seeds 42-46, 3 worlds, 5000 ticks, crowded first, jobs 1, `--self-check seed42`, after the planner says the host is free; apply decision 76 per step (memo row 86): people deaths per world, the per-seed extinction output, starvation deaths, the N15 rows.

### Risks to watch
- The merchant-37 real-kernel scene: the hunter there must not read as acting, or retreat (~210) would outbid the meal and break row 83's fix; check its hunter's task in the test.
- A new cycle where a wounded subject with an acting hostile flees instead of eating: intended (SURV-07: only a present threat to life outranks a pressing need; an acting hostile is one).

## Design points for the designer (confirm before code)
1. **The hp consequence line (no new constant).** Proposed: the line is death (hp 0), and the "need" is the damage fraction `1 - hp/max_hp`. Reuse `ESCALATION_ONSET` 0.6 and `ESCALATION_FULL` 0.85 (`src/engine/need_pull.py:21-22`) with no travel or rate term (hp loss has no steady per-tick rate).
   - The escalation starts at hp 40% and is full at hp 15%.
   - Both edges already exist as hp bands: `cognition.py:135` panic +0.2 below 0.4, `tactical.py:507` cover/retreat branch below 0.4, `tactical.py:522` pure retreat below 0.15.
   - Not proposed:
     - CombatRetreatScorer's own gate at 0.5 (`scorers.py:229`): it would need a different onset, which is a new constant.
     - `WOUNDED_HP_RATIO` 0.7 (`tactical_threat.py:30`): it is a threat term, not a consequence line, and its band has no edge for "full".
     - The commitment and self-assessment `< 0.2` lines: one edge only.
2. **The threat gate.** The escalation applies only while `present_threat_to(entity, state)` holds. This mirrors SURV-07: only a present threat outranks a pressing need. Without the gate, a wounded subject with nothing in view outranks its own starving hunger. `present_threat_to` is read, not changed (step B changes what counts as acting).

## Steps (after confirmation)
1. `src/engine/need_pull.py`: add `HP_LINE = 1.0` (the damage fraction at death; a named value like HUNGER_LINE, not a tuning constant) and `retreat_pull(raw, hp_ratio) = raw + ESCALATION_AMPLITUDE * smoothstep(ONSET, FULL, 1 - hp_ratio)`. If the designer counts `HP_LINE` as a new constant, inline `1 - hp_ratio` against the fraction instead.
2. `src/ai/goals/scorers.py` CombatRetreatScorer: after the existing raw utility, `utility = retreat_pull(utility, hp_ratio) if present_threat_to(entity, state) else utility`. The existing early return and target are unchanged.
3. Docs in the same change:
   - Bible 04 §1 (goal tiers): the retreat escalation.
   - SURV-07 world rule: the row 83 "As built" sentence and the parked alternative become built.
   - `intentional_divergences.md`: a new 2.x entry (Intentional Gameplay Change).
   - Parity ledger: a new STRAT-xxx entry, P1, with test_path.
   - `registries/mechanisms.yaml` content only if rpg-planner says so (it owns the content).
4. Tests: see test_plan.md. The row 83 pin (retreat <= 150) is replaced, which needs the planner's yes.
5. Measure: paired `--base 341f700d0 --new <step A tip>`, seeds 42-46, crowded, then frontier and urban, 5000 ticks, jobs 1, after the planner says the host is free. Report per (world, role) alive and extinctions, starvation deaths, the N15 rows, the retreat/hunger goal win counts, and the 3-world hash change (expected to differ). Stop line per the planner. A result outside it goes to the owner.

## Scope guards
- No change to the hunger pull, `_hunger_escalated_unless_threatened`, `present_threat_to`, `tactical_threat.py` or the tactical order (`tactical.py`).
- No new tuning constant.
- No push without the user's yes.
