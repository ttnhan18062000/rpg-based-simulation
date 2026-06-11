---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260607-NORMALIZEDMODULE-TYPING
artifact_type: plan
tags: [normalizedmodule, typing]
---

# Implementation Plan — TCK-20260607-NORMALIZEDMODULE-TYPING

## Accepted Types

From investigation:

| Field | From | To |
|---|---|---|
| `biomes` | `List[Any]` | `Tuple[str, ...]` |
| `ecologies` | `List[Any]` | `Tuple[str, ...]` |
| `populations` | `List[Any]` | `Tuple[str, ...]` |
| `relationships` | `List[Any]` | `Tuple[str, ...]` |

`NormalizationError` does not exist in the codebase yet. It will be defined in `normalizer.py` as a local exception class (or imported from a shared errors module if one exists — check during implementation).

---

## Ordered Steps

### Step 1 — Add `NormalizationError` to `normalizer.py`

**Scope guard:** New exception class only. No behavior change.

Add above the `@dataclass` definition:
```python
class NormalizationError(ValueError):
    """Raised when a module field cannot be normalized to a typed ref collection."""
```

AC mapped: "Normalizer rejects dict-without-id with a clear error"

---

### Step 2 — Add `_normalize_ref_list()` helper to `normalizer.py`

**Scope guard:** New private function only. Does not touch `NormalizedWorldModule` definition yet.

```python
def _normalize_ref_list(value: List[Any], *, field_name: str) -> Tuple[str, ...]:
    """
    Normalize a raw ref list to an immutable tuple of string IDs.
    - List[str]: validate no duplicates, return as tuple.
    - List[dict] with 'id' key: extract IDs, validate no duplicates, return as tuple.
    - List[dict] without 'id' key: raise NormalizationError.
    - Other element types: raise NormalizationError.
    """
    seen: set = set()
    result: list = []
    for item in value:
        if isinstance(item, str):
            item_id = item
        elif isinstance(item, dict):
            item_id = item.get("id")
            if not item_id or not isinstance(item_id, str):
                raise NormalizationError(
                    f"Dict entry in '{field_name}' has no valid 'id' key: {item!r}"
                )
        else:
            raise NormalizationError(
                f"Unexpected element type {type(item).__name__!r} in '{field_name}': {item!r}"
            )
        if item_id in seen:
            raise NormalizationError(
                f"Duplicate ref '{item_id}' in '{field_name}' is rejected."
            )
        seen.add(item_id)
        result.append(item_id)
    return tuple(result)
```

AC mapped: "Normalizer converts list-of-strings and list-of-dicts-with-id", "Normalizer rejects dict-without-id"

---

### Step 3 — Update `NormalizedWorldModule` field types

**Scope guard:** Type annotation change only. `frozen=True` dataclass — no mutation path changes.

In `normalizer.py` lines 29–32, change:
```python
biomes: List[Any]
ecologies: List[Any]
populations: List[Any]
relationships: List[Any]
```
to:
```python
biomes: Tuple[str, ...]
ecologies: Tuple[str, ...]
populations: Tuple[str, ...]
relationships: Tuple[str, ...]
```

Update imports: add `Tuple` to the `from typing import` line; remove `Any` if no longer needed elsewhere (check — `Any` is used in `normalize_count_map` parameter type, keep it).

AC mapped: "`NormalizedWorldModule.biomes/ecologies/populations/relationships` are `Tuple[str, ...]`"

---

### Step 4 — Update `WorldModuleAuthoringNormalizer.normalize()` to use `_normalize_ref_list`

**Scope guard:** Replace the four bare `list(spec.X)` calls with `_normalize_ref_list(list(spec.X), field_name="X")`. No other change in `normalize()`.

```python
biomes=_normalize_ref_list(list(spec.biomes), field_name="biomes"),
ecologies=_normalize_ref_list(list(spec.ecologies), field_name="ecologies"),
populations=_normalize_ref_list(list(spec.populations), field_name="populations"),
relationships=_normalize_ref_list(list(spec.relationships), field_name="relationships"),
```

Note: `spec.biomes` is already `List[str]` (Pydantic-validated), so the dict-with-id branch is defensive but will not fire in normal use. The duplicate-detection branch is active.

AC mapped: All normalizer ACs (conversion + rejection)

---

### Step 5 — Add `add_module_edges()` to `ContentReferenceGraph`

**Scope guard:** New public method on `ContentReferenceGraph`. Does not change the constructor signature or `_build_graph` yet.

In `src/content/reference_graph.py`, after `is_record_used()` (line 209), add:

```python
def add_module_edges(self, normalized_module: "NormalizedWorldModule") -> None:
    """Add edges from a normalized module into the reference graph."""
    from src.worldmodules.normalizer import NormalizedWorldModule  # local import to avoid circular
    module_node = f"module:{normalized_module.module_id}"
    for b_id in normalized_module.biomes:
        self.add_edge(module_node, f"biome:{b_id}")
    for e_id in normalized_module.ecologies:
        self.add_edge(module_node, f"ecology:{e_id}")
    for p_id in normalized_module.populations:
        self.add_edge(module_node, f"population:{p_id}")
    for rel_id in normalized_module.relationships:
        self.add_edge(module_node, f"faction_relationship:{rel_id}")
    for res_id in normalized_module.resources:
        self.add_edge(module_node, f"resource:{res_id}")
    for bld_id in normalized_module.buildings:
        self.add_edge(module_node, f"building:{bld_id}")
    for svc_id in normalized_module.services:
        self.add_edge(module_node, f"service:{svc_id}")
```

AC mapped: "`ContentReferenceGraph.add_module_edges(NormalizedWorldModule)` exists"

---

### Step 6 — Update `_build_graph()` to call `add_module_edges` instead of inline loops

**Scope guard:** Replace the inline biome/ecology/population/relationship loops in `_build_graph` (lines 289–298) with a normalize-then-call pattern.

Current inline loop in `_build_graph` (lines 289–298):
```python
for biome in module.biomes:
    self.add_edge(module_node, f"biome:{biome}")
for ecology in module.ecologies:
    ...
```

The `modules` parameter is `List[WorldModuleSpec]`. Normalize each spec before calling `add_module_edges`:

```python
from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
...
for module in modules:
    module_node = f"module:{module.module_id}"
    self.add_node(module_node, module)
    # existing: requires, regions, recipes ...
    # Replace inline V2 loops with:
    normalized = WorldModuleAuthoringNormalizer.normalize(module)
    self.add_module_edges(normalized)
    # resources/buildings/services dict loop follows (keep as-is, or fold into add_module_edges)
```

Carefully: The existing code also handles `module.requires`, `module.regions`, `module.population_recipes`, `module.resource_recipes`, `module.building_recipes`, and `module.factions` inline. Only the four `List[Any]` field loops (lines 289–298) plus the dict loops for resources/buildings/services at lines 301–309 are being replaced. The other inline loops (requires, regions, recipes, factions) are NOT changed.

AC mapped: "Graph building flow uses normalized module refs, not raw spec"; "No graph code parses YAML comments or raw dict shapes"

---

### Step 7 — Write new tests in `tests/unit/worldmodules/test_modules.py`

Add the following test functions (per test plan):
- `test_string_biomes_normalize_to_tuple`
- `test_string_ecologies_normalize_to_tuple`
- `test_string_populations_normalize_to_tuple`
- `test_string_relationships_normalize_to_tuple`
- `test_empty_ref_fields_normalize_to_empty_tuple`
- `test_dict_with_id_biome_normalizes_to_id_string`
- `test_dict_without_id_biome_raises_normalization_error`
- `test_duplicate_biome_ref_fails`

Also update `test_normalizer_v1_and_v2` to add `isinstance(..., tuple)` assertions.

AC mapped: "All existing real module tests pass", plus new normalizer AC tests

---

### Step 8 — Write new tests for `ContentReferenceGraph.add_module_edges`

Create `tests/unit/content/test_reference_graph.py` (or add to `test_content_usage_matrix.py` if that file already tests the graph).

Add:
- `test_add_module_edges_adds_biome_edges`
- `test_add_module_edges_adds_ecology_population_relationship_edges`
- `test_add_module_edges_uses_normalized_ids_not_raw_dicts`
- `test_graph_build_uses_add_module_edges`

AC mapped: "`add_module_edges` exists and uses normalized IDs"

---

### Step 9 — Run scoped test suite

```bash
pytest tests/unit/worldmodules/ tests/unit/content/test_reference_graph.py -q
pytest tests/unit/worldassembly/ tests/unit/content/ -q
```

All tests must pass. No slow tests required.

---

## Scope Guards (What NOT to Change)

- Do NOT change `WorldModuleSpec` (source authoring schema stays flexible with `List[str]`).
- Do NOT change `resource_refs`/`building_refs`/`service_refs` (already `Dict[str, int]` in `NormalizedWorldModule`).
- Do NOT change `resolver.py` field iteration — it already works with the new tuple type.
- Do NOT change the graph edge structure (same edge format `concept:id`).
- Do NOT change `requires`, `regions`, `population_recipes`, `resource_recipes`, `building_recipes`, `factions` handling in `_build_graph`.
- Do NOT add a parity ledger entry in this ticket — that is a post-implementation step.

---

## AC-to-Step Mapping

| Acceptance Criterion | Steps |
|---|---|
| `NormalizedWorldModule.biomes/ecologies/populations/relationships` are `Tuple[str, ...]` | 3 |
| Normalizer converts list-of-strings and list-of-dicts-with-id correctly | 2, 4 |
| Normalizer rejects dict-without-id with a clear error | 2, 4 |
| `ContentReferenceGraph.add_module_edges(NormalizedWorldModule)` exists | 5 |
| Graph building flow uses normalized module refs, not raw spec | 6 |
| All existing real module tests pass | 7, 9 |
| No graph code parses YAML comments or raw dict shapes | 6, 8 |

---

## Unresolved Questions

None. All types and behaviors have been decided from investigation.
