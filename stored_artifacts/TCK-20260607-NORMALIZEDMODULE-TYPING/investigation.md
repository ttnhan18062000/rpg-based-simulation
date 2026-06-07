# Investigation — TCK-20260607-NORMALIZEDMODULE-TYPING

## Current Behavior (file:line)

### `src/worldmodules/normalizer.py`

**Lines 14–36 — `NormalizedWorldModule` dataclass**
Four fields are declared as `List[Any]`:
```python
biomes: List[Any]        # line 29
ecologies: List[Any]     # line 30
populations: List[Any]   # line 31
relationships: List[Any] # line 32
```
`NormalizedWorldModule` is a `@dataclass(frozen=True)`.

**Lines 113–115 — `WorldModuleAuthoringNormalizer.normalize()`**
The four fields are populated with bare `list(spec.X)` — no type coercion, no validation:
```python
biomes=list(spec.biomes),
ecologies=list(spec.ecologies),
populations=list(spec.populations),
relationships=list(spec.relationships),
```

### `src/worldmodules/schema.py`

**Lines 74–77 — `WorldModuleSpec` v2 layout fields**
The source schema already declares these as `List[str]`:
```python
biomes: List[str] = Field(default_factory=list, ...)
ecologies: List[str] = Field(default_factory=list, ...)
populations: List[str] = Field(default_factory=list, ...)
relationships: List[str] = Field(default_factory=list, ...)
```
This means `WorldModuleSpec` already enforces string-only elements via Pydantic validation. The `List[Any]` in `NormalizedWorldModule` is a downstream typing gap — the data is already strings when it arrives, but the type contract does not say so.

**Key finding:** No real YAML module file uses `dict`-with-id format for biomes/ecologies/populations/relationships. All seven real YAML files under `data/content/world_modules/` use plain string lists (e.g., `biomes: ["frontier_village"]`). Because `WorldModuleSpec` validates these fields as `List[str]` at parse time, by the time `normalize()` is called the values are already `List[str]`. The dict-with-id normalizer branch described in the ticket scope is therefore a defensive/future-proofing addition, not a refactor of an existing runtime path.

### `src/content/reference_graph.py`

**Lines 289–298 — `_build_graph`, V2 layout loop (uses raw `WorldModuleSpec`)**
```python
for biome in module.biomes:
    self.add_edge(module_node, f"biome:{biome}")
for ecology in module.ecologies:
    self.add_edge(module_node, f"ecology:{ecology}")
for population in module.populations:
    self.add_edge(module_node, f"population:{population}")
for relationship in module.relationships:
    self.add_edge(module_node, f"faction_relationship:{relationship}")
```
`ContentReferenceGraph.__init__` accepts `modules: Optional[List[WorldModuleSpec]]` (line 166). It receives raw `WorldModuleSpec` objects, iterates the fields assuming they contain strings, and treats them as IDs directly — without normalization guarantees. This is the Fix 2 target: add `add_module_edges(NormalizedWorldModule)` and use it instead of this inline iteration, so graph edges are built from normalization-validated ID tuples.

### `src/worldassembly/resolver.py`

**Line 10 — import:** `from src.worldmodules.normalizer import NormalizedWorldModule`

**Lines 652–654 — `resolve_module_contribution()` signature:**
```python
def resolve_module_contribution(
    self,
    module: WorldModuleSpec | NormalizedWorldModule,
    ...
```
At call site (line 286), `module` is always a `NormalizedWorldModule` (produced by `WorldModuleAuthoringNormalizer.normalize()` on line 233). The `WorldModuleSpec` alternative in the union is vestigial.

**Lines 693–722 — downstream consumption of the four fields:**
The resolver iterates `module.biomes`, `.ecologies`, `.relationships`, `.populations` with plain `for x_id in module.X:` loops, treating each element as a string ID passed to the catalog resolvers. This is consistent with `Tuple[str, ...]` — no change needed here. The resolver is **not** a risk surface for this refactor.

---

## What Types Should Replace List[Any] for Each Field

| Field | Source type (WorldModuleSpec) | Target type (NormalizedWorldModule) | Reason |
|---|---|---|---|
| `biomes` | `List[str]` | `Tuple[str, ...]` | Immutable ref sequence; IDs only; no ordering semantics |
| `ecologies` | `List[str]` | `Tuple[str, ...]` | Same |
| `populations` | `List[str]` | `Tuple[str, ...]` | Same |
| `relationships` | `List[str]` | `Tuple[str, ...]` | Same |

`Tuple[str, ...]` is correct because:
1. `NormalizedWorldModule` is `frozen=True` — a `list` field in a frozen dataclass is mutable internally; a tuple is structurally immutable.
2. These fields are pure ID ref sequences (catalog references), not ordered collections with append semantics.
3. All call sites (`resolver.py` lines 693–722, `reference_graph.py` lines 289–298) only iterate — no `.append()`, no index mutation.

---

## Mechanics/Engine Constraints

Not applicable. This is an internal typing refactor of a pre-assembly normalization dataclass. No simulation laws, formulas, or tick behavior are involved.

---

## Parity Ledger Overlap

Scanned `docs/parity_ledger/substrate.yaml` (3771 entries, lines 1–2210 reviewed). No entry references `NormalizedWorldModule`, the normalizer, or these four fields. The parity ledger covers world generation determinism, snapshot immutability, entity builder, serialization, navigation, combat, and subsystem lifecycle — none of which touch module normalization typing.

**Conclusion:** No existing parity ledger entries are affected. A new entry should be added to `substrate.yaml` to track the typing contract for these four fields.

---

## Prior Work

- **TCK-20260604-PHASE22-SCHEMA-NORMALIZATION (DONE):** Created `WorldModuleAuthoringNormalizer` and `NormalizedWorldModule` in `normalizer.py`. Left the four fields as `List[Any]` — this ticket is the direct follow-on.
- **TCK-20260604-PHASE23-REFERENCE-GRAPH (DONE):** Implemented `ContentReferenceGraph` in `reference_graph.py`. Built the graph from raw `WorldModuleSpec` inline. The `add_module_edges` method called for in Fix 2 does not yet exist.
- **TCK-20260529-OBS-PHASE22-BEHAVIOR-NORMALIZATION (DONE):** Earlier normalization work, superseded by Phase 22.

No open tickets cover this same scope. No conflict with companion ticket TCK-20260607-RESOLVER-BOUNDARY (which addresses the typed input boundary of the resolver, not the normalizer output contract).

---

## Risks and Open Questions

1. **Existing test at line 97 (`test_normalizer_v1_and_v2`):** Uses `len(normalized_v1.biomes) == 0` and `normalized_v2.biomes[0] == "biome_v2"`. After the change to `Tuple[str, ...]`, `len()` still works on tuples. Index access `[0]` works on tuples. The test will pass without modification, but asserting `isinstance(normalized.biomes, tuple)` should be added.

2. **Dict-with-id format:** The ticket requests the normalizer also handle `List[dict]` with `id` key. However, `WorldModuleSpec.biomes/ecologies/populations/relationships` are all typed `List[str]` — Pydantic will reject a dict element at parse time before `normalize()` is ever called. This means the dict-with-id branch in the normalizer is defensive infrastructure for a future authoring path where `WorldModuleSpec` is loosened. It is safe to add but will not be exercised by real data. The test that validates dict-without-id raises `NormalizationError` is therefore testing the normalizer's standalone API contract, not a real runtime path.

3. **`add_module_edges` and the reference graph:** `ContentReferenceGraph.__init__` receives `List[WorldModuleSpec]`, not `List[NormalizedWorldModule]`. After adding `add_module_edges(NormalizedWorldModule)`, the graph build path must normalize each spec before calling the method. This touches `_build_graph` and/or the caller that constructs `ContentReferenceGraph`. The existing inline iteration in `_build_graph` (lines 289–298) must be replaced by `add_module_edges`.

4. **`NormalizationError`:** The normalizer does not currently define a custom exception. The ticket requires raising `NormalizationError` for dict-without-id inputs. This class must be defined (or imported from an existing errors module). Check whether `src/worldmodules/` has an errors module.

---

## Anti-Drift Hazards

- `test_normalizer_v1_and_v2` checks `normalized_v2.biomes[0] == "biome_v2"` — passes on tuple, but add an explicit `isinstance(..., tuple)` assertion to lock the contract.
- `reference_graph.py` `_build_graph` iterates `module.biomes` etc. as strings — after this ticket's Fix 2, that loop is replaced by `add_module_edges`. If someone re-adds the inline loop later, edges will be double-counted. The new method must be the single source.
- `NormalizedWorldModule` is `frozen=True`. Changing `List[Any]` to `Tuple[str, ...]` is structurally consistent; no `replace()` pattern needs updating.
