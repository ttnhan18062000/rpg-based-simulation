---
ticket_id: TCK-20260614-WORLDSCEN-PERSPECTIVES
phase: investigation
date: 2026-06-15
---

# Investigation: TCK-20260614-WORLDSCEN-PERSPECTIVES
## Wire WorldCompositionSpec.default_perspectives into CompileContext

---

## Current Behavior

### CompileContext fields (src/worldassembly/context.py — WORLD-ASM-003)

`CompileContext.__init__` initialises these dicts/fields:

| Field | Type | Notes |
|---|---|---|
| `entities` | `Dict[str, ResolvedEntityProfile]` | populated by `CompileProfileResolver.resolve()` |
| `buildings` | `Dict[str, ResolvedBuildingProfile]` | same |
| `resources` | `Dict[str, ResolvedResourceProfile]` | same |
| `factions` | `Dict[str, ResolvedFactionEconomyProfile]` | same |
| `region_ownership` | `Dict[str, Faction]` | populated inline |
| `legacy_factions` | `Dict[str, Faction]` | populated inline |
| `legacy_roles` | `Dict[str, EntityRole]` | populated inline |
| `provenance` | `Optional[Any]` | set via `set_provenance()` |

**There is NO `perspectives` field and NO `register_perspective()` method.**

`to_dict()` serialises all fields above. `from_dict()` deserialises them. Neither mentions perspectives.

### WorldCompositionSpec.default_perspectives (src/worldassembly/schema.py — WORLD-ASM-006)

Field **exists**:
```python
default_perspectives: List[str] = Field(default_factory=list, description="Default perspective IDs")
```

Also present on `NormalizedWorldComposition` (L138). `WorldCompositionNormalizer.normalize()` passes it through correctly (verified by `test_composition_normalization_shorthand_and_mixed` and `test_real_composition_normalization_preserves_perspectives`).

### PerspectiveDefinition (src/content/schema.py L185)

**Exists.** Schema:
```python
class PerspectiveDefinition(CatalogBaseDefinition):
    chosen_faction: str
    default_focus: str
    projected_labels: Dict[str, List[str]]
```

### CatalogRepository perspective support (src/content/repository.py)

Fully wired:
- `self.perspectives: Dict[str, PerspectiveDefinition] = {}` (L185)
- Loaded from `data/content/social/perspectives.yaml` via `ContentFamilySpec("social.perspectives", ...)` (L109)
- `get_perspective(def_id)` method (L431-432)
- Included in catalog summary dict (L496, L536)

Catalog data file `data/content/social/perspectives.yaml` contains:
- `hero_guild_perspective`
- `wild_beast_pack_perspective`
- `goblin_warband_perspective`
- `merchant_league_perspective`

### PerspectiveDefinition resolver (src/content/resolver.py — SocialDefaultsResolver)

**Exists** at `SocialDefaultsResolver.resolve_perspective(perspective_id: str)` (L329-334):
```python
def resolve_perspective(self, perspective_id: str) -> PerspectiveDefinition:
    record = self._repo.get_perspective(perspective_id)
    if record is None:
        raise ResolverError("perspective", perspective_id)
    return record
```

`SocialDefaultsResolver` is already imported as `PerspectiveDefinition` is already imported from `src.content.schema` (L32 in resolver.py). The class is in the same file.

### WorldAssemblyResolver.assemble() — gap

`WorldAssemblyResolver.__init__` does NOT instantiate a `SocialDefaultsResolver`. The `assemble()` method does NOT:
- Read `normalized_comp.default_perspectives`
- Call any perspective resolver
- Store resolved perspectives anywhere

At line 639, `CompileProfileResolver.resolve()` is called to produce the `compile_context`. `CompileProfileResolver` also does not touch perspectives.

### ScenarioSetupResolver (src/scenarios/resolver.py — READ ONLY)

`_validate_perspective()` (L75-85) uses `composition.default_perspectives` as an allowlist: if it is non-empty and `scenario.perspective` is not in it, it raises `ValueError`. This guard runs **before** `_assembly_resolver.assemble()` is called (L47-48). The resolved `ResolvedScenarioSetup` carries `perspective_id: str` (L28) — it does NOT need `CompileContext.perspectives`. `ScenarioSetupResolver` will not be modified.

---

## Gap Analysis

| Gap | Severity | Description |
|---|---|---|
| `CompileContext` has no `perspectives` field | **Blocking** | `default_perspectives` declared in composition is silently dropped after assembly |
| `WorldAssemblyResolver.assemble()` never reads `normalized_comp.default_perspectives` | **Blocking** | Perspectives are never resolved or validated against catalog |
| No `register_perspective()` method on `CompileContext` | **Blocking** | No authoritative write path for perspectives into context |
| `to_dict()` / `from_dict()` do not include `perspectives` | **Medium** | Serialisation roundtrip will silently lose perspectives; affects CLI `handle_resolve` path |
| Assembly contract doc (WORLD-ASM-003 table) does not list `perspectives` | Documentation | Must be updated after implementation |

**What is NOT a gap:**
- `PerspectiveDefinition` schema — exists
- `CatalogRepository.get_perspective()` — exists
- `SocialDefaultsResolver.resolve_perspective()` — exists
- `WorldCompositionSpec.default_perspectives` field — exists and survives normalisation
- `ScenarioSetupResolver` perspective allowlist guard — already works correctly

---

## Mechanics / Engine Constraints

- **WORLD-ASM-009 (failure contract):** Any `ResolverError` during resolution aborts assembly — no silent skips. Unknown perspective IDs must raise `ResolverError`, consistent with how unknown regions, factions, roles, and biomes are handled.
- **WORLD-ASM-003 (CompileContext contract):** CompileContext is not frozen — the resolver populates it incrementally. After resolution it must not be modified.
- **WORLD-ASM-008 (resolution sequence):** Perspective resolution belongs **after** the per-module merge loop and **before** `CompileProfileResolver.resolve()` is called (line 639 in resolver.py). This is the cleanest insertion point: all catalog-level context is available, no module-level data is needed for perspectives (they are composition-level, not module-level).
- **Docs/mechanics/06_worldbuilding_foundation.md** — compositions declare topology and sovereignty. Perspectives are a composition-level declaration, not a module-level one. Wiring them during assembly (not per-module) is consistent with this.
- **Empty `default_perspectives`** → empty `CompileContext.perspectives` — no error. This is the zero-conflict default path.

---

## Parity Overlap

No existing `substrate.yaml` entry covers `CompileContext.perspectives`. The nearest entries are:

- `SUBSTRATE-NEW-001` — covers the two compilation paths (composition→CompileContext via WorldAssembly) but does not mention perspectives.
- `SUBSTRATE-NEW-003` — covers WorldModuleAssemblyResolver.assemble() improvements; not perspective-related.

**A new parity entry is required** in `docs/parity_ledger/substrate.yaml` after implementation. Suggested ID: `SUBSTRATE-NEW-004`.

The assembly contract doc (`docs/world/assembly_contract.md` — WORLD-ASM-003 table) must be updated to add the `perspectives` row.

---

## Key Changes Required

### 1. `src/worldassembly/context.py`

- Add `self.perspectives: Dict[str, PerspectiveDefinition] = {}` to `__init__` (import `PerspectiveDefinition` from `src.content.schema`, or keep type as `Dict[str, Any]` to avoid coupling — see Risk 1 below).
- Add `register_perspective(self, perspective_id: str, resolved_def: PerspectiveDefinition) -> None` method.
- Add `"perspectives"` key to `to_dict()` — serialise as `{id: def.model_dump()}`.
- Add perspectives deserialisation in `from_dict()` — reconstruct `PerspectiveDefinition` instances from dict.

**Recommended typing:** Use `Dict[str, Any]` in the field and store raw `model_dump()` output, OR import `PerspectiveDefinition` directly. Direct import is cleaner and consistent with how `ResolvedEntityProfile` etc. are imported. The existing `models.py` pattern (typed resolved profiles) should be followed.

### 2. `src/worldassembly/resolver.py` — `WorldAssemblyResolver`

In `__init__`:
- Instantiate `SocialDefaultsResolver(catalog_repo)` and store as `self.social_resolver`.

In `assemble()`, after the module merge loop (after line 553) and before `CompileProfileResolver.resolve()` (line 639):
```python
# Resolve perspectives declared in composition
for persp_id in normalized_comp.default_perspectives:
    self.social_resolver.resolve_perspective(persp_id)  # raises ResolverError if unknown
    # perspective stored in compile_context after profile_resolver.resolve() call below
```

Then after `compile_context = self.profile_resolver.resolve(...)`, iterate `normalized_comp.default_perspectives` again and call `compile_context.register_perspective(persp_id, resolved_def)`.

**Or simpler:** resolve all perspectives into a local dict first, then register them onto the returned `compile_context` in one pass. This avoids double-iteration.

### 3. Import additions in `resolver.py`

Add `SocialDefaultsResolver` to the import from `src.content.resolver`.

### 4. `docs/world/assembly_contract.md`

Add `perspectives` row to the WORLD-ASM-003 table. Update the compliance ID list.

### 5. New parity ledger entry in `docs/parity_ledger/substrate.yaml`

Add `SUBSTRATE-NEW-004` covering perspective wiring.

---

## Risks

### Risk 1 — Coupling direction: `context.py` importing `content/schema.py`
`CompileContext` currently only imports from `src.worldassembly.models` and `src.core.enums`. Adding an import of `PerspectiveDefinition` from `src.content.schema` introduces a new dependency edge: `worldassembly.context → content.schema`. The existing imports in `resolver.py` already include `content.resolver` (line 20-29), so the module-level coupling already exists. Typing `perspectives` as `Dict[str, Any]` avoids the coupling in `context.py` at the cost of losing static type safety. **Recommendation:** use `Dict[str, Any]` in the `perspectives` field of `CompileContext` and keep the typed `PerspectiveDefinition` only in resolver.py where it is already imported.

### Risk 2 — `to_dict()` / `from_dict()` round-trip for perspectives
`PerspectiveDefinition.projected_labels` is a `Dict[str, List[str]]` — fully JSON-serialisable. `model_dump()` will produce a plain dict. `from_dict()` needs to reconstruct either a plain dict or a `PerspectiveDefinition` from it. If stored as `Dict[str, Any]` in `CompileContext`, `from_dict()` can simply copy the raw dict back in without importing `PerspectiveDefinition`. This is the recommended approach.

### Risk 3 — `test_compile_context_serialization` regression
The existing `test_compile_context_serialization` test verifies that `to_dict()` and `from_dict()` produce lossless round-trips. Adding `perspectives` to `to_dict()` and `from_dict()` must not break this test. The test uses a composition without `default_perspectives`, so `perspectives` will be `{}` — the round-trip test will still pass as long as `from_dict()` handles the absent `"perspectives"` key with `.get("perspectives", {})`.

### Risk 4 — `WorldAssemblyValidator` does not validate perspectives
The existing `WorldAssemblyValidator.validate()` does composition validation (module refs) but has no perspective check. A separate `ResolverError` path in `assemble()` is the correct enforcement point (consistent with WORLD-ASM-009). No change to `WorldAssemblyValidator` is needed.

### Risk 5 — Order of operations in `assemble()`
`compile_context` is created by `self.profile_resolver.resolve(world_spec, population_recipes_dict)` at line 639. `CompileProfileResolver.resolve()` returns a fresh `CompileContext` — perspectives must be registered on the returned context **after** this call, not before. Any pre-call registration would be lost.

---

## Anti-Drift Hazards

1. **Do not add perspectives to `WorldAssemblyValidator`** — validation is already handled by the `ResolverError` path in `assemble()` (WORLD-ASM-009). Adding a second check creates redundancy and drift risk.
2. **Do not modify `ScenarioSetupResolver`** — it already uses `composition.default_perspectives` correctly as an allowlist. The ticket scope explicitly excludes it (Out of Scope section).
3. **Do not resolve perspectives per-module** — `default_perspectives` is a composition-level field, not a module-level field. Perspective resolution must happen after the module merge loop, not inside it.
4. **Do not validate `SimulationScenarioDefinition.perspective` against `CompileContext.perspectives`** — that belongs in `ScenarioSetupResolver` (already done via `_validate_perspective`) and is explicitly out of scope.
5. **`to_dict()` key must be `"perspectives"`** (not `"default_perspectives"`) — `to_dict()` uses simplified keys (e.g., `"entities"` not `"resolved_entities"`). Consistency requires the single-word form.
