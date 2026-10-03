---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH
phase: done
date: 2026-09-11
tags: [world, content, architecture]
---

# TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH

## Title
The obvious fix for Campaign's `pending_information_responses` gap is wrong — threading it naively silently delivers seeded knowledge to the wrong entity

## Status
DONE

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
- `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE` (done, since this ticket was
  filed) — **this ticket's own "never sets `population_id` anywhere" claim is now stale.**
  Re-checked 2026-09-13 while cross-referencing the spawn-region precedent below: that ticket's own
  fix now sets `properties["population_id"]` in both `entity_spawner.py` (`population_id=_key`,
  matching `resolver.py`'s `PopulationSpec.id`-keyed registration) and `archetype_factory.py`
  (`properties["population_id"] = spawn.population_id`), confirmed via direct grep — zero hits is
  no longer accurate. **This does not mean the mismatch is resolved** — this ticket's own central
  warning applies to this exact temptation: a field being present is not the same as the resolution
  producing the *correct* `actor_id`, which is only provable the way this ticket's own worked
  example does it (a real `frontier_living_world` run, checking `actor_id=9` resolves to the
  intended entity, not just that `population_id` is non-empty). Whoever picks this ticket up should
  re-run that exact empirical check first — it may turn out Direction 1 is now already implemented
  incidentally, or it may turn out the key format/individual-index alignment still doesn't match
  `target_population_id`'s expectations. Not assumed either way here.
- `TCK-20260911-ENTITYSPAWNCONTEXT-SPAWN-REGION-THREADING-GAP` (done, 2026-09-13) — **a working
  precedent for this ticket's own Direction 1.** That ticket threaded `spawn_region` (a different
  field, same shape of gap) from `PopulationSpec` through `ResolvedEntityProfile` and into
  `EntitySpawnContext`/`archetype_factory.py`'s `properties` dict — the identical mechanism
  Direction 1 would need for `population_id`/individual-index identity. The fix pattern (add the
  field to `ResolvedEntityProfile`, set it at both `resolver.py` construction sites, read it at
  `spawn_from_context()` instead of hardcoding a default) is now a proven, working template in this
  exact file, not something to re-derive from scratch.

## Related Docs
None yet.

## Related Stored Artifacts
`staging_artifacts/TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH/investigation.md`
— full empirical re-verification (all 16 population groups in `frontier_living_world` checked, not
just the worked example) and the fix's design/rationale. `plan.md`/`test_plan.md` for the full
build and test breakdown.

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
- **Added 2026-09-13**: Direction 1 may already be partially or fully done, incidentally, by
  `TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE`'s own fix — see the Related
  Tickets correction above. First real step when this ticket is picked up: re-run the ticket's own
  empirical check (`frontier_living_world`, does `actor_id=9` now resolve to the intended frontier
  guard rather than the goblin raider) before assuming any further implementation is needed at all.

## Implementation Notes
**Re-verified the ticket's own premise empirically before implementing**, per explicit peer
instruction: the "population_id never set anywhere" claim was confirmed stale
(`TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE` added it since this ticket
was filed), and the ticket's own worked example (`frontier_living_world`, `actor_id=9`) no longer
reproduces the goblin-raider misdelivery — checked all 16 population groups in that world, not
just the one example, zero actor_id mismatches found between `WorldCompiler.compile()`'s own
entity space and Campaign's own catalog-spawn entity space today.

**What was still real and unfinished**: neither `pending_information_responses` nor
`pending_self_model_information_events` was threaded into Campaign's `AuthoritativeState` at all
(2 separate "deliberately not threaded yet" comments in `orchestrator.py`). Built the real fix:
extracted `WorldCompiler.compile()`'s own resolution logic into a shared
`WorldCompiler.resolve_pending_information()` staticmethod (parameterized on the entities dict, so
it isn't hardcoded to `compile()`'s own entity space), then threaded both fields into both
`_build_initial_state()` branches, each resolving against that branch's own real entities dict
(fresh catalog roster / reconstructed survivor roster) — never reusing `compile()`'s own resolved
`actor_id` values, since that alignment, though empirically true for `frontier_living_world` today,
is not a documented or structurally-guaranteed invariant between the two independently-implemented
spawn pipelines.

Full detail (including the exact empirical checks run) in staging_artifacts/investigation.md.

## Test Summary
See staging_artifacts (→ stored_artifacts) test_plan.md for the full list. 4 new tests, all
asserting the resolved entity's own `population_id` (not list length) — matching the ticket's own
acceptance bar exactly, including a full real-episode `AuthoritativeApplyPipeline.refine()` run
proving `InformationBeliefPhase.apply()` assimilates the fact into the correct entity. 1
pre-existing negative-assertion test updated (its own premise is now resolved). Broader regression:
673 passed, 1 skipped across worldbuilding/campaigns/worldassembly/cognition/scenario-runtime
suites.

## Files Changed
- `src/worldbuilding/compiler.py` — extracted `resolve_pending_information()` as a shared
  staticmethod; `compile()` now calls it (behavior-preserving refactor).
- `src/domains/campaigns/orchestrator.py` — threaded `pending_information_responses`/
  `pending_self_model_information_events` into both `_build_initial_state()` branches.
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py` — 3 new tests, 1 updated.
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py` — 1 new test.
- `staging_artifacts/TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH/{investigation,plan,test_plan}.md`.

## Completion Summary
Re-verified the ticket's own premise before touching any code, per explicit instruction, and found
it partially stale: the population_id tagging fix landed since this ticket was filed, and the
originally-reported goblin-raider misdelivery no longer reproduces for the worked example. The
underlying threading gap was still real, though — neither pending-information field reached
Campaign's `AuthoritativeState` at all. Built the fix as originally scoped (Direction 2: resolve
locally against Campaign's own roster), now cheaper than the ticket anticipated since the
population_id groundwork already existed from a different ticket. Both fields now thread into both
episode-0 and survivor-reconstruction branches, resolved against each branch's own real entity
space, with the acceptance bar (prove the resolved entity is correct, not just present) satisfied
by tests that read the resolved entity's own identity, plus one full real-episode integration test
proving the downstream `InformationBeliefPhase` consumer actually assimilates the fact correctly.
