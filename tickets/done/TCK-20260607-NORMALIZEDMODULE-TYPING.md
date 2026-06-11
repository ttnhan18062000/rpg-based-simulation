---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260607-NORMALIZEDMODULE-TYPING
phase: done
date: 2026-06-07
tags: [normalizedmodule, typing]
---

# TCK-20260607-NORMALIZEDMODULE-TYPING

## Title
Replace List[Any] fields in NormalizedWorldModule with typed ref collections

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`NormalizedWorldModule` in `src/worldmodules/normalizer.py` has four fields typed as
`List[Any]` — `biomes`, `ecologies`, `populations`, `relationships`. These should be
typed as `tuple[str, ...]` (immutable ID ref sequences) since they contain catalog reference
IDs after normalization, not inline definitions.

Additionally, `ContentReferenceGraph` in `src/content/reference_graph.py` imports and
consumes raw `WorldModuleSpec` directly instead of `NormalizedWorldModule`, so graph edges
for modules are built without the normalization guarantees.

## Scope

### Fix 1 — `NormalizedWorldModule` field typing (`normalizer.py`)

Current:
```python
biomes: List[Any]
ecologies: List[Any]
populations: List[Any]
relationships: List[Any]
```

Target:
```python
biomes: Tuple[str, ...]
ecologies: Tuple[str, ...]
populations: Tuple[str, ...]
relationships: Tuple[str, ...]
```

Normalizer must:
- Accept `List[str]` → tuple of strings
- Accept `List[dict]` with `id` key → tuple of ID strings
- Reject `List[dict]` without `id` key → raise `NormalizationError`

### Fix 2 — `ContentReferenceGraph` to accept `NormalizedWorldModule` for module edges

Current: `reference_graph.py` builds module edges from `WorldModuleSpec` fields directly.

Add:
```python
def add_module_edges(self, normalized_module: NormalizedWorldModule) -> None:
    """Add edges from a normalized module into the reference graph."""
```

Edges to add:
```
module → biome   (each ID in normalized_module.biomes)
module → ecology (each ID in normalized_module.ecologies)
module → population (each ID in normalized_module.populations)
module → relationship (each ID in normalized_module.relationships)
module → resource (each key in normalized_module.resources)
module → building (each key in normalized_module.buildings)
module → service  (each key in normalized_module.services)
```

Update the graph-building flow in `assemble()` or the graph constructor to call
`add_module_edges(normalized_module)` instead of using raw spec fields.

### Tests

Add in `tests/unit/worldmodules/test_modules.py`:
```
- list of string biomes normalizes to tuple
- dict-with-id biome normalizes to ID string
- dict-without-id biome raises NormalizationError
- duplicate biome refs in input fail clearly
```

Add in `tests/unit/content/test_reference_graph.py` (or `test_content_usage_matrix.py`):
```
- add_module_edges adds biome/ecology/population/relationship edges
- add_module_edges uses normalized IDs, not raw dicts
```

## Out of Scope
- Do not change `WorldModuleSpec` (raw authoring schema stays flexible)
- Do not change `resource_refs`/`building_refs`/`service_refs` (already `Dict[str, int]`)
- Do not change graph edge structure beyond adding module→catalog edges

## Acceptance Criteria
- [ ] `NormalizedWorldModule.biomes/ecologies/populations/relationships` are `Tuple[str, ...]`
- [ ] Normalizer converts list-of-strings and list-of-dicts-with-id correctly
- [ ] Normalizer rejects dict-without-id with a clear error
- [ ] `ContentReferenceGraph.add_module_edges(NormalizedWorldModule)` exists
- [ ] Graph building flow uses normalized module refs, not raw spec
- [ ] All existing real module tests pass
- [ ] No graph code parses YAML comments or raw dict shapes

## Related Tickets
- TCK-20260607-RESOLVER-BOUNDARY (companion — typed input boundary)

## Related Docs
- `world_phase_20_28_repair_remaining.md` R3.1, R3.2

## Related Code Areas
- `src/worldmodules/normalizer.py:14-32`
- `src/content/reference_graph.py:168-214`
- `tests/unit/worldmodules/test_modules.py`

## Assumptions / Open Questions
- Are there real modules that use dict-with-id format for biomes/ecologies? Check `data/content/world_modules/*.yaml` before implementing.

## Implementation Notes
All seven real YAML module files use plain string lists for biomes/ecologies/populations/relationships — no dict-with-id format exists in real data. The dict-with-id branch in `_normalize_ref_list` is defensive infrastructure for a future authoring path.

`NormalizationError(ValueError)` defined locally in `normalizer.py` — no shared errors module existed.

`add_module_edges` passes count metadata (`{"count": count}`) for resources/buildings/services edges, preserving parity with the old inline loop's behavior in `_build_graph`. This was caught by `test_layered_catalog.py::test_graph_module_count_maps_and_metadata`.

`_build_graph` factions loop (`for faction in module.factions`) was kept inline (not folded into `add_module_edges`) because factions come from raw `WorldModuleSpec`, not `NormalizedWorldModule`. Only the four V2 layout tuple fields and the resources/buildings/services dict loops were replaced by `add_module_edges`.

`test_string_relationships_normalize_to_tuple` uses `module_type="ecology"` — `"social"` is not a registered module type in `WorldModuleSpec`.

Pre-existing worldassembly failures (`CAT-REL-099` missing `apprentice_mage` population) confirmed to be unrelated to this ticket.

## Test Summary
```
pytest tests/unit/worldmodules/ tests/unit/content/test_reference_graph.py tests/unit/content/test_layered_catalog.py -q
```
29 passed.

## Files Changed
- `src/worldmodules/normalizer.py`
- `src/content/reference_graph.py`
- `tests/unit/worldmodules/test_modules.py`
- `tests/unit/content/test_reference_graph.py` (new)

## Completion Summary
Replaced List[Any] with Tuple[str, ...] on NormalizedWorldModule.biomes/ecologies/populations/relationships. Added NormalizationError(ValueError) and _normalize_ref_list() helper in normalizer.py. Updated WorldModuleAuthoringNormalizer.normalize() to use _normalize_ref_list(). Added ContentReferenceGraph.add_module_edges(NormalizedWorldModule) and replaced inline V2 layout loops in _build_graph. Added 13 new tests (9 in test_modules.py, 4 in test_reference_graph.py). All tests passing.
