---
ticket_id: TCK-20260614-WORLDSCEN-PERSPECTIVES
phase: plan
date: 2026-06-15
---

# Plan: TCK-20260614-WORLDSCEN-PERSPECTIVES
## Wire WorldCompositionSpec.default_perspectives into CompileContext

---

## Scope Guards

- **READ ONLY — do not touch:**
  - `src/scenarios/resolver.py` (ScenarioSetupResolver) — already handles perspective allowlist correctly at scenario level; any modification would duplicate logic and violate out-of-scope boundary.
  - `src/worldassembly/validator.py` (WorldAssemblyValidator) — perspective enforcement belongs in `assemble()` via `ResolverError`, not in the validator (WORLD-ASM-009). Adding a validator check would create redundancy drift.
  - `src/worldmodules/` — perspectives are composition-level, not module-level. No module files are touched.
- **DO NOT:**
  - Store perspectives before `compile_context` is returned from `profile_resolver.resolve()` — the returned context is a fresh object; pre-call registration is lost (Risk 5 in investigation).
  - Import `PerspectiveDefinition` into `context.py` — use `Dict[str, Any]` to avoid a new `worldassembly.context → content.schema` coupling edge.
  - Add a second iteration over `default_perspectives` — resolve into a local dict first, register in one pass after `profile_resolver.resolve()` returns.

---

## Dependency Map

```
Step 1 (context.py)
  └── Step 2 (resolver.py __init__ + assemble) — needs perspectives field + register_perspective() to exist
        └── Step 3 (fix test_v2_module_resolution_and_heuristics) — must happen before Step 4 test run to avoid false failure
              └── Step 4 (new test file) — tests against the wired implementation
                    └── Step 5 (docs) — written after behaviour is verified green
                          └── Step 6 (parity ledger) — status: verified only after tests pass
```

Steps 5 and 6 have no code dependency on each other and can be done in either order after Step 4.

---

## AC → Step Mapping

| Acceptance Criterion | Step(s) |
|---|---|
| Composition with `default_perspectives: ["hero_guild_perspective"]` produces `CompileContext.perspectives` with that ID resolved | Steps 1, 2, 4 (Test 1) |
| Unknown perspective ID fails assembly with `ResolverError` naming the unknown ID | Steps 2, 4 (Test 2) |
| Empty `default_perspectives` assembles without error, `perspectives == {}` | Steps 1, 2, 4 (Test 3) |
| `dungeon_crawl.yaml` with `default_perspectives: ["hero_guild_perspective"]` assembles correctly | Steps 2, 4 (integration) |
| All existing integration tests pass | Steps 3, 4 (regression run) |

---

## Ordered Steps

### Step 1 — Extend `CompileContext` with perspectives field and register method

**File:** `src/worldassembly/context.py`

**Changes (all within the class body):**

1. In `__init__`, after `self.legacy_roles: Dict[str, EntityRole] = {}`, add:
   ```python
   self.perspectives: Dict[str, Any] = {}
   ```

2. After `register_legacy_role()`, add:
   ```python
   def register_perspective(self, perspective_id: str, resolved_def: Any) -> None:
       self.perspectives[perspective_id] = resolved_def
   ```
   - `resolved_def` is typed `Any` — the stored value is the raw `model_dump()` dict from `PerspectiveDefinition`, avoiding a coupling import.

3. In `to_dict()`, add a `"perspectives"` key after `"legacy_roles"`:
   ```python
   "perspectives": dict(self.perspectives),
   ```
   - `self.perspectives` already holds plain dicts (from `model_dump()`), so no further transformation is needed.

4. In `from_dict()`, add after the `legacy_roles` loop:
   ```python
   for k, v in data.get("perspectives", {}).items():
       ctx.perspectives[k] = v
   ```
   - Uses `.get("perspectives", {})` to tolerate contexts serialised before this ticket (backward compat — Risk 3 / Test 6).

**Verification:** The existing `test_compile_context_serialization` test must still pass — `perspectives` will be `{}` for that composition, and `from_dict` handles absent key gracefully.

---

### Step 2 — Wire perspective resolution into `WorldAssemblyResolver`

**File:** `src/worldassembly/resolver.py`

**2a — Import `SocialDefaultsResolver` at the top of the file.**

Extend the existing import block at lines 20–29:
```python
from src.content.resolver import (
    BiomeResolver,
    EcologyResolver,
    RegionResolver,
    ResourceResolver,
    BuildingResolver,
    RelationshipResolver,
    PopulationRecipeResolver,
    ResolverError,
    SocialDefaultsResolver,   # ← add this line
)
```

**2b — Instantiate `SocialDefaultsResolver` in `WorldAssemblyResolver.__init__`.**

At the end of `__init__` (after `self.population_recipe_resolver = PopulationRecipeResolver(catalog_repo)`, line ~210), add:
```python
self.social_resolver = SocialDefaultsResolver(catalog_repo)
```

**2c — Resolve perspectives in `assemble()`, after module merge loop and before `CompileProfileResolver.resolve()`.**

Insertion point: after the relationship provenance block ends (~line 553) and before the `# Ensure width and height` comment block (~line 555).

Insert:
```python
# Resolve perspectives declared in composition (WORLD-ASM-009: unknown ID raises ResolverError)
resolved_perspectives: Dict[str, Any] = {}
for persp_id in normalized_comp.default_perspectives:
    persp_def = self.social_resolver.resolve_perspective(persp_id)
    resolved_perspectives[persp_id] = persp_def.model_dump()
```

**2d — Register perspectives on the returned `compile_context`.**

After `compile_context = self.profile_resolver.resolve(world_spec, population_recipes_dict)` (line 639), add:
```python
for persp_id, persp_data in resolved_perspectives.items():
    compile_context.register_perspective(persp_id, persp_data)
```

**Why two passes are avoided:** perspectives are resolved into `resolved_perspectives` in one pass (step 2c), then registered onto the fresh `compile_context` after it is created (step 2d). No double-iteration over `default_perspectives`.

**Why insertion is after module merge loop:** `default_perspectives` is a composition-level field, not a module-level field. Per investigation §Mechanics (WORLD-ASM-008), perspective resolution belongs after the per-module loop and before `CompileProfileResolver.resolve()`.

**Why insertion is before `profile_resolver.resolve()`:** `compile_context` does not exist until `profile_resolver.resolve()` returns. Perspectives must be held in a local dict until then.

---

### Step 3 — Fix `test_v2_module_resolution_and_heuristics` (pre-existing test regression)

**File:** `tests/unit/worldassembly/test_assembly.py`, line 564

**Change:** The composition dict at that line contains `"default_perspectives": ["hero_view"]`. After Step 2, `assemble()` will raise `ResolverError("perspective", "hero_view")` because `"hero_view"` is not in the catalog.

**Resolution:** Change `"hero_view"` to `"hero_guild_perspective"` (a known catalog ID confirmed by `data/content/social/perspectives.yaml`).

Do not remove `default_perspectives` from the dict — the test also exercises heuristic assembly with real perspective data, and changing to a known ID is the minimal correct fix that keeps the test semantically representative.

Note: the same `"hero_view"` appears at line 494 and line 500 in a normalisation-only test (`test_composition_normalization_shorthand_and_mixed`) — those do NOT call `assemble()` and must NOT be changed. Only the instance at line 564 is in the assembly path.

---

### Step 4 — Write new unit test file

**File:** `tests/unit/worldassembly/test_perspective_resolution.py` (new file)

Implement all 7 tests from the test plan:

| Test | What it verifies |
|---|---|
| `test_known_perspective_resolves_into_compile_context` | Known ID → `compile_context.perspectives` has the key; `chosen_faction` matches catalog |
| `test_unknown_perspective_id_raises_resolver_error` | Unknown ID → `ResolverError` with ID in message |
| `test_empty_default_perspectives_produces_empty_dict` | No `default_perspectives` → `perspectives == {}`, no error |
| `test_multiple_perspectives_all_resolve` | Two IDs both land in `perspectives` with correct `chosen_faction` |
| `test_perspectives_survive_serialization_roundtrip` | `to_dict()` has `"perspectives"` key; `from_dict()` round-trips `chosen_faction` |
| `test_from_dict_tolerates_missing_perspectives_key` | Backward compat: raw dict without `"perspectives"` key → `ctx.perspectives == {}` |
| `test_register_perspective_stores_resolved_def` | Unit test of `register_perspective()` directly on a bare `CompileContext()` |

Fixtures required: `catalog_repo` (real loaded `CatalogRepository`) and `module_repo` (real loaded `WorldModuleRepository`). Reuse fixture patterns from `tests/unit/worldassembly/test_assembly.py` — do not create new fixture infrastructure.

Use a minimal valid composition with at least one enabled module (e.g., `plains_layout` + `standard_villagers`) to keep tests fast and non-slow-marked.

**Run after writing:**
```
pytest tests/unit/worldassembly/test_perspective_resolution.py -v
```

Then regression sweep:
```
pytest tests/unit/worldassembly/ tests/integration/worldassembly/ tests/integration/scenarios/ tests/unit/content/test_resolvers.py -v -m "not slow"
```

---

### Step 5 — Update assembly contract doc

**File:** `docs/world/assembly_contract.md`

In the WORLD-ASM-003 table (CompileContext fields), add a row:

| Field | Type | Populated by | Notes |
|---|---|---|---|
| `perspectives` | `Dict[str, Any]` | `WorldAssemblyResolver.assemble()` | Keyed by perspective ID; value is `model_dump()` of `PerspectiveDefinition`; empty `{}` when `default_perspectives` is absent |

No other sections in the doc require edits — WORLD-ASM-009 (failure contract) and WORLD-ASM-008 (resolution sequence) already cover the `ResolverError` and ordering constraints that apply here.

---

### Step 6 — Add parity ledger entry

**File:** `docs/parity_ledger/substrate.yaml`

Append after the last entry (currently `SUBSTRATE-NEW-003`):

```yaml
- id: SUBSTRATE-NEW-004
  text: >
    WorldAssemblyResolver.assemble() resolves each ID in
    WorldCompositionSpec.default_perspectives via SocialDefaultsResolver.resolve_perspective(),
    raises ResolverError on unknown IDs, and stores the model_dump() output in
    CompileContext.perspectives keyed by perspective ID.
    Empty default_perspectives produces an empty perspectives dict.
  status: verified
  priority: P1
  v2_evidence: >
    src/worldassembly/resolver.py (assemble(), perspective resolution block);
    src/worldassembly/context.py (perspectives field, register_perspective, to_dict, from_dict)
  test_path: tests/unit/worldassembly/test_perspective_resolution.py
  divergence_note: ""
```

Set `status: verified` only after Step 4 tests are confirmed green.

---

## Unresolved Questions

None. All catalog IDs, resolver locations, insertion points, and type decisions are confirmed by the investigation. The plan is fully executable.

---

## Quick Reference: Line Numbers (at time of planning)

| Location | Current line | What lives there |
|---|---|---|
| `resolver.py` import block | L20–29 | `from src.content.resolver import (...)` |
| `resolver.py` `__init__` last line | ~L210 | `self.population_recipe_resolver = PopulationRecipeResolver(catalog_repo)` |
| `resolver.py` end of module merge loop | ~L553 | Last relationship provenance block closes |
| `resolver.py` `CompileProfileResolver.resolve()` call | L639 | `compile_context = self.profile_resolver.resolve(...)` |
| `context.py` last field in `__init__` | L31 | `self.provenance: Optional[Any] = None` |
| `context.py` last `to_dict()` key | L65 | `"legacy_roles"` |
| `context.py` last `from_dict()` loop | L85–86 | `legacy_roles` loop |
| `test_assembly.py` problematic line | L564 | `"default_perspectives": ["hero_view"]` in assembly test |
