---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE
phase: open
date: 2026-09-02
tags: [lifecycle, engine]
---

# TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE

## Title
Human/humanoid reproduction cadence sub-phase — new WD-16 cycle, per-parent cooldown, NOT marriage-gated

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child ticket 5 of 6 under the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION). This is the human/humanoid reproduction trigger path: a new cadence sub-phase (proposed WD-16) registered in `src/engine/cadence.py`'s `SystemCadence`, that periodically checks eligible ADULT, alive, same-location, same-race entity pairs with clear per-parent cooldowns and produces a birth. IMPORTANT — per an explicit 2026-08-31 plan-owner decision, this path does NOT require an active marriage contract as a precondition. The idea-32 atlas card's "gated on marriage" language is stale relative to the 2026-08-29 build-order decoupling of Marriage (idea 33) from Reproduction (idea 32); do not implement a marriage-contract check anywhere in this ticket, and flag the stale atlas card text for a doc correction. Depends on TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA and TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE landing first (this path calls into the genetics inheritance step for the new entity's GeneticProfile).

## Scope
- Register a new cadence entry (proposed WD-16) in `src/engine/cadence.py`'s `SystemCadence`/`should_run()`, following the existing cadence-registration pattern used by other periodic system phases.
- On each cadence firing, evaluate eligible ADULT, alive, same-location, same-race entity pairs (cross-race pairing explicitly excluded per resolved design decision — same-race only).
- Eligibility requires: both entities ADULT life stage, alive, co-located, same race, and both individual per-parent cooldowns (from TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA) clear.
- No marriage-contract check anywhere in this eligibility logic.
- On a successful pairing, produce a new entity via the existing builder path (`src/core/builder.py`, extended by TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA), recording `parent_a_id`, `parent_b_id`, `birth_tick`, `birth_city_id`, and calling into TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE's inheritance step for the new entity's `GeneticProfile`.
- Set both parents' per-parent cooldown fields on a successful birth.
- Seed a `SocialBond` between each parent and the child (reuses the seeding path from TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA).
- Eligibility for the pairing is also suppressed when `compute_regional_scarcity()` for the birth region exceeds the region's cohort `migration_threshold` (0.7 default) — same population-pressure gate reused by the natural-creature path.
- Explicitly document (in Implementation Notes / a mechanics-doc note), not silently ignore, that individual births from this path do not yet feed back into the aggregate `population_cohorts` signal — that is closed by the final epic child ticket, TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE.

## Out of Scope
- Marriage as a precondition — explicitly excluded per the 2026-08-31 decision described above.
- The natural-creature and magical/demonic paths (separate tickets).
- The genetics inheritance formula itself — implemented in TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE, this ticket only calls into it.
- Closing the population-pressure feedback loop (nudging `population_cohorts` on birth) — TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE, the final child ticket.
- Correcting the stale "gated on marriage" text in `docs/brainstorm/rpg_feature_atlas.html`'s idea-32 card — note it as a disclosed gap for a small follow-up doc fix rather than editing the brainstorm doc as part of this ticket, unless Plan decides it's trivial enough to bundle in.

## Acceptance Criteria
- [ ] A new WD-16-style cadence entry fires periodically per `SystemCadence`'s existing registration pattern.
- [ ] Calling the reproduction check for two ADULT, alive, same-location, same-race entities with both per-parent cooldowns clear produces a new entity via the builder path, with `parent_a_id`, `parent_b_id`, `birth_tick`, `birth_city_id` correctly recorded and a `GeneticProfile` attached via TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE's inheritance step.
- [ ] No marriage-contract state is read or checked anywhere in this eligibility path — verifiable by grep showing no `ContractKind.MARRIAGE`/`MarriageState` reference in the new code.
- [ ] A `SocialBond` is seeded between each parent and the child at high familiarity/sentiment.
- [ ] Both parents' per-parent cooldown fields are set on a successful birth, and a repeat check on the same pair before cooldown clears does not produce a second birth (test proves this).
- [ ] Eligibility is suppressed when `compute_regional_scarcity()` exceeds the region's `migration_threshold` — test proves both allowed and suppressed cases.
- [ ] `docs/mechanics/05_world_evolution.md` documents this cadence sub-phase, explicitly noting individual births do not yet feed the aggregate `population_cohorts` signal (until the closure ticket lands); a `docs/parity_ledger/world_dynamics.yaml` entry cites it.
- [ ] A note is filed (ticket body or a small follow-up ticket, per Plan's judgment) flagging `docs/brainstorm/rpg_feature_atlas.html`'s idea-32 "gated on marriage" text as stale relative to the 2026-08-29 decoupling decision.

## Related Tickets
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION (parent epic)
- TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA (hard dependency — must land first)
- TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE (hard dependency — must land first, this ticket calls into its inheritance step)
- TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE (downstream sibling — depends on this ticket landing)
- TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT (related but explicitly NOT a dependency — Marriage and Reproduction are decoupled)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md (2026-08-29 build-order decoupling decision)
- docs/brainstorm/rpg_feature_atlas.html (idea 32 card — "gated on marriage" text is stale, flag for correction)
- docs/mechanics/05_world_evolution.md
- docs/engine/kernel.md (cadence/phase registration pattern)

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/cadence.py
- src/domains/demographics/cohort.py
- src/core/builder.py
- src/core/updates.py

## Assumptions / Open Questions
- Exact cadence interval for WD-16 (analogous to `DemographicCycleService`'s 200-tick `COHORT_INTERVAL`) is a Plan-phase decision.
- Whether the marriage-gate stale doc text gets its own tiny follow-up ticket or is corrected inline here is left to Plan's judgment based on how large the doc-fix ends up being.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
