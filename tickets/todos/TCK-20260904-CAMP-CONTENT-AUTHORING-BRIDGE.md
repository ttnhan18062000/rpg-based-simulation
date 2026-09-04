---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE
phase: open
date: 2026-09-04
tags: [content, world]
---

# TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE

## Title
Author real Camp/Nest/Lair content so state.camps and LAIR-kind Places are actually populated in compiled worlds

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Three M4 tickets (`TCK-20260904-CAMP-NEST-CLASSIFICATION`, `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`,
`TCK-20260904-LAIR-ENTITY-ANCHOR`) and one downstream ticket
(`TCK-20260904-FACTION-EXPAND-DIRECTIVE`) all built real, tested, production-ready mechanisms for
Camp/Nest/Lair gameplay — but every one of them is currently inert in every real compiled world,
because no world-module content on disk actually sets the opt-in fields (`PlaceRecipeSpec.creature_kind`
for Camp/Nest, a LAIR-kind Place with a real occupant precedent) that would activate them. This is
purely a content-authoring gap, not a missing mechanism — this ticket closes it by authoring real
content and confirming end-to-end activation.

## Scope
- Author `creature_kind` values (from the confirmed 6-race set: `goblin`, `orc`, `wolf`, `spider`,
  `troll`, `slime`) on at least one real CAMP-kind and one real NEST-kind Place in the existing world
  corpus (`data/content/world_modules/`), using the classification table from
  `docs/mechanics/05_world_evolution.md` §6 (Camp/Nest Classification & Nest Spread) to pick a
  race-appropriate placement — do not invent new content wholesale where an existing CAMP-kind Place
  (e.g. `goblin_camp_conflict.yaml`) can simply gain the field.
- Author at least one real LAIR-kind Place with a `dragonkin` occupant precedent in the world corpus
  (per `TCK-20260904-LAIR-ENTITY-ANCHOR`'s own finding that no real corpus world has one today) —
  either add to an existing world module or justify a new one.
- Recompile the affected world(s) and verify via `canonical_state_hash`/`WorldCompiler.compile()`
  re-run that `state.camps` is genuinely non-empty and the Lair occupant spawns correctly, following
  the same isolation-verification pattern idea 66's own migration tickets used (diff scoped to the
  regions/places/camps changed, no unrelated state drift).
- Confirm `CampService.process_camps()` genuinely fires (raid/spawn/Nest-spread branches) against the
  newly-real camp content in at least one real simulation run, and that
  `FactionDecisionPhase`'s `EXPAND_TERRITORY` → `CampService` maturity-boost consumption path
  (`TCK-20260904-FACTION-EXPAND-DIRECTIVE`) is observably reachable for the first time.
- Update the parity-ledger entries that explicitly flagged this inertness as a limitation
  (`WORLD-109`, `WORLD-124`, and any `FAC-003` divergence-note language) to reflect that real content
  now exists, via `tools/parity_ledger_writer.py` — do not hand-edit YAML.

## Out of Scope
- Any change to the classification rule, `CampService` mechanism, `PlaceState`/`CampState` schema, or
  `FactionDecisionPhase`/`EXPAND_TERRITORY` logic itself — all four are already correct and tested;
  this ticket only authors content and verifies activation.
- City-ownership/idea 35 implementation, Camp/Nest-as-conquest-target logic, or any other scope
  explicitly deferred by the sibling tickets above — those remain their own future work.
- Migrating every world in the corpus — one real, verified activation per Camp/Nest/Lair kind is
  sufficient to close this gap; broader corpus-wide migration (if desired) is a separate, larger
  follow-up.

## Acceptance Criteria
- At least one real, compiled world has `state.camps` non-empty (at least one CAMP-kind and one
  NEST-kind camp) after this ticket, verified by a real compile+inspect, not a synthetic test fixture.
- At least one real, compiled world has a real LAIR-kind Place with a live `dragonkin` occupant,
  verified the same way.
- A real simulation run against the updated content shows `CampService.process_camps()`'s raid,
  spawn, and Nest-spread branches all reachable (not just unit-tested in isolation).
- `EXPAND_TERRITORY`'s CampService maturity-boost consumption branch is shown reachable in a real run
  for the first time.
- `WORLD-109`, `WORLD-124`, and FAC-003's divergence notes are updated to drop the "inert against real
  content" caveat where it's no longer true, with fresh `v2_evidence` citing the new content.
- No unrelated state drift in the affected world(s) — isolation verified via `canonical_state_hash`
  diffing at multiple entity-count scales, matching idea 66's own migration-ticket precedent.

## Related Tickets
- TCK-20260904-CAMP-NEST-CLASSIFICATION
- TCK-20260904-CAMPSTATE-PLACE-BRIDGE
- TCK-20260904-LAIR-ENTITY-ANCHOR
- TCK-20260904-FACTION-EXPAND-DIRECTIVE
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD
- TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT

## Related Docs
- docs/mechanics/05_world_evolution.md (§6 Camp/Nest Classification & Nest Spread)
- docs/world/raid_boss_camp_contract.md
- docs/world/compiler_contract.md
- docs/parity_ledger/world_dynamics.yaml (WORLD-109, WORLD-124)
- docs/parity_ledger/faction.yaml (FAC-003)

## Related Stored Artifacts
- stored_artifacts/TCK-20260904-CAMP-NEST-CLASSIFICATION/
- stored_artifacts/TCK-20260904-CAMPSTATE-PLACE-BRIDGE/
- stored_artifacts/TCK-20260904-LAIR-ENTITY-ANCHOR/
- stored_artifacts/TCK-20260904-FACTION-EXPAND-DIRECTIVE/

## Related Code Areas
- data/content/world_modules/ (real content to author)
- src/world/camp.py
- src/world/boss.py
- src/worldbuilding/compiler.py
- src/worldbuilding/recipe.py, src/worldbuilding/schema.py (creature_kind field)
- src/engine/faction_decision.py

## Assumptions / Open Questions
- Whether to extend an existing world module or author a new one is a real content-design call left
  to this ticket's own investigation/plan — the sibling tickets deliberately declined to migrate real
  content to keep their own scope narrow and behavior-neutral; this ticket exists specifically to make
  that call.
- Totem/stockpile/palisade magnitudes (typed scaffolding added by `TCK-20260904-CAMP-NEST-CLASSIFICATION`,
  still unpopulated by any production writer) are a related but distinct gap — this ticket does not
  need to populate them unless doing so is trivial alongside the content authoring above.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled on completion.)
