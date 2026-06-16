---
status: authoritative
layer: engine
authority: P1
audience: agent
last_verified: 2026-06-16
tags: [worldmodules, engine, contract, pipeline, normalization, topology]
---

# World Modules Contract

**Source:** `src/worldmodules/` (4 files: schema.py, normalizer.py, repository.py, utils.py)  
**Compliance namespace:** `WORLD-MOD-001` through `WORLD-MOD-007`  
**Authoritative status:** `WorldModuleSpec` objects are **preprocessing inputs** — they are consumed during world assembly to produce `AuthoritativeState`. The module specs themselves are not part of `AuthoritativeState` or the simulation hash.

Cross-links:
- Consumer: `docs/world/assembly_contract.md` — `WorldAssemblyResolver` consumes `NormalizedWorldModule` via `topological_sort_modules`
- Upstream content path: `docs/content/pipeline_contract.md` — `ContentPathConfig.world_modules_dir` governs discovery root

---

## Pipeline Position

```
data/world_modules/**/*.yaml
    ↓
WorldModuleRepository.load_all()          [repository.py — WORLD-MOD-004/005]
    ↓  (Pydantic validation per module; duplicate IDs fatal)
WorldModuleSpec (in-memory registry)
    ↓
WorldModuleAuthoringNormalizer.normalize()   [normalizer.py]
    ↓  (ref deduplication, count-map coercion, tuple freeze)
NormalizedWorldModule
    ↓
topological_sort_modules(modules_map)     [utils.py — WORLD-MOD-006/007]
    ↓  (Kahn's algorithm, alphabetical tie-breaking)
Ordered List[str] of module IDs
    ↓
WorldAssemblyResolver (see docs/world/assembly_contract.md)
```

---

## Schema Contract (schema.py — WORLD-MOD-001, WORLD-MOD-002, WORLD-MOD-003)

### `ModuleParameterSpec` (WORLD-MOD-003)

Frozen Pydantic model (`extra="forbid"`) defining a single configurable parameter exposed by a module.

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` (min_length=1) | yes | Parameter identifier |
| `type` | `str` | yes | Primitive type — must be one of: `string`, `integer`, `float`, `boolean`, `enum`, `id_reference` |
| `default` | `Optional[Any]` | no | Default value; if set, must be in `allowed_values` if `allowed_values` is also set |
| `required` | `bool` | no (default `False`) | Whether the parameter must be supplied |
| `allowed_values` | `Optional[List[Any]]` | no | Enumerated valid values |
| `min_value` | `Optional[Union[int, float]]` | no | Numeric lower bound |
| `max_value` | `Optional[Union[int, float]]` | no | Numeric upper bound |
| `description` | `Optional[str]` | no | Human-readable description |

**Validation rule:** If both `default` and `allowed_values` are set, `default` must appear in `allowed_values`. Violation raises `ValueError` at construction.

#### WORLD-MOD-003 — Parameter Expression Engine

`ModuleParameterEvaluator` (`src/worldmodules/evaluator.py`) enforces `ModuleParameterSpec` constraints at assembly time and evaluates template expressions in recipe count fields.

**Constraint enforcement order** (per parameter, per `ModuleParameterEvaluator.evaluate()`):
1. Merge: `{spec.name: spec.default}` for all specs, then `update(injected)`.
2. Required check: if `required=True` and resolved value is `None` → raise `AssemblyParameterError`.
3. `allowed_values` check: if value not in list → raise `AssemblyParameterError`.
4. `min_value` / `max_value` check (numeric values only): out-of-bounds → raise `AssemblyParameterError`.

**`AssemblyParameterError(ValueError)`** — carries `module_id` and `param_name` attributes; message format: `[{module_id}] param '{param_name}': {reason}`.

**Zero-param fast path:** Modules with `parameters: []` skip all evaluation overhead. `evaluate_field()` returns immediately when `isinstance(value, int)`.

**Recipe count field expression grammar** (implemented in `evaluate_field()`):

```
expression  := term (('+' | '-') term)*
term        := factor (('*' | '/') factor)*
factor      := NUMBER | '(' expression ')'
NUMBER      := integer or float literal (after {key} substitution)
```

**Expression evaluation rules:**
- Substitution phase: all `{key}` tokens are replaced with their resolved numeric string representation before AST parsing. An unresolved key raises `AssemblyParameterError`.
- AST safety phase: `ast.parse(expr, mode='eval')` followed by `ast.walk()` with explicit allow-list: `{ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.UAdd, ast.USub}`. Any other node type raises `ValueError("unsafe expression")`. `eval()` is never called on raw strings.
- Coercion: result is always `int` (truncation via `int(...)`, not rounding).
- Non-numeric substitution (e.g. a string-type param in arithmetic) raises `ValueError`.

**Count field types:** `PopulationRecipeSpec.count`, `ResourceRecipeSpec.count`, and `BuildingRecipeSpec.count` accept `Union[int, str]`. String values are parameter template expressions resolved at assembly time. Template YAML (`WorldTemplateSpec`) must always use integer literals — a non-integer count in template context raises `ValueError` at expansion time.

### `WorldModuleSpec` (WORLD-MOD-001, WORLD-MOD-002)

Frozen Pydantic model (`extra="forbid"`) representing a reusable structural world-building module.

**Schema Contract (WORLD-MOD-001):** Single unified format. `schema_version` is an optional human-readable label defaulting to `None`. It is not validated by the schema — any string value (or absence) is accepted. `module_type` is the enforced identity discriminator (see WORLD-MOD-002 below).

**Identity fields:**

| Field | Type | Default | Description |
|---|---|---|---|
| `schema_version` | `Optional[str]` | `None` | Optional human-readable label; not validated |
| `module_id` | `str` (min_length=1) | required | Unique module identifier |
| `module_type` | `str` | required | Functional type — validated against `REGISTERED_MODULE_TYPES` |
| `display_name` | `str` (min_length=1) | required | Human-readable name |
| `description` | `Optional[str]` | `None` | Optional description |
| `version` | `str` | `"1.0.0"` | Semver string |

**Dependency fields:**

| Field | Type | Description |
|---|---|---|
| `requires` | `List[str]` | Module IDs that must be processed before this module |
| `provides` | `List[str]` | Semantic aliases advertised by this module |
| `parameters` | `List[ModuleParameterSpec]` | Exposed configurable variables |

**Structural contribution fields:**

| Field | Type | Notes |
|---|---|---|
| `regions` | `List[RegionRecipeSpec]` | Region layout recipes |
| `population_recipes` | `List[PopulationRecipeSpec]` | Entity spawning recipes |
| `resource_recipes` | `List[ResourceRecipeSpec]` | Resource node recipes |
| `building_recipes` | `List[BuildingRecipeSpec]` | Building construct recipes |
| `observability_tags` | `List[str]` | Structural audit tags — used by `ModuleScorer` for danger dimension detection |
| `quest_definitions` | `List[QuestDefinition]` | Quest definitions contributed by this module; merged by `WorldAssemblyResolver` (see WORLD-ASM-011) |

**IMPORTANT:** `provided_features` is NOT a field on `WorldModuleSpec` — it belongs to `WorldCompositionSpec` only. `extra="forbid"` will reject any YAML key not in the schema above.

**Tag field note:** The tag field is `observability_tags`. There is no `tags` field on `WorldModuleSpec`.

**Catalog reference fields** (normalized to tuples/dicts by `WorldModuleAuthoringNormalizer`; available in all modules alongside recipe fields):

| Field | Normalized to | Description |
|---|---|---|
| `biomes` | `biome_refs: Tuple[str, ...]` | Biome layout template refs |
| `ecologies` | `ecology_refs: Tuple[str, ...]` | Ecology layout template refs |
| `populations` | `population_refs: Tuple[str, ...]` | Population template refs |
| `relationships` | `relationship_refs: Tuple[str, ...]` | Relationship layout refs |
| `resources` | `resources: Dict[str, int]` | Resource node count map |
| `buildings` | `buildings: Dict[str, int]` | Building count map |
| `services` | `services: Dict[str, int]` | Service count map |
| `factions` | (list passthrough) | Associated faction IDs |

**Registered module types:**

```python
REGISTERED_MODULE_TYPES = {
    "terrain", "settlement", "ecology",
    "economy", "conflict", "population", "danger_zone"
}
```

New types may be added at runtime via `WorldModuleSpec.register_module_type(type_str)`. This mutates the module-level set — use with caution in test isolation.

---

## Repository Contract (repository.py — WORLD-MOD-004, WORLD-MOD-005)

`WorldModuleRepository` discovers and loads `WorldModuleSpec` documents from a directory tree.

**Constructor:** `WorldModuleRepository(modules_dir=None)` — defaults to `ContentPathConfig().world_modules_dir` (`data/world_modules/` by default).

**`load_all()` — (WORLD-MOD-004)**

Recursively walks `modules_dir` with `os.walk`, reading all `.yaml` and `.yml` files. Missing directory is silently tolerated — `load_all()` returns without error.

**Per-file loading rules:**
- Empty/falsy YAML content is silently skipped.
- A file may contain a single dict or a list of dicts — both are supported.
- Any item missing `module_id` raises `ValueError`.
- Duplicate `module_id` across any loaded files raises `ValueError` (no override allowed).
- Pydantic schema validation failure raises `ValueError` with location and cause.

**Query operations (WORLD-MOD-005):**

| Method | Returns | Notes |
|---|---|---|
| `get_module(module_id)` | `Optional[WorldModuleSpec]` | `None` if not found |
| `list_modules()` | `List[WorldModuleSpec]` | All loaded modules |
| `list_modules_by_type(module_type)` | `List[WorldModuleSpec]` | Case-insensitive type match |
| `module_fingerprint(module_id)` | `Optional[str]` | SHA-256 of sorted raw dict items; `None` if not found |

**Fingerprint:** `SHA-256(str(sorted(raw_dict.items())))` — deterministic given identical YAML content. Used for provenance tracking in `WorldAssemblyResolver`.

---

## Normalizer Contract (normalizer.py)

`WorldModuleAuthoringNormalizer.normalize(spec: WorldModuleSpec) → NormalizedWorldModule`

Converts the flexible Pydantic `WorldModuleSpec` (which allows `Union[Dict, List]` for several fields) into a strictly-typed frozen dataclass suitable for downstream consumption. This is the **hand-off point** between authoring-time flexibility and assembly-time rigidity.

**`NormalizedWorldModule`** — frozen dataclass. Fields:

- Identity fields mirror `WorldModuleSpec` directly.
- Ref list fields (`biome_refs`, `ecology_refs`, `population_refs`, `relationship_refs`) are `Tuple[str, ...]` — immutable, deduplicated.
- Count map fields (`resources`, `buildings`, `services`) are `Dict[str, int]` with all counts ≥ 1.

**`NormalizationError(ValueError)`** — raised when:
- A ref list element is neither a string nor a dict with a valid `"id"` key.
- A duplicate ID is found in a ref list or count map.
- A count value is non-positive (≤ 0) or not an integer.

**Normalization rules:**

| Input shape | `_normalize_ref_list` output | `normalize_count_map` output |
|---|---|---|
| `List[str]` | `Tuple[str, ...]` (validated, no dups) | `{str: 1}` per item |
| `List[dict with 'id']` | `Tuple[str, ...]` (IDs extracted) | Key from `resource_type`/`building_type`/`service_type`/`id`; count from `count` field (default 1) |
| `Dict[str, int]` | n/a | Passthrough (all counts validated ≥ 1) |
| Duplicate ID | `NormalizationError` | `ValueError` |

---

## Topological Sort Contract (utils.py — WORLD-MOD-006, WORLD-MOD-007)

**`topological_sort_modules(modules_map: Dict[str, Any]) → List[str]`**

Sorts module IDs so that every module appears **after** all of its `requires` dependencies.

**Algorithm:** Kahn's topological sort with alphabetical tie-breaking at each round. The alphabetical sort is applied after each node is processed — ensuring that modules at the same dependency depth are always processed in lexicographic order regardless of insertion order.

**Cycle detection:** If the topological ordering cannot be completed (cycle in `requires` edges), raises `ValueError("Circular dependency detected in structural world module graph.")`.

**External requires:** A module may declare `requires` IDs that are not present in `modules_map`. These external references are silently ignored (no error). Only intra-map dependency edges participate in the sort.

**Determinism:** Given the same `modules_map` keys and `requires` relationships, `topological_sort_modules` always produces the same ordering. No randomness is introduced.

---

## Compliance ID Index

| ID | File | Description |
|---|---|---|
| WORLD-MOD-001 | src/worldmodules/schema.py | `WorldModuleSpec` unified schema and field contract |
| WORLD-MOD-002 | src/worldmodules/schema.py | `REGISTERED_MODULE_TYPES` and `module_type` validation |
| WORLD-MOD-003 | src/worldmodules/schema.py | `ModuleParameterSpec` schema and default/allowed_values cross-validation |
| WORLD-MOD-004 | src/worldmodules/repository.py | `WorldModuleRepository.load_all()` — discovery, deduplication, validation |
| WORLD-MOD-005 | src/worldmodules/repository.py | Query operations and `module_fingerprint` contract |
| WORLD-MOD-006 | src/worldmodules/utils.py | `topological_sort_modules` — Kahn's algorithm and cycle detection |
| WORLD-MOD-007 | src/worldmodules/utils.py | Determinism guarantee and alphabetical tie-breaking rule |
