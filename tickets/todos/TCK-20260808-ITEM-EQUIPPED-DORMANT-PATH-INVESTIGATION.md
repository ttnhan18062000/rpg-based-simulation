---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION
phase: open
date: 2026-08-08
tags: [progression, simulation-quality]
---

# TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION

## Title
`item_equipped` never fires in real gameplay — one real contributing cause (species-evolution gear
upgrade) is already tracked elsewhere, but 2 other real, independent equip-producing code paths
have not yet been traced

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Split out from `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD` (2026-08-08, per user
review) — that ticket confirmed one real contributing cause of `item_equipped`'s dormancy
(`EvolutionSystem`'s species-evolution gear upgrade, itself gated behind the corpus-wide-dormant
`level_up`), but explicitly flagged 2 other real, independent, non-level-gated equip-producing
code paths that were found but not traced:

- `src/domains/progression/resolver.py:43-44` — constructs a real `EquipmentUpdate(slot_updates=
  {EquipSlot.MAIN_HAND: "iron_sword"})`, unrelated to `EvolutionSystem`'s own level-gated logic.
- `src/core/equipment.py:239-265` — a separate, general equipment-resolution service
  (`slot_updates=equipment_changes`).

Neither of these is confirmed to share `EvolutionSystem`'s own `levels_gained > 0` root cause —
they are structurally independent code, and could be gated by something else entirely (a feature
flag, a quest/shop-reward dependency, an AI decision that never fires, or something not yet
identified). This ticket exists specifically because bundling unconfirmed, independent leads into
one ticket was a real mistake in the original filing — this one gets its own real investigation.

## Scope
1. **Investigate** (mandatory before Plan):
   - Trace `src/domains/progression/resolver.py`'s own real caller(s) and gating condition(s) —
     confirm whether this code path is ever reached in real gameplay, and if not, why.
   - Trace `src/core/equipment.py`'s own real caller(s) and gating condition(s) — same question.
   - Confirm via real corpus-wide instrumentation (not static reading alone) whether either path
     produces any real `item_equipped` events across a representative multi-world, long-tick
     sample — matching this session's own established "verify via real execution" discipline.
   - If both paths are confirmed dormant, determine the real reason(s) — do not assume they share
     one cause with each other, or with `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`'s
     own species-evolution finding, without checking.
2. **Plan**: scope the real, minimal fix based on Investigate's own confirmed root cause(s) —
   which may turn out to require no code fix at all if e.g. the real content/scenario preconditions
   for these paths simply don't exist in the current corpus (a content gap, not a code bug) —
   report that honestly if so, rather than forcing a fix.
3. **Implement**: only the real, confirmed, minimal fix.

## Out of Scope
- `EvolutionSystem`'s own species-evolution gear-upgrade dormancy — already tracked in
  `TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`, do not duplicate.
- `skill_unlocked`/`progression_conversion_applied`/`attribute_changed` — covered by the sibling
  ticket above, not this one.
- `trait_expressed`/`pillar_trait_unlocked` — covered by
  `TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION`, not this one.

## Acceptance Criteria
- [ ] investigation.md traces both `src/domains/progression/resolver.py`'s and
      `src/core/equipment.py`'s real caller chains and confirms (via real execution, not static
      reading alone) whether either produces real `item_equipped` events under any real corpus
      condition
- [ ] Real root cause(s) reported honestly, including "this is a content gap, not a code bug" as a
      valid, non-forced conclusion if that's what the evidence shows
- [ ] If a real fix lands, re-verified against real corpus data
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD (sibling — split from the same original
  filing; owns the species-evolution contributing cause, not this ticket's own 2 leads)
- TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT (DONE — `docs/audits/D21_entity_lifecycle_foundation_layers.md`,
  the audit that originally surfaced `item_equipped`'s dormancy)
- TCK-20260701-SIMQ-EMIT-PROGRESSION (DONE — original event-emitter wiring; not directly relevant
  to `item_equipped` specifically, which predates that ticket, but useful pattern reference)

## Related Docs
- `docs/audits/D21_entity_lifecycle_foundation_layers.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/domains/progression/resolver.py`
- `src/core/equipment.py`
- `src/observability/event_extractor.py` (lines ~342-364 — the real `item_equipped`/
  `item_unequipped` emitter, already correctly wired)

## Assumptions / Open Questions
- Whether these 2 paths share a root cause with each other, or with the species-evolution finding
  in the sibling ticket — not assumed; Investigate must trace each independently.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
