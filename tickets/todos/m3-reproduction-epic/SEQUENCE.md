# Implementation Sequence — m3-reproduction-epic

Tickets must be implemented in this order. Generated from intra-batch dependency analysis
(C1 investigation, M3 create-tickets batch, 2026-09-02) plus the epic doc's own build order.
`implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA  (no deps in this batch — foundational)
2. TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH  (depends on: TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA)
3. TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH  (depends on: TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA)
4. TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE  (depends on: TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA)
5. TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE  (depends on: TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA, TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE)
6. TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE  (depends on: TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH, TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH, TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE)

## Notes

- The epic ticket `TCK-20260902-EPIC-RPG-M3-REPRODUCTION` tracks all 6 above; it is scope-only,
  not part of the implementation sequence itself.
- Ticket 6 (population-pressure closure, idea 38) must land no later than atomically with the
  last of tickets 2/3/5 — the source epic doc's own acceptance constraint forbids exposing
  repeatable births before this loop can incorporate them.
- Tickets 2 and 3 have no dependency on each other and could in principle implement in either
  order or even be parallelized by a future orchestrator change — kept sequential here since
  `implement-epic` executes strictly one ticket at a time.
- Cross-batch (not enforced by this file): `tickets/todos/m3-family-species/TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE.md`
  has one AC signal blocked pending ticket 1 (birth-record schema) landing in this batch — see
  that ticket's own Related Tickets/Assumptions sections.

tracking_doc: docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
