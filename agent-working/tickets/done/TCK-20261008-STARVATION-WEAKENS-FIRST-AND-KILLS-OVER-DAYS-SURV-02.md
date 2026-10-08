---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261008-STARVATION-WEAKENS-FIRST-AND-KILLS-OVER-DAYS-SURV-02
phase: done
date: 2026-10-08
tags: [combat]
---

# TCK-20261008-STARVATION-WEAKENS-FIRST-AND-KILLS-OVER-DAYS-SURV-02

## Title
Past the hunger line a person weakens first (slower recovery, worse in a fight), then loses health slowly, and dies after about 2 to 3 days without food, not within half an hour (SURV-02 amendment, owner decision 36).

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner decision 36 (2026-10-08, designer commit 92f43c41e). Before: `hunger >= 95.0` cost 2 HP per life-due tick (`apply.py`), death about 50 ticks after the line.

## Scope
1. `src/engine/starvation.py`: one frozen table (weakened 85, starving 95, recovery x0.5, attack x0.8, death 6000 ticks) and pure stage functions. 2. `apply.py`: the HP term under the same >= 95 guard and one recovery scale per entity on the stamina and readiness regeneration. 3. `combat.py`: the STARVATION_WEAKENED attack factor, compounding with EXHAUSTION. 4. Unit tests, LB-S18 kernel scenario with a control arm, divergence 2.94, parity PROG-129, Bible 01 section 4, the `attributes_biology` note. 5. Pinned 5x3 at 10000 ticks.

## Out of Scope
- Illness from raw food; the fatigue and sleep consequence; moving the table into content (a later step).

## Acceptance Criteria
- [x] A full-health person with no food dies 4800 to 7200 ticks after the line, with the weakened stage observable before (LB-S18).
- [x] The weakening reuses existing machinery where possible: the cognitive capacity degradation stays the hungry stage (it cannot carry recovery or combat, stated in the investigation); EXHAUSTION's attack factor pattern and the stamina and readiness regeneration are scaled.
- [x] Divergence, parity, Bible 01 and the `attributes_biology` mechanisms note are written.
- [x] Pinned 5x3 at 5000 and 10000 ticks.

## Related Tickets
- TCK-20261008-LIGHT-BALANCE-PASS-HUMAN-HUNGER-IS-LOW-DECISION-33 (the rate change). - TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL (its collapse dynamics depend on this).

## Related Docs
- `docs/world_rules/life-body/survival-needs.md` (SURV-02 amendment); `docs/mechanics/01_entity_anatomy.md` section 4; `docs/guidelines/intentional_divergences.md` 2.94.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-STARVATION-WEAKENS-FIRST-AND-KILLS-OVER-DAYS-SURV-02/` (investigation.md, probes/).

## Related Code Areas
- `src/engine/starvation.py`, `src/engine/apply.py`, `src/engine/combat.py`, `src/strategy/cognition_capacity.py`.

## Assumptions / Open Questions
- Finding for the designer: `sleep_debt >= 98.0` still costs 1 HP per tick (`apply.py`), the same shape as the defect fixed here.
- The worlds feed few people, so the long-run survivors converge (alive at tick 10000 is unchanged); the staging delays and spreads deaths.

## Implementation Notes
Stages derive from `hunger` alone; the loss is staggered by (life-due ordinal + entity id) modulo `round(6000 / max_hp)`.

## Test Summary
`tests/unit/engine/test_starvation_stages.py` (28), `tests/mechanic_scenarios/test_starvation_over_days.py` (LB-S18: 2); three passive-death tests re-staged to a 1 HP per tick subject. 958 passed in the engine/combat/actions/scenario/pipeline/progression/ph9/mechanism sweeps; ratchet OK; mypy clean; lint-imports 17 kept, 0 broken.

## Files Changed
src/engine/starvation.py (new), apply.py, combat.py; tests as above; docs (01_entity_anatomy, intentional_divergences 2.94, parity PROG-129), registries/mechanisms.yaml, the verification view, the completeness pin (314 files).

## Completion Summary
Starvation is staged and kills over days; starvation deaths by tick 1500 fell from 10.0 / 13.4 / 7.2 to about 0 per run; the new code costs about 0.7 percent of the apply step.
