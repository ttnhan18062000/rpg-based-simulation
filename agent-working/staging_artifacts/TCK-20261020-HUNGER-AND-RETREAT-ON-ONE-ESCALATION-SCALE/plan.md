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
