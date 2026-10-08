---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07
phase: done
date: 2026-10-07
tags: [strategy, cognition]
---

# TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07

## Title
Biological needs escalate above ordinary goals before their consequence line (world rule SURV-07), and a subject that cannot reach a bed in time rests where it stands (SURV-06).

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Decision 24 (SURV-07): a standing biological need's pull grows steeply as its consequence line approaches, so that well before the line it outranks ordinary goals, early enough to reach a way to meet it; only a present threat to life outranks a pressing need. The decision side of the umbrella `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100` (breaks 3b and 3c), together with SURV-06's rest in place. Curve shape and magnitudes are engineering's (memo row 24); the planner accepted the curve below as the engineering default.

Justification (census, before the change, `crowded_frontier` and `frontier_living_world`, seed 42, 1500 ticks): `region_stabilization` a flat 100, `resolve_blocker` up to 103.8, `town_return` up to 134.8, and the need goals were only the raw need, so among entities with hunger of at least 60 or sleep debt of at least 40 the winners were `region_stabilization` and `resolve_blocker` and need goals won 0 times. The walk to the inn is up to about 190 tiles (about 19 hunger points on the way).

## Scope
1. `need_pull` (`src/ai/goals/need_pull.py`): raw need plus a smoothstep from 0.6 to 0.85 of the consequence line (hunger 95, sleep deprivation 98), worth up to +60, evaluated on the level the subject will have on arrival `(need + rate x walking tiles) / line`, with the kind's own per-tick rate (`need_rates`, SURV-05). Used by `SleepScorer` and `EatScorer`; no other goal's magnitude changes.
2. The escalation gives way to a present threat: a perceived, catalog-hostile neighbour plus AGENCY-07's `present_threat_terms` (`present_threat_to`). **A present threat requires at least one perceived hostile, for both the need gate and rest in place; a wound alone does not count** (planner ruling, SURV-06 "sleep rough anywhere it is not in danger" and AGENCY-07's present-threat line).
3. Rest in place (`rest_in_place_update`, `src/engine/tactical_rest.py`): a fatigue project that cannot reach a bed (inn or home, `service_tile`) before sleep debt reaches 0.85 of the line, or has none, dispatches `REST` with reason `REST_IN_PLACE` when no present threat holds.
4. Parity: Bible 04 subsection, ledger STRAT-280, divergence 2.81.

## Out of Scope
- The free meal and the poor subject's redirect (Decision 27), filed as `TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL` (Lane B, one PR with the redirect).
- The opportunity-attack-per-step defect, `TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP`.
- `core_actions.py`, `town_resolution.py` and the per-kind need-path integrity check (`need_paths.py`).

## Acceptance Criteria
- [x] Need terms escalate above the highest ordinary goal before the line: tests in `tests/unit/ai/test_need_pull.py` and `test_need_scorers.py`.
- [x] A present threat takes the escalation away; a wound alone does not (tests).
- [x] Rest in place dispatches `REST` with reason `REST_IN_PLACE` through the tactical pass, per-kind rates change the dispatch tick, an adjacent bed or a non-bed building behaves (tests; the corpus never reaches the rule in 1500 or 3000 ticks, so the proof is the constructed test).
- [x] Five-seed measurement on three worlds, pinned, reported with per-seed values (stored artifacts). Starvation falls on every world; total deaths and alive at t=1100 are within one SD on every world; alive at t=1000 is within one SD on two worlds and **fails on `crowded_frontier` (18.2 to 7.8)**, owned by the opportunity-attack ticket.
- [x] Disclosures in divergence 2.81: part of the starvation gain is free meals; every remaining starvation death is a broke subject; the `crowded_frontier` t=1000 cell; pinning and determinism.

## Related Tickets
- `TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100` (umbrella, stays open), `TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES` (SURV-05/06, #407).
- `TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL`, `TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP`.

## Related Docs
- `docs/world_rules/life-body/survival-needs.md` (SURV-05, SURV-06, SURV-07), `docs/plans/systemic_world/owner_decision_memo.md` rows 22 to 24, `docs/mechanics/04_strategic_cognition.md`, `docs/guidelines/intentional_divergences.md` 2.81.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07/` (investigation with the five-seed table, plan, test plan, `probes/`).

## Related Code Areas
- `src/ai/goals/need_pull.py`, `scorers.py`, `present_threat.py`, `scorers_support.py`; `src/engine/tactical_rest.py`, `tactical.py`.

## Assumptions / Open Questions
- The curve constants (0.6, 0.85, +60) are the accepted engineering default; they were not tuned: planner ruled not to tune the curve to hide the shortfall.
- Open, owned elsewhere: the free meal, the poor subject's redirect (Decision 27), and opportunity attacks while walking.

## Implementation Notes
Commit 1 is the designer's SURV-05/06/07 evidence patch. The curve and the scorers; the present-threat gate in the scorers (the tactical pass cannot gate a scored goal, because scorers do not see hostiles); rest in place hooked into the tactical pass after the AGENCY-07 retreat branch; `_suspend_project_for_threat` extracted from `evaluate_entity_intent` for the function-length ceiling. An affordability change (the inn is a way to eat only for a subject that can pay, `service_prices.py`, a typed `NeedAccess`) was built and measured and is **not shipped here**: on its own it starves every broke subject; it is preserved on the local branch `rpg-need-affordability` for Decision 27. Measurements ran with a governor pinned to NORMAL; determinism was checked on one world and one seed (four runs under load, identical).

## Test Summary
New: `tests/unit/ai/test_need_pull.py` (9), `tests/unit/ai/test_need_scorers.py` (7), `tests/unit/engine/test_rest_in_place.py` (13). Scoped runs listed in the PR. Corpus: five seeds (42 to 46), 1500 ticks, three worlds, `audit_mode`, budget off, pinned governor; full table with per-seed values in the stored artifacts.

## Files Changed
`src/ai/goals/need_pull.py`, `scorers.py`, `present_threat.py`, `scorers_support.py`; `src/engine/tactical_rest.py`, `tactical.py`; the three test files; `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml`, `docs/guidelines/intentional_divergences.md`, the designer's patch (`docs/world_rules/life-body/survival-needs.md`, `docs/plans/systemic_world/owner_decision_memo.md`), `docs/REGISTRY.yaml`; stored artifacts and probes.

## Completion Summary
The need goals now win before their consequence line and give way to a present threat; a subject that cannot reach a bed in time rests where it stands when no present threat holds. Starvation deaths fall on all three corpus worlds (25.0 to 13.2, 25.8 to 13.0, 16.0 to 10.8), but part of that gain is free meals eaten by subjects that cannot pay (SURV-06 rules this out; closed with Decision 27), every remaining starvation death is a broke subject, and `crowded_frontier` alive at t=1000 falls from 18.2 to 7.8 through opportunity attacks taken while walking. The disclosure is in divergence 2.81.
