---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261009-SLEEP-DEBT-WEAKENS-THEN-COLLAPSES-THE-SUBJECT-WHERE-IT-STANDS-NO-HP-LOSS
phase: done
date: 2026-10-09
tags: []
---

# TCK-20261009-SLEEP-DEBT-WEAKENS-THEN-COLLAPSES-THE-SUBJECT-WHERE-IT-STANDS-NO-HP-LOSS

## Title
Past a high sleep-debt line a subject weakens, and at 98 or more it falls asleep where it stands and cannot act until its debt drops below a wake line; it loses no HP (SURV-02, owner decision 41). The sleep goal reaches a bed only within reach and range.

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Before: `apply.py` cost 1 HP per tick at sleep debt 98 or more, the same shape as the starvation defect decision 36 replaced; measured on the hunting batch, nearly every creature died of it around tick 2000 whatever it ate, and the death was labelled STARVATION when hunger was also at 95. The designer's addition: the sleep pull aims at the nearest open way, not always the inn.

## Scope
1. `src/engine/sleep_debt.py` (one frozen table, pure stage functions, `collapse_update`, `sleep_done`). 2. Remove the HP drain; keep `PassiveDeathCause.SLEEP_DEPRIVATION` unwritten. 3. Weakened stage (the EXHAUSTION line reads the table; recovery scale is the worse of the hunger and sleep stages). 4. Collapse: a held SLEEP chosen in the tactical pass, held by the actions phase until the debt is below the wake line, a held walk stops (`move_ends_here`). 5. The sleep goal's bed is a way only within `bed_reach` and inside a leashed subject's range (`way_in_range`). 6. LB-S19 scenario with a control arm and a wolf; Bible 01 and 04, parity `PROG-130`, divergence 2.104.

## Out of Scope
- WAKE, the 0.5 scale, the bed reach and the sleep recovery rate are unruled placeholders (the designer); a deep-sleep duration of hundreds of ticks; the need-wake and held-move arrival fixes (Lane C); TownScorer's return to town; the population measurement (waits for the need-wake); shelter and cold (M3).

## Acceptance Criteria
- [x] No HP loss from sleep debt; a collapsed subject takes no action and does not move until its debt is below the wake line; it then walks on (LB-S19 main, person and wolf); a rested subject does none of it (control).
- [x] Bible 01, parity and divergence are updated.
- [ ] Population measurement: deferred until the need-wake lands (held movers otherwise swamp the result).

## Related Tickets
- TCK-20261008-STARVATION-WEAKENS-FIRST-AND-KILLS-OVER-DAYS-SURV-02 (the pattern); the hunting batch (TCK-20261009-A-KILL-LEAVES-MEAT-AND-A-CARNIVORE-EATS-IT-RAW-WITH-A-DIET-GATE-DECISION-44), which found the drain.

## Related Docs
- `docs/mechanics/01_entity_anatomy.md` section 4; `docs/mechanics/04_strategic_cognition.md` section 1; divergence 2.104; parity `PROG-130`; LB-S19 on the designer's branch.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261009-SLEEP-DEBT-WEAKENS-THEN-COLLAPSES-THE-SUBJECT-WHERE-IT-STANDS-NO-HP-LOSS/`

## Related Code Areas
- `src/engine/sleep_debt.py`, `apply.py`, `combat.py`, `tactical.py`, `tactical_hold.py`, `candidate_selector.py`, `pipeline_phases/actions.py`, `src/ai/goals/scorers.py`, `src/engine/way_in_range.py`.

## Assumptions / Open Questions
- WAKE 60 and the 0.5 scale are rpg-planner's suggestions in LB-S19; the sleep recovery rate is open (a collapse lasts about 11 ticks, ~7 minutes of game time; the SLEEP action relieves 20 per execution and costs 100 readiness at 10 a tick). Sent to the designer by rpg-planner.
- The collapse lags reaching the line by up to a brain cadence (about 11 ticks); accepted.
- `way_in_range` is a local helper behind the name another lane adds for the hunger ways; whichever lands second converges.

## Implementation Notes
The mob-leash block moved out of `evaluate_entity_intent` into `tactical_hold.leash_return_update` (unchanged) to stay under the tightened code-health ceilings. Four tests that pinned the drain were re-staged onto the hunger drain.

## Test Summary
`tests/unit/engine/test_sleep_debt_stages.py` (6); `tests/mechanic_scenarios/test_sleep_debt_collapse.py` (3); `tests/mechanic_scenarios/test_sleep_pull_nearest_open_way.py` (2); re-staged tests in `test_apply.py`, `test_passive_death_cause_and_rebirth_defeat_lifecycle.py` and `test_natural_aging_old_age_dispatch.py`; code health, mypy and import contracts clean.

## Files Changed
See `git diff origin/main --stat` of the PR.

## Completion Summary
Sleep debt now weakens and then collapses a subject where it stands and costs no health. Placeholders are named, not chosen; the population measurement waits for the need-wake.
