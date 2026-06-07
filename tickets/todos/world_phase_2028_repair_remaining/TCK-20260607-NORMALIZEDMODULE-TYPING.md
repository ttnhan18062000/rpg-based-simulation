# TCK-20260607-NORMALIZEDMODULE-TYPING

## Title
Replace List[Any] fields in NormalizedWorldModule with typed ref collections

## Status
OPEN

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
9-phase standard. Investigation must check real YAML module files for dict vs string biome/ecology/population/relationship formats before changing normalizer behavior.

## Test Summary
```
pytest tests/unit/worldmodules/ tests/unit/content/test_reference_graph.py -q
```

## Files Changed
- `src/worldmodules/normalizer.py`
- `src/content/reference_graph.py`
- `tests/unit/worldmodules/test_modules.py`

## Completion Summary
(to be filled)
