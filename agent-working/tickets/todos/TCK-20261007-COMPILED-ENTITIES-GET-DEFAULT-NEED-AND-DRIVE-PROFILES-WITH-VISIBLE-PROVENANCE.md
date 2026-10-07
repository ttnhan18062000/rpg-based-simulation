---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261007-COMPILED-ENTITIES-GET-DEFAULT-NEED-AND-DRIVE-PROFILES-WITH-VISIBLE-PROVENANCE
phase: open
date: 2026-10-07
tags: [simulation-quality]
---

# TCK-20261007-COMPILED-ENTITIES-GET-DEFAULT-NEED-AND-DRIVE-PROFILES-WITH-VISIBLE-PROVENANCE

## Title
Compiled entities get default need and drive profiles from their species and role, with a typed, visible provenance (AGENCY-08, SURV-05 needs half)

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Child of `TCK-20261007-EPIC-DECISION-CORE-LIVE-MOTIVATION-AND-HONEST-FIGHT-OR-FLEE-INPUTS`. Measured on main `f8f1b69fd`: 666 of 666 compiled entities across the 24 corpus worlds carry neither `need_profile_id` nor `drive_profile_id`. Their breakdown:
- by role: MONSTER 220, WORKER 180, GUARD 176, SHOPKEEPER 49, HERO 41;
- by species: human 324, goblin 82, undead 54, wolf 50, orc 36, spider 35, lizardfolk 24, elf 6, spirit 4, and no species 51 (HERO 30, SHOPKEEPER 15, GUARD 6).

So the motivation layer is inert on the standard worlds. The catalog already declares a need_profile for all 13 species, and a drive_profile for each of its 29 archetypes.

Rule, decided by world-rule-catalog-design under the owner's delegation on 2026-10-07 (memo row 22, AGENCY-08, SURV-05). Needs belong to the body; drives belong to the person.
- **NEED** = the species need_profile. A person (civil role) with no species falls back to humanoid_survival. A non-person with no species is a content defect, reported, not guessed.
- **DRIVE** = the most specific DECLARED source: (a) an archetype matching the (species, role) pair; (b) the civil role (WORKER→cautious_commoner, GUARD/HERO→disciplined_protector, SHOPKEEPER→profit_seeker); (c) MONSTER → a per-species default drive DECLARED in content (seed once: wolf and spider → territorial_predator, goblin and orc → opportunistic_raider, undead → undead_purpose_bound; the other MONSTER species need their own declaration). Never compute it at runtime.
- **Provenance is a typed field** on the entity: explicit, defaulted:species, defaulted:role, defaulted:species_drive or defaulted:person_fallback. Not metadata, and not a reason string.

## Scope
1. A per-species `default_drive` field in species content, seeded as above, with every MONSTER species declared.
2. A typed provenance field for each of need and drive. `src/core/state.py` is in scope; ask rpg-feature-planning before editing it, as usual.
3. Assignment on the compile path (`WorldCompiler` / world assembly), following the rule's precedence. Archetype-spawned entities keep provenance `explicit`.
4. A coverage report across the 24 worlds: explicit vs each default kind, and any content defects.
5. Before/after on ONE tree: seed 42, the standard worlds plus the campaign episode, audit_mode, budget off, 2 runs. Report the AGENCY-07 flight-gate firings, the territory/duty sort effect (`tactical.py:459-463`), deliberate attacks, deaths, and the campaign tests' status. Disclosed re-baseline (SimQ anchors move).

## Out of Scope
- The biological half of SURV-05 (`TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES`, Lane B).
- The five pressure dimensions with no reader (SURV-04).
- Tuning.

## Acceptance Criteria
- [ ] 666 of 666 corpus entities carry need and drive profiles with typed provenance. The coverage table is recorded, and any content defect is reported, not defaulted.
- [ ] Every MONSTER species declares a default_drive. No runtime frequency computation.
- [ ] The behaviour change is measured on one tree, with a divergence entry and parity entry.
- [ ] No new "V2" names (owner rule 2026-10-07).

## Related Tickets
- `TCK-20261007-EPIC-DECISION-CORE-LIVE-MOTIVATION-AND-HONEST-FIGHT-OR-FLEE-INPUTS` (parent)
- `TCK-20261007-SAFETY-DISPOSITION-TRIGGERS-RETREAT-ON-SIGHT-AGENCY-07` (#398)

## Related Docs
- Memo row 22; catalog AGENCY-08, SURV-05

## Related Stored Artifacts

## Related Code Areas
`src/world/motivation/pressure_resolver.py`, `src/worldbuilding/compiler.py`, `src/worldassembly/resolver.py`, `src/core/state.py`, `data/content/living/species.yaml`

## Assumptions / Open Questions

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
