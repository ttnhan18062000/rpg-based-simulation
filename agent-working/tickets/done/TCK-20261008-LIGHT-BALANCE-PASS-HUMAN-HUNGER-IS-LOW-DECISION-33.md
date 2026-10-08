---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261008-LIGHT-BALANCE-PASS-HUMAN-HUNGER-IS-LOW-DECISION-33
phase: done
date: 2026-10-08
tags: []
---

# TCK-20261008-LIGHT-BALANCE-PASS-HUMAN-HUNGER-IS-LOW-DECISION-33

## Title
Light balance pass (owner decision 33), row 1: `humanoid_survival` hunger goes from medium to low (0.1 to 0.05 per tick).

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
At the base rate a person reaches the starvation line 9.5 hours after a full meal and is dead about 10 hours after it (Bible 05: 2400 ticks per day), which needs about six inn meals a day. Owner decision 33 allows a light balance pass on content values with a fiction reason, one pass, one measurement.

## Scope
One value: `humanoid_survival` hunger "low" in `data/content/living/need_profiles.yaml`, with the table of the values considered (inn meal 40, berry 30, regrowth 1 per 200 ticks: no change; starting gold for workers: declined).

## Out of Scope
Code constants (starvation line, starvation damage, the rate multipliers, prices); other kinds; sleep.

## Acceptance Criteria
- [x] The value changed with its fiction reason as the comment. - [x] The kinds that use the profile are listed (human, orc, elf, dwarf, troll, lizardfolk, species-less persons). - [x] Divergence 2.91 with the table. - [x] The rate tests follow.

## Related Tickets
- `TCK-20261008-ENV-08-SETTLED-LAND-AND-THE-NEAR-WILD-CARRY-NO-STANDING-AMBIENT-HAZARD`
- `TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT`

## Related Docs
- `docs/guidelines/intentional_divergences.md` 2.91; `docs/mechanics/01_entity_anatomy.md` section 4; `docs/parity_ledger/progression.yaml` PROG-128.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-LIGHT-BALANCE-PASS-HUMAN-HUNGER-IS-LOW-DECISION-33/` (investigation, plan, test plan); the shared probes and measurement rows are in `agent-working/stored_artifacts/TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL/probes/`.

## Related Code Areas
- `data/content/living/need_profiles.yaml`; `src/engine/biological_needs.py` (read only).

## Assumptions / Open Questions
- By owner ruling (2026-10-08) the batch lands with free meals still on; the free-meal removal is parked on branch `d27-free-meal-removal` under `TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL` (kept open).
- Decision 31's landing bar (a second way to eat in all three measured worlds) is not met; recorded with numbers in divergence 2.89 and on the parked ticket.

## Implementation Notes
One content value. At 0.05 per tick a person reaches the starvation line about 19 hours after a full meal and three 40-hunger inn meals a day cover the 120 hunger that builds. The 1500-tick attribution (starvation 28.6 to 8.2, 20.4 to 12.6, 21.4 to 0.0) was measured with the free-meal removal on and is parked evidence; it is a clock effect, since the window is 0.63 of a day.

## Test Summary
`tests/unit/engine/test_biological_needs.py` (human rate 0.05, goblin medium 0.1, apply-path accumulation) and `tests/unit/world/test_recovery_class_hall.py` (hero hunger 30.05) pass; combined headline in divergence 2.89.

## Files Changed
`data/content/living/need_profiles.yaml`, two test files, divergence 2.91, parity PROG-128 note, Bible 01 row, a mechanism note, 24 resolved worlds regenerated.

## Completion Summary
Humans hunger at half the base rate. In the 5000-tick landing measurement survivors at tick 1000 are 19.2, 21.2 and 21.8 against 8.0, 16.8 and 13.8 on main; the starvation wave moves to ticks 1000 to 2000. It is a balance fix, not a way to eat.
