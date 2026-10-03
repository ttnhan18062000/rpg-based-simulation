# Investigation — TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH

## Re-verification of the ticket's own premise (required before implementing, per peer instruction)

The ticket's own Request Summary claims `WorldEntitySpawner`/`ArchetypeEntityFactory` "never sets
`properties["population_id"]` anywhere." This is stale: `TCK-20260911-REGION-DECLARED-POPULATION-
SPAWNED-ENTITY-DIVERGENCE` (done, after this ticket was filed) added exactly that tagging to both
`src/worldassembly/entity_spawner.py` (`population_id=_key`) and `src/entities/archetype_factory.py`
(`properties["population_id"] = spawn.population_id`). The ticket's own later Related Tickets note
already flagged this staleness and asked whoever picks it up to re-run the empirical check rather
than assume either way — done here, not skipped.

**Empirical re-run of the ticket's own worked example** (`frontier_living_world`, seed=42): built a
real `CampaignOrchestrator` and called `_build_initial_state()` (Campaign's real catalog-spawn
path) alongside a direct `WorldCompiler.compile()` call (the ticket's own original repro path),
then compared every population group's actor_id assignment between the two:

- `WorldCompiler.compile()` resolves `target_population_id='frontier_village_population_frontier_guard'`
  to `actor_id=9`, `kind="guard"` — matches the ticket's own claim exactly.
- Campaign's own catalog-spawned roster (`CatalogScenarioStateBuilder.build()` →
  `WorldEntitySpawner.spawn_from_context()`) now ALSO has `actor_id=9` with
  `population_id="frontier_village_population_frontier_guard"` — **not a goblin raider**. The
  ticket's own worked example no longer reproduces.
- Checked all 16 population groups (49 total entities) in `frontier_living_world`, not just the one
  worked example: every population's actor_id list is byte-identical between `WorldCompiler.compile()`'s
  own entity space and Campaign's own catalog-spawn entity space. Zero mismatches.

**What this does and doesn't mean.** The population_id tagging fix is real and correctly populated
now — the premise is stale. But this alignment across two independently-implemented spawn pipelines
(compiler.py's classic loop vs. `WorldEntitySpawner`'s catalog-native loop) is not a documented or
structurally-guaranteed invariant anywhere in the codebase — it holds today because both pipelines
happen to process this world's populations in the same order with the same counts, not because
anything enforces that. Reusing `WorldCompiler.compile()`'s own pre-resolved `actor_id` values
directly (the "naive fix" the ticket explicitly warns against) would happen to work for this
content today, but is not something to build the real fix on. The robust fix — resolving
`target_population_id` against Campaign's OWN entities dict, independent of `WorldCompiler.compile()`'s
own numbering — is correct regardless of whether the two pipelines' numbering coincides, and is what
this ticket's own acceptance bar ("prove the resolved entity IS the intended one") actually demands.

**What is still real, unfinished work, confirmed via a second grep-based check**: neither
`pending_information_responses` nor `pending_self_model_information_events` is threaded into
`CampaignOrchestrator._build_initial_state()` at all — both of that method's two branches carry an
explicit comment saying so ("deliberately NOT threaded here yet" / "intentionally not threaded here
either"). The mismatch premise is stale; the missing threading is not. This ticket's real remaining
scope is: build the threading, using the population_id tagging that already exists, resolved
against Campaign's own roster rather than reused from `WorldCompiler.compile()`.

## Fix built

`WorldCompiler.resolve_pending_information(entities, pending_information_response_specs,
pending_self_model_information_event_specs)` — extracted `compile()`'s own inline
`target_population_id → actor_id` resolution logic (previously hardcoded to `compile()`'s own
`entities` local) into a shared, parameterized staticmethod. `compile()` itself now calls this same
method against its own `entities` dict — byte-identical behavior, confirmed via the full existing
`test_world_compiler.py` suite (8 pre-existing tests covering this exact resolution, all still
green) and the empirical alignment check above (unchanged results before/after the extraction).

`CampaignOrchestrator._build_initial_state()`'s both branches now call this same shared method:
- **Episode-0 branch**: resolves against `catalog_result.state.entities` (the fresh catalog-spawned
  roster for this episode) — the entity space that actually matters for Campaign mode, not
  `compiled_state`'s own separate one.
- **Survivor-reconstruction branch (episode N>0)**: resolves against `entities` (the reconstructed
  survivor roster). Verified `population_id` survives the carry-forward round-trip
  (`EntityCarryForward.properties` mirrors `entity.identity.properties` at capture time, confirmed
  via `src/domains/campaigns/orchestrator.py:840`'s own `properties=dict(cf.properties)`). A
  population with no surviving member this episode correctly resolves to "no match, skip" (matching
  `WorldCompiler.compile()`'s own existing behavior for an unmatched population), not a misdelivery
  to an unrelated entity that happens to hold that population's old actor_id.

Both fields threaded into both branches, per the ticket's own Scope instruction (mirroring the
already-shipped `information_source_profiles` fix, which is threaded into both branches too, with
no actor-ID dependency of its own).

## Real, end-to-end proof (not just non-empty)

Per the ticket's own acceptance bar, every new test asserts on the *resolved entity's own
population_id*, never just list length:
- `frontier_living_world`'s real seeded fact (`trade_road_bandit_activity`/`danger_rating`,
  certainty=0.8 — the ticket's own worked example) resolves through the real
  `CampaignOrchestrator._build_initial_state()` to an entity whose `population_id` is
  `frontier_village_population_frontier_guard` — proven, not assumed.
- `unit_selfmodel_pilot`'s real seeded `pending_self_model_information_events` entry (targeting
  `pop_1`, an unknown fact about `material.wood.source`) resolves to the entity carrying
  `population_id="pop_1"`.
- A fabricated survivor carry-forward with `population_id="frontier_village_population_frontier_guard"`
  proves the episode-N>0 branch resolves against the survivor roster, not a stale/unrelated space.
- A full real-episode integration test drives the Campaign-built state through
  `AuthoritativeApplyPipeline.refine()` and confirms `InformationBeliefPhase.apply()` actually fires
  `belief_assimilated` for the correct entity, with the correct assimilated `KnowledgeFact` — the
  ticket's own explicit Scope bullet, not left as an assumption from shape-matching alone.
