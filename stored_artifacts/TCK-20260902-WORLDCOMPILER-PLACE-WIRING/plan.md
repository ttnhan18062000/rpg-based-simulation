---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-WORLDCOMPILER-PLACE-WIRING
artifact_type: plan
tags: [content]
---

# Plan — TCK-20260902-WORLDCOMPILER-PLACE-WIRING

1. Add `PlaceRecipeSpec` (content-authoring, recipe layer) to `src/worldbuilding/recipe.py`;
   `RegionRecipeSpec.places: List[PlaceRecipeSpec] = []`.
2. Add `PlaceSpec` (resolved-content layer) to `src/worldbuilding/schema.py`;
   `RegionSpec.places: List[PlaceSpec] = []`.
3. Wire `src/worldassembly/resolver.py`'s `resolve_module_contribution()` (the real Composition-path
   assembly site) to convert `RegionRecipeSpec.places` → `RegionSpec.places`, namespacing place ids with
   the same module `prefix` as their parent region id.
4. Wire `WorldCompiler.compile()` (`src/worldbuilding/compiler.py`) to construct real `PlaceState`
   instances from `r_spec.places`, populate `AuthoritativeState.places` and each region's
   `RegionState.places`.
5. Verify the Composition path is fully covered without extra work, by confirming it round-trips through
   the same `WorldCompiler.compile()` call as the Direct path (via `world.resolved.yaml`) rather than
   having its own separate `AuthoritativeState` construction.
6. Write tests: 6 in `tests/unit/worldbuilding/test_place_wiring.py` (Direct path), 2 in
   `tests/unit/worldassembly/test_resolver.py` (Composition path + backward-compat).
7. Update `docs/world/compiler_contract.md`'s `RegionSpec` field list.
8. Add a parity ledger entry (`SUB-390`) via `tools/parity_ledger_writer.py`.
