---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-EPIC-RPG-M3-REPRODUCTION
phase: open
date: 2026-09-02
tags: [lifecycle, world]
---

# TCK-20260902-EPIC-RPG-M3-REPRODUCTION

## Title
Reproduction (M3 idea 32) — tracking epic for the 6-ticket birth/genetics/population-loop initiative

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Idea 32 (Reproduction) from `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md` has zero
real code today — it is design-only in `docs/brainstorm/rpg_feature_atlas.html`. Both of its hard
M2 dependencies are confirmed genuinely landed (idea 14 → `RaceDefinition.intelligence_tier`, idea
43 → `population_cohorts` seeding), but a real implementation independently spans 6 separate
subsystems: durable birth-record schema, three species-branching decision paths
(natural-creature/magical-demonic/human-humanoid), orphaned `GeneticsSystem` wiring, and the
still-open population-pressure feedback-loop closure (idea 38). This was investigated as concern C1
of the M3 create-tickets batch on 2026-09-02; the investigator's own independent, code-grounded
recommendation — matching the epic doc's own flagged uncertainty — was to split this into its own
epic with child tickets rather than fold it into the flat 5-ticket M3 batch as one item. The user
confirmed this split on 2026-09-02.

This epic tracks child tickets only; no direct implementation happens here.

**Explicit resolved decision (2026-09-02, user-confirmed):** the idea-32 atlas card's "human/humanoid
births are gated on marriage (see next card)" language is stale. The 2026-08-29 M3 build-order note
explicitly decoupled Marriage (idea 33) from Reproduction (idea 32) — reproduction does **not**
require an active marriage contract as a precondition anywhere in this epic's child tickets. The
atlas card text should be corrected as a small follow-up doc fix (flagged in
TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE).

## Scope
Full findings are in the C1 investigation (folded into each child ticket's own Request Summary).
Child tickets, in required build order:
1. `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA` — foundational durable schema (parent ids,
   birth tick, birth city, per-parent cooldown) + builder wiring. No dependencies; every other
   child ticket depends on this landing first.
2. `TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH` — Camp maturity/spawn reuse, no tracked
   parent pair. Depends on (1).
3. `TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH` — Calamity substrate reuse, full-adult spawn,
   no childhood. Depends on (1).
4. `TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE` — wires the previously-orphaned
   `GeneticsSystem`/`GeneticProfile` into a real call path for the first time. Depends on (1).
5. `TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE` — new WD-16 cadence sub-phase, per-parent
   cooldown, explicitly NOT marriage-gated. Depends on (1) and (4).
6. `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE` — closes the idea-38 population-pressure
   feedback loop (individual births nudge the aggregate `population_cohorts` signal). Must land
   atomically with or immediately after (2), (3), and (5) — the epic's own acceptance constraint
   forbids exposing repeatable births before this loop can incorporate them.

## Out of Scope
- Idea 31 (Personal Dependents) and idea 34 (Coming of Age) — tracked separately in the flat M3
  batch (`tickets/todos/m3-family-species/`), not as children of this epic, though both have a
  documented dependency on child ticket (1)'s birth-record schema.
- Idea 33 (Marriage) — explicitly decoupled from this epic per the 2026-08-29 build-order decision;
  tracked separately in `tickets/todos/m3-family-species/TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT.md`.
- Any marriage-contract precondition on reproduction eligibility, in any child ticket.

## Acceptance Criteria
- [ ] All 6 child tickets are DONE, in the build order listed above.
- [ ] No child ticket introduces a marriage-contract precondition anywhere in reproduction
      eligibility logic.
- [ ] The population-pressure feedback loop (child 6) lands no later than atomically with the last
      of the three birth-path tickets (children 2, 3, 5) — repeatable births are not considered
      "shipped" by this epic until child 6 is also DONE.
- [ ] `docs/mechanics/05_world_evolution.md` and `docs/mechanics/01_entity_anatomy.md` document the
      full reproduction mechanism (birth-record schema, all three paths, genetics inheritance,
      population-pressure closure) once all children land.
- [ ] `docs/brainstorm/rpg_feature_atlas.html`'s idea-32 card's stale "gated on marriage" text is
      corrected (tracked via child ticket 5's follow-up note).

## Related Tickets
### Investigation (prerequisite — done)
- C1 investigation (2026-09-02, part of the M3 create-tickets batch) — full findings folded into
  each child ticket below.

### Child tickets (implementation sequence)
- TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA — foundational schema (open)
- TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH — natural-creature path (open)
- TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH — magical/demonic path (open)
- TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE — genetics wiring (open)
- TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE — human/humanoid cadence sub-phase (open)
- TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE — idea-38 feedback-loop closure (open)

### Upstream dependencies
- TCK-20260831-SPECIES-INTELLIGENCE-TIER (idea 14, DONE)
- TCK-20260831-POPULATION-COHORT-SEEDING (idea 43, DONE)

### Downstream / sibling M3 tickets (not children of this epic, but depend on it)
- TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE (idea 34 — one AC blocked pending child (1))
- TCK-20260902-PERSONAL-DEPENDENTS-ROUTE-BIAS (idea 31 — parental-dependent auto-registration
  deferred pending child (1))

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 32 and idea 38 cards)
- docs/mechanics/05_world_evolution.md
- docs/mechanics/01_entity_anatomy.md
- docs/parity_ledger/world_dynamics.yaml

## Related Stored Artifacts
None — epic tier tracks child tickets only; each child ticket carries its own staging artifacts.

## Related Code Areas
- src/core/state.py
- src/core/updates.py
- src/core/builder.py
- src/world/camp.py
- src/world/calamity.py
- src/systems/lifecycle_systems/genetics.py
- src/domains/demographics/cohort.py
- src/domains/world_emergence/models.py
- src/engine/cadence.py

## Assumptions / Open Questions
- Idea 32 is explicitly named by the epic doc as "the single highest-cost, highest-risk idea in
  the whole 65-idea set" — this epic split is the direct response to that flagged risk, confirmed
  by independent investigation and the user's own 2026-09-02 decision.
- SEQUENCE.md in `tickets/todos/m3-reproduction-epic/` enforces the build order above for
  `implement-epic`.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
