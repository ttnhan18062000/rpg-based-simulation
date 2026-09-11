---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH
phase: open
date: 2026-09-11
tags: [world, content, architecture]
---

# TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH

## Title
The obvious fix for Campaign's `pending_information_responses` gap is wrong — threading it naively silently delivers seeded knowledge to the wrong entity

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
**The obvious fix here is wrong, and this ticket exists to stop someone from shipping it.** Do
NOT thread `compiled_state.pending_information_responses` directly into
`CampaignOrchestrator._build_initial_state()`'s returned `AuthoritativeState` — it looks identical
to the correct, already-shipped fix for `information_source_profiles`
(`TCK-20260909-CAMPAIGN-INFORMATION-SOURCE-PROFILES-NOT-THREADED`) and will compile, pass a
naive smoke test, and silently misdeliver a seeded fact to a random unrelated entity.

**Proof, not assertion.** `WorldCompiler.compile()` resolves each `pending_information_responses`
entry's `target_population_id` into an `actor_id` (`src/worldbuilding/compiler.py:660-664`) by
matching against `entity.properties.get("population_id")` on **its own internally-compiled entity
dict** (`compiler.py:546` sets `"population_id": pop_key` when building that dict). Campaign mode
does not use that entity dict at all — it spawns entities via the separate, catalog-native
`WorldEntitySpawner`/`ArchetypeEntityFactory` pipeline (`src/worldassembly/entity_spawner.py`,
`src/entities/archetype_factory.py`), which **never sets `properties["population_id"]` anywhere**
(confirmed: zero hits for `"population_id"` in `src/worldassembly/` or `src/entities/`, only
docstring mentions elsewhere).

Verified empirically against real content, not just traced: for `frontier_living_world`,
`WorldCompiler.compile()` resolves `target_population_id='frontier_village_population_frontier_guard'`
to `actor_id=9`. In Campaign's own real, catalog-spawned entity roster for the identical world
composition and seed, `entity_id=9` is a **goblin_raider** — an entirely unrelated entity from a
different faction, species, and population group. A `trade_road_bandit_activity`/`danger_rating`
fact (certainty=0.8) intended for a human frontier guard would be silently assimilated into a
goblin raider's beliefs instead. This is worse than the current "never fires" state: a visible gap
gets noticed; a bug that fires and silently delivers plausible-looking data to the wrong entity
looks like emergent behavior and could survive undetected for months.

## Scope
- Design a correct way to resolve `PopulationSpec`/`target_population_id` identity against
  Campaign's own catalog-spawned entity roster. Two candidate directions (decide during
  Investigate, don't assume either is right):
  1. Tag Campaign-spawned entities with their own `population_id` inside `WorldEntitySpawner`
     itself (the `ctx.entities` key each profile was registered under, matching
     `compiler.py:546`'s own convention) — a shared-pipeline change affecting every
     `WorldEntitySpawner` consumer, not Campaign-local, so it needs the same scrutiny any shared
     spawner change gets.
  2. Re-resolve `pending_information_responses`' `target_population_id` against Campaign's own
     roster at `_build_initial_state()` time instead, independent of `WorldCompiler.compile()`'s
     own resolution — Campaign-local, smaller blast radius, but duplicates resolution logic that
     already exists in `compiler.py`.
- Whichever direction is chosen, add a real test proving the resolved `actor_id` in the final
  Campaign state actually corresponds to the intended `target_population_id`'s entity — not just
  that the field is non-empty (the exact class of false-positive this ticket exists to prevent).
- Once resolved, thread `pending_information_responses` into both `_build_initial_state()`
  branches (mirroring the already-shipped `information_source_profiles` fix), and confirm
  `InformationBeliefPhase.apply()` actually assimilates the fact into the *correct* entity in a
  real Campaign episode run.

## Out of Scope
- `information_source_profiles` — already correctly threaded in
  `TCK-20260909-CAMPAIGN-INFORMATION-SOURCE-PROFILES-NOT-THREADED`, no actor-ID dependency, not
  affected by this gap.
- `pending_self_model_information_events` — same `target_population_id` → `actor_id` resolution
  pattern as `pending_information_responses` (`compiler.py:685-713`), and therefore has the
  identical mismatch risk if it were ever threaded into Campaign mode — but it is not currently
  threaded and not part of this investigation's own scope. Worth a note for whoever picks this
  up: the fix chosen here should probably cover both fields, since they share the exact same root
  cause.

## Related Tickets
- `TCK-20260909-CAMPAIGN-INFORMATION-SOURCE-PROFILES-NOT-THREADED` (origin of this finding —
  closed partial, with `information_source_profiles` shipped and this field's own fix split out
  here per peer review)
- `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE` — **likely the same root
  cause, not just a related symptom.** That ticket found `WorldEntitySpawner`'s catalog-native
  pipeline never expands `PopulationSpec.count` into individually-spawned entities; this ticket
  found the same pipeline never sets `population_id` on what it does spawn. Both are instances of
  **the catalog spawn path not carrying population identity through** — `WorldCompiler.compile()`
  (the classic pipeline) does both correctly; `WorldEntitySpawner` (the catalog pipeline Campaign
  actually uses) does neither. Whoever picks up either ticket should check whether one fix —
  threading real `PopulationSpec` identity (`id`, individual index within `count`) into
  `WorldEntitySpawner`'s own output — closes both, rather than scoping each narrowly and
  potentially fixing the same underlying gap twice.

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/worldbuilding/compiler.py` (`WorldCompiler.compile()`, the `target_population_id` →
  `actor_id` resolution at lines 660-664 and 690-694)
- `src/worldassembly/entity_spawner.py`, `src/entities/archetype_factory.py` (Campaign's own
  catalog-native spawn pipeline — never sets `population_id`)
- `src/domains/campaigns/orchestrator.py` (`_build_initial_state()`, where the fix ultimately
  lands once the resolution question is settled)

## Assumptions / Open Questions
- Whether Direction 1 (tag `population_id` in `WorldEntitySpawner`) or Direction 2 (re-resolve
  Campaign-locally) is correct is not decided here — real Investigate/Plan work for whoever picks
  this up. Direction 1 is likely the more durable fix given its connection to
  `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE`, but confirm rather than
  assume.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
