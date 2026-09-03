---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-WORLDCOMPILER-PLACE-WIRING
artifact_type: investigation
tags: [content]
---

# Investigation — TCK-20260902-WORLDCOMPILER-PLACE-WIRING

Two production compilation paths confirmed via `docs/world/compiler_contract.md`'s "Two Compilation
Paths" section (not assumed): Direct (`WorldSpec` → `WorldCompiler.compile()`) and Composition
(`WorldModuleSpec` → `WorldAssemblyResolver` → `WorldSpec`, round-tripping through `world.resolved.yaml`
back into the same `WorldCompiler.compile()` call — traced directly via `src/worldbuilding/cli.py`'s
`resolve`/`compile` subcommand handlers).

The ticket's own open question — whether content authoring needs a schema/format update or whether the
compiler can infer Place boundaries from tags — was resolved directly from
`docs/brainstorm/rpg_expected_schemas.html#schema-66`'s "Content Migration Sensitivity Points" table
(found via `search_docs`, once KGMCP reconnected): `WorldModuleSpec.regions` needs a new nested
`places: List[PlaceRecipeSpec]` field — a real schema class addition, not tag inference. The same doc
also confirms `hero_guild_routing` (the Stage B pilot world) already has the right mixed-content shape
to use this schema directly, with no new content authoring needed for the pilot itself.

Real assembly site confirmed via direct code trace (not assumed from the epic doc's earlier framing):
`src/worldassembly/resolver.py`'s `resolve_module_contribution()` (not the `dummy_spec` validation-only
construction elsewhere in the same file) is where `RegionRecipeSpec` → `RegionSpec` conversion actually
happens for the production Composition path.
