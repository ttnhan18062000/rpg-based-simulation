---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-WORLDCOMPILER-PLACE-WIRING
phase: done
date: 2026-09-02
tags: [content]
---

# TCK-20260902-WORLDCOMPILER-PLACE-WIRING

## Title
Wire WorldCompiler to construct Places from content

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 2/5 of `TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD`, depends on
`TCK-20260902-PLACE-SCHEMA-MIGRATION`. Wires `WorldCompiler.compile()` (`src/worldbuilding/compiler.py`,
confirmed the sole production site constructing a populated `AuthoritativeState` from content) to
construct `PlaceState` instances and populate `RegionState.places`/back-references from
`data/content/world_modules/*.yaml`, replacing today's flat sibling-region model. No world content is
recompiled/migrated yet — that is the pilot tickets' job; this ticket makes the compiler *capable* of
producing the new shape.

## Scope
- Extend `WorldCompiler.compile()` to recognize Place-shaped content and construct `PlaceState`
  instances, linked to their parent `RegionState` via the schema migration ticket's dual-sided
  membership.
- Preserve backward output for any content not yet expressed in Place-shaped form (this ticket wires the
  capability; it does not force-migrate all 21 worlds' content — that is the pilot/rollout tickets).

## Out of Scope
- Recompiling/migrating any specific world (pilot tickets).
- Authoring new Place-shaped content.

## Acceptance Criteria
- [x] `WorldCompiler.compile()` can construct a correct `PlaceState`/`RegionState.places` pair from
      Place-shaped content, verified by a direct unit test (not just an integration pilot run).
      6 tests in `tests/unit/worldbuilding/test_place_wiring.py`.
- [x] Existing (non-Place-shaped) content still compiles unchanged — no regression to current worlds
      until they are explicitly migrated by the pilot tickets. Confirmed via
      `test_non_place_shaped_content_compiles_unchanged` and full 893-test regression sweep.

## Related Tickets
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD (parent epic)
- TCK-20260902-PLACE-SCHEMA-MIGRATION (dependency)
- TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT (depends on this)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md`
- `docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md` item 9

## Related Stored Artifacts
(staging artifacts in `staging_artifacts/TCK-20260902-WORLDCOMPILER-PLACE-WIRING/`)

## Related Code Areas
- `src/worldbuilding/compiler.py` (`WorldCompiler.compile()`)
- `src/worldbuilding/schema.py` (new `PlaceSpec`, `RegionSpec.places`)
- `src/worldbuilding/recipe.py` (new `PlaceRecipeSpec`, `RegionRecipeSpec.places`)
- `src/worldassembly/resolver.py` (`WorldAssemblyResolver.resolve_module_contribution()`)
- `docs/world/compiler_contract.md` (Schema Contract section, corrected)
- `data/content/world_modules/*.yaml` (not yet touched — no content authored against the new schema)

## Assumptions / Open Questions
- ~~Whether content authoring needs a schema/format update to express Place-shaped regions, or whether
  the compiler can infer Place boundaries from existing tags~~ — **Resolved.** A real schema/format
  update was needed: `docs/brainstorm/rpg_expected_schemas.html#schema-66`'s own "Content Migration
  Sensitivity Points" table (found via `search_docs` on pickup) had already named the exact answer —
  `WorldModuleSpec.regions` needs a new nested `places: List[PlaceRecipeSpec]` field, not tag inference.
  Implemented as `PlaceRecipeSpec`/`RegionRecipeSpec.places` (`src/worldbuilding/recipe.py`) and
  `PlaceSpec`/`RegionSpec.places` (`src/worldbuilding/schema.py`), wired through
  `WorldAssemblyResolver.resolve_module_contribution()`. The doc's own note that `hero_guild_routing`
  (the Stage B pilot world) already has the right mixed content shape to use this schema directly, with
  no new content authoring needed for the pilot itself, is a useful pointer for the Stage B pilot ticket.

## Implementation Notes
- `docs/world/compiler_contract.md`'s "Two Compilation Paths" section confirmed there are genuinely two
  production paths to wire, not one: the **Direct** path (`WorldSpec` → `WorldCompiler.compile()`) and
  the **Composition** path (`WorldModuleSpec` → `WorldAssemblyResolver` → `WorldSpec`, round-tripping
  through `world.resolved.yaml` back into the same `WorldCompiler.compile()` call — traced directly via
  `src/worldbuilding/cli.py`'s `resolve`/`compile` subcommands, not assumed). Both are wired: the
  Composition path's `WorldAssemblyResolver.resolve_module_contribution()` (`src/worldassembly/resolver.py`)
  converts `RegionRecipeSpec.places` → `RegionSpec.places`, and since that produces a real `WorldSpec`
  that round-trips through the Direct path's already-wired `WorldCompiler.compile()`, no separate
  Place-construction logic was needed in the resolver itself.
- Place ids are namespaced with the same module `prefix` as their parent region id
  (`f"{prefix}{p.id}"`), matching the existing region-id namespacing convention exactly — avoids
  collision if a module is composed multiple times into one world.
- `PlaceRecipeSpec`/`PlaceSpec`'s `kind` field validates against the same 7 `PlaceKind` values as the
  runtime enum, normalized to uppercase — content authoring errors (e.g. a typo'd kind) are caught at
  Pydantic validation time, not silently accepted or discovered later at compile/runtime.
- Confirmed via direct test: existing content with no `places:` declared compiles to `places=[]`
  everywhere (both `AuthoritativeState.places` and every `RegionState.places`), so this ticket changes
  zero existing worlds' compiled output or `state_hash`.

## Test Summary
- 6 new tests in `tests/unit/worldbuilding/test_place_wiring.py`: Direct-path Place construction,
  multiple Places per region, non-Place-shaped content unchanged, mixed Place-shaped/legacy regions
  coexisting in one world, canonical-hash participation, invalid `kind` rejected at schema level.
- 2 new tests in `tests/unit/worldassembly/test_resolver.py`: Composition-path wiring with prefix
  namespacing confirmed, and backward-compat (no-places region resolves to an empty list, not an error).
- Full regression sweep: `pytest tests/unit/worldbuilding/ tests/unit/worldassembly/
  tests/unit/worldmodules/ tests/unit/core/ tests/unit/engine/ tests/unit/kernel/ tests/certification/
  -m "not slow"` → 893 passed, 2 skipped (pre-existing, unrelated), 0 failed.

## Files Changed
- `src/worldbuilding/recipe.py` — new `PlaceRecipeSpec`, `RegionRecipeSpec.places`.
- `src/worldbuilding/schema.py` — new `PlaceSpec`, `RegionSpec.places`.
- `src/worldassembly/resolver.py` — `resolve_module_contribution()`: converts `RegionRecipeSpec.places`
  → prefix-namespaced `RegionSpec.places`.
- `src/worldbuilding/compiler.py` — `WorldCompiler.compile()`: constructs real `PlaceState` instances
  from `r_spec.places`, populates `AuthoritativeState.places` and each `RegionState.places`.
- `docs/world/compiler_contract.md` — corrected the `RegionSpec` field list (was already missing
  `tags`; now also lists `places`).
- `tests/unit/worldbuilding/test_place_wiring.py` — new file, 6 tests.
- `tests/unit/worldassembly/test_resolver.py` — 2 new tests.
- `docs/parity_ledger/substrate.yaml` — new entry `SUB-390`, written via `tools/parity_ledger_writer.py`.
- `tickets/inprogress/TCK-20260902-WORLDCOMPILER-PLACE-WIRING.md` → moved to `tickets/done/`.

## Completion Summary
Landed idea 66's second child ticket: `WorldCompiler.compile()` can now construct real `PlaceState`
instances from Place-shaped content, on both real compilation paths (Direct and Composition). Resolved
the ticket's own open question directly from `docs/brainstorm/rpg_expected_schemas.html#schema-66`,
found via `search_docs` on pickup — a real content-schema addition (`PlaceRecipeSpec`/`PlaceSpec`) was
needed, not tag inference, exactly as that doc's Content Migration Sensitivity Points table had already
specified. No existing content declares `places:` yet, so this ticket changes zero existing worlds'
compiled output — it makes the compiler capable, matching its own explicit scope. Next in the epic's
child-ticket sequence: `TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT`, which can now actually author and
compile a real Place-shaped world.
