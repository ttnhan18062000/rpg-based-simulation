---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260607-NORMALIZEDMODULE-TYPING
artifact_type: test_plan
tags: [normalizedmodule, typing]
---

# Test Plan — TCK-20260607-NORMALIZEDMODULE-TYPING

## Regression Surface

| File | Risk | Reason |
|---|---|---|
| `tests/unit/worldmodules/test_modules.py` | Medium | `test_normalizer_v1_and_v2` uses `len()` and index `[0]` on biomes — both work on tuple, but no explicit type assertion |
| `tests/unit/content/test_layered_catalog.py` | Low | Uses `ContentReferenceGraph` via `test_phase23_reference_graph_and_dead_active_data`; graph edges for modules may shift if `add_module_edges` changes traversal |
| `tests/unit/worldassembly/test_assembly.py` | Low | Assembly calls `WorldModuleAuthoringNormalizer.normalize()` then `resolve_module_contribution`; field iteration is tuple-safe |
| `tests/unit/content/test_content_usage_matrix.py` | Low | May construct `ContentReferenceGraph` with module fixtures |

---

## New Tests Required (per AC)

### In `tests/unit/worldmodules/test_modules.py`

**1. `test_string_biomes_normalize_to_tuple`**
- Input: `WorldModuleSpec` with `biomes=["forest_edge", "highland"]`
- Assert: `normalized.biomes == ("forest_edge", "highland")`
- Assert: `isinstance(normalized.biomes, tuple)`
- Covers AC: `NormalizedWorldModule.biomes` is `Tuple[str, ...]`

**2. `test_string_ecologies_normalize_to_tuple`**
- Input: `WorldModuleSpec` with `ecologies=["wetland_ecology"]`
- Assert: `normalized.ecologies == ("wetland_ecology",)` and `isinstance(normalized.ecologies, tuple)`
- Covers AC: ecologies field is `Tuple[str, ...]`

**3. `test_string_populations_normalize_to_tuple`**
- Input: `WorldModuleSpec` with `populations=["goblin_scout", "wolf_pack"]`
- Assert: `normalized.populations == ("goblin_scout", "wolf_pack")` and `isinstance(normalized.populations, tuple)`
- Covers AC: populations field is `Tuple[str, ...]`

**4. `test_string_relationships_normalize_to_tuple`**
- Input: `WorldModuleSpec` with `relationships=["town_to_bandits"]`
- Assert: `normalized.relationships == ("town_to_bandits",)` and `isinstance(normalized.relationships, tuple)`
- Covers AC: relationships field is `Tuple[str, ...]`

**5. `test_empty_ref_fields_normalize_to_empty_tuple`**
- Input: `WorldModuleSpec` with no biomes/ecologies/populations/relationships
- Assert all four fields are `()` (empty tuple), not `[]`
- Covers AC: empty input stays typed

**6. `test_dict_with_id_biome_normalizes_to_id_string`**
- Input: normalizer called directly with `biomes=[{"id": "deep_forest"}]` (bypassing Pydantic — use a mock spec or adapt the normalizer to accept raw lists)
- Assert: result biomes == `("deep_forest",)`
- Covers AC: dict-with-id accepted
- Note: This tests the normalizer's standalone API, not a real WorldModuleSpec path

**7. `test_dict_without_id_biome_raises_normalization_error`**
- Input: dict without `id` key, e.g. `{"name": "deep_forest"}`
- Assert: raises `NormalizationError` (or the chosen exception type) with a descriptive message
- Covers AC: dict-without-id rejected clearly

**8. `test_duplicate_biome_ref_fails`**
- Input: `biomes=["forest_a", "forest_a"]` — Note: `WorldModuleSpec.biomes: List[str]` does NOT deduplicate at Pydantic level, so duplicates will reach the normalizer
- Assert: raises `ValueError` or `NormalizationError` naming the duplicate
- Covers AC: duplicate refs fail clearly

### In `tests/unit/content/test_reference_graph.py` (new file) or `test_content_usage_matrix.py`

**9. `test_add_module_edges_adds_biome_edges`**
- Build a `NormalizedWorldModule` with `biomes=("highland_biome",)` and minimal other fields
- Call `graph.add_module_edges(normalized_module)`
- Assert: edge `module:test_mod → biome:highland_biome` exists in `graph.edges`
- Covers AC: `add_module_edges` adds biome edges

**10. `test_add_module_edges_adds_ecology_population_relationship_edges`**
- Build a `NormalizedWorldModule` with one entry in each of `ecologies`, `populations`, `relationships`
- Call `graph.add_module_edges(normalized_module)`
- Assert all four edge types (biome, ecology, population, faction_relationship) are present
- Covers AC: all four field types produce edges

**11. `test_add_module_edges_uses_normalized_ids_not_raw_dicts`**
- Construct a `NormalizedWorldModule` where biomes is `("clean_id",)` (already normalized)
- Assert: edge target is `biome:clean_id`, not `biome:{'id': 'clean_id'}` or similar
- Covers AC: graph code never parses YAML comments or raw dict shapes

**12. `test_graph_build_uses_add_module_edges`** (integration)
- Construct `ContentReferenceGraph` with a `WorldModuleSpec` fixture that has a non-empty `biomes` list
- Assert the graph edges contain `module:{id} → biome:{id}` entries
- Verifies the graph build flow goes through `add_module_edges` path
- Covers AC: graph-building flow uses normalized module refs

---

## Update Existing Tests

**`test_normalizer_v1_and_v2` in `test_modules.py`:**
- Add `assert isinstance(normalized_v2.biomes, tuple)` after line 114
- Add `assert isinstance(normalized_v1.biomes, tuple)` after line 97
- Keeps regression lock on type contract

---

## Scoped Pytest Commands

```bash
# Primary: normalizer and reference graph
pytest tests/unit/worldmodules/ tests/unit/content/test_reference_graph.py -q

# Regression: assembly and content usage matrix
pytest tests/unit/worldassembly/ tests/unit/content/ -q

# Full fast suite (no slow markers)
pytest tests/unit/ -m "not slow" -q
```

---

## Anti-Drift Guards

1. **Type assertion tests (tests 1–5)** lock `isinstance(x, tuple)` — prevent a future regression that changes back to `list`.
2. **`test_add_module_edges_uses_normalized_ids_not_raw_dicts` (test 11)** prevents re-introduction of dict-shape traversal in graph code.
3. **`test_graph_build_uses_add_module_edges` (test 12)** ensures the graph constructor does not bypass the new method.
4. **Duplicate detection test (test 8)** ensures the normalizer's new validation branch doesn't get silently removed.
