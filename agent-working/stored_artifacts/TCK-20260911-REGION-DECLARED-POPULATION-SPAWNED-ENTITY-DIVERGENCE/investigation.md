# Investigation — TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE

## Context Scan (mandatory, run before any grep/file-read)
`mcp__knowledge-search__search_docs` for `PopulationSpec count spawned entity divergence
population_cohorts declared population WorldEntitySpawner` surfaced
`docs/world/demographics_contract.md` §1a (Compile-Time Seeding) as the most relevant existing doc —
read in full below. `graphify query` for the same topic returned the broad worldassembly/worldbuilding
community graph (WorldCompiler, WorldAssemblyResolver, WorldEntitySpawner, PopulationSpec, etc.) —
consistent with what static grep would find, used only to confirm no additional relevant node existed
outside what direct code reading covers below.

## Step 1: intentional vs. accidental — this ticket's own required first Acceptance Criterion
Per the ticket's own Scope: "Determine whether this divergence is intentional... or accidental...
Investigate git history / design docs... before concluding either way — do not assume." Did not
assume; gathered direct evidence from four independent sources before concluding.

**Evidence for "abstract background population, distinct by design" (checked first, since
`docs/world/demographics_contract.md`'s own language uses "abstract"):**
- `docs/world/demographics_contract.md` Overview: "introduces abstract population dynamics to each
  region." `PopulationCohort.count` field doc: "Abstract population count for this bracket."
- This describes `population_cohorts`' own internal accounting (birth/death/migration cycling), not
  a claim about its relationship to spawned entity count.

**Evidence against that reading, and for "accidental divergence" (decisive):**
1. `PopulationSpec.count`'s own field docstring (`src/worldbuilding/schema.py:206`): `"Initial count
   of entities in this population group"` — explicitly "entities," not an abstract background
   number. (Contrast `ResourceNodeSpec.count`, an analogous field on a different spec, worded the
   same literal way: "Total resource charges / stock available.")
2. Mechanics Bible (Certified Level 1 Authoritative) `docs/mechanics/06_worldbuilding_foundation.md`
   line 54: "Population groups define **initial entities**, including counts, roles, factions, and
   spawn regions."
3. Same doc, line 153 (Sidecar Provenance Manifest spec): "**Entity Lineage**: Links unique entity
   IDs back to their parent population ID (`pop_key`) and generator rule." This describes a
   one-population-to-many-entities design (multiple entity IDs, one parent population ID via a
   "generator rule") — not a one-to-one or population-is-abstract-only model.
4. **Decisive, not just textual**: `WorldCompiler.compile()`'s own classic (non-catalog) pipeline
   (`src/worldbuilding/compiler.py:480-546`) ALREADY implements exactly this design today, correctly:
   ```python
   for _ in range(pop_spec.count):
       x = rng.get_int(...); y = rng.get_int(...)
       # de-confliction against occupied_entity_tiles
       ...
       pop_key = getattr(pop_spec, "id", f"pop_{pop_idx}")
       ent_properties = {
           "spawn_region": pop_spec.spawn_region,
           "population_id": pop_key,
           "faction_id": pop_spec.faction,
       }
       # V2EntityBuilder(next_entity_id)... next_entity_id incremented each iteration
   ```
   This is a real loop over `count`, spawning `count` individually-positioned entities, each tagged
   `population_id` for provenance — the exact behavior the Mechanics Bible describes and the exact
   behavior the newer pipeline lacks.

**The newer, catalog/archetype-native pipeline never got this ported.** Confirmed by direct
comparison:
- `CompileProfileResolver.resolve()` (`src/worldassembly/resolver.py:1031-`): `for pop_idx, pop_spec
  in enumerate(getattr(spec, "entities", [])):` — one `ResolvedEntityProfile` registered per
  population, `pop_spec.count` never read in this function at all.
- `ResolvedEntityProfile` (`src/worldassembly/models.py`) has no `count` field — structurally
  incapable of carrying the value forward even if something wanted to read it later.
- `WorldEntitySpawner.spawn_from_context()` (`src/worldassembly/entity_spawner.py:54`): `for _key,
  profile in ctx.entities.items():` — one `EntityState` per profile, no loop over any count.
- Neither `_spawn_archetype_native()` nor `_spawn_legacy_guard()` sets `properties["population_id"]`
  anywhere — confirmed by direct read of both full function bodies.

**Determination: accidental, not intentional.** The classic pipeline already implements the
Mechanics-Bible-described one-population-to-many-entities design correctly, including real
per-individual positions and `population_id` provenance tagging. The newer catalog/archetype-native
pipeline (`CompileProfileResolver.resolve()` → `WorldEntitySpawner.spawn_from_context()`) — the one
`frontier_living_world` and Campaign mode actually use — never ported either behavior when it was
built. This is a real regression relative to an already-correct precedent in the same codebase, not
two deliberately-separate abstraction layers.

## Step 2: same root cause as a second, independently-filed ticket
`TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` (filed the same day, from a
different investigation) found the second half of the same gap: `WorldEntitySpawner`'s catalog
pipeline never sets `properties["population_id"]`, causing `pending_information_responses`'
`target_population_id` → `actor_id` resolution to silently misdeliver seeded facts to an unrelated
entity (verified there with a real example: `frontier_village_population_frontier_guard` resolving
to a goblin raider instead of a human guard). Both tickets independently concluded the same thing:
`WorldCompiler.compile()` (classic) does both count-expansion and population_id-tagging correctly;
`WorldEntitySpawner` (catalog) does neither. Both tickets explicitly flag this and ask whoever picks
either one up to check whether one fix closes both.

**Reported to peer before deciding fix scope**, per this whole audit arc's established discipline
for scope decisions with wider blast radius than the ticket's own narrow framing. Recommended
folding both fixes into one change (same function, same root cause, natural to tag `population_id`
at the same point count-expansion already needs to restructure the loop) — awaiting confirmation
before Implement.

## Confirmed, not assumed: the party-formation ticket's premise holds regardless of this
determination
`TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION`'s blocking-dependency note assumes
`WorldEntitySpawner` spawns exactly one entity per population regardless of `count` is a real
structural fact. Confirmed independently here by the same direct code read (`spawn_from_context()`'s
loop, `CompileProfileResolver.resolve()`'s loop) — true regardless of which fix-scope option is
chosen for this ticket.
