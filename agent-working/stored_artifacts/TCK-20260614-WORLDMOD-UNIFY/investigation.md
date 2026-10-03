---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260614-WORLDMOD-UNIFY
artifact_type: investigation
tags: [worldmodules, schema, unify, normalizer, resolver]
---

# Investigation — TCK-20260614-WORLDMOD-UNIFY

## Current Behavior

### `src/worldmodules/schema.py` — WorldModuleSpec (L48–L99)

`WorldModuleSpec` is a frozen Pydantic model (`extra="forbid"`) with a required
`schema_version` field (L52) validated at L83–88 to be either `"worldmodule.v1"`
or `"worldmodule.v2"`:

```python
@field_validator("schema_version")
@classmethod
def validate_schema_version(cls, v: str) -> str:
    if v not in ("worldmodule.v1", "worldmodule.v2"):
        raise ValueError("schema_version must be 'worldmodule.v1' or 'worldmodule.v2'")
    return v
```

Despite the v1/v2 split in the validator, **all structural contribution fields for both
versions are present in a single class** (L67–82). The v1 fields (`regions`,
`population_recipes`, `resource_recipes`, `building_recipes`) and v2 fields (`biomes`,
`ecologies`, `populations`, `relationships`, `resources`, `buildings`, `services`,
`factions`) coexist. Every field defaults to an empty list. This means the schema
already effectively supports both shapes — the `schema_version` validator is the only
enforced separation.

All 10 real modules in `data/content/world_modules/` carry `schema_version: "worldmodule.v1"`,
but they use fields from both groups:
- `frontier_village_core.yaml` uses `biomes`, `ecologies`, `populations`, `buildings`
  (all v2-named fields) with no `population_recipes`/`resource_recipes`.
- `forest_warden_grove.yaml` uses `biomes`, `ecologies`, `populations`, `resources`,
  `relationships` — again all nominally v2 fields.
- `goblin_camp_conflict.yaml` uses `biomes`, `ecologies`, `populations`, `relationships`.

In other words, **real data is already the unified format** — the schema_version field
is a nominal label, not a behavioral gate at the schema layer.

### `src/worldmodules/normalizer.py` — WorldModuleAuthoringNormalizer (L129–156)

`WorldModuleAuthoringNormalizer.normalize()` has **no branching on `schema_version`**.
It unconditionally normalizes all fields (v1 recipe lists and v2 ref lists) from any
`WorldModuleSpec`. The resulting `NormalizedWorldModule` dataclass (L18–41) carries
`schema_version: str` as a passthrough field.

Key finding: the normalizer is already version-agnostic in its field handling. The only
downstream effect of `schema_version` being stored in `NormalizedWorldModule` is
consumed in the resolver.

### `src/worldassembly/resolver.py` — assemble() (L212–650)

Two explicit `schema_version` checks gate v2-specific behavior in `assemble()`:

1. **L456–481**: v2 resource merge loop
   ```python
   if spec.schema_version == "worldmodule.v2":
       module_regions = [r for r in regions.values() if entity_origins.get(r.id) == m_id]
       for res_idx, (res_type, count) in enumerate(contribution.resource_refs.items()):
           ...
           spawn_region = self._find_best_region_for_resource(res_type, module_regions)
   ```

2. **L508–533**: v2 building merge loop
   ```python
   if spec.schema_version == "worldmodule.v2":
       module_regions = [r for r in regions.values() if entity_origins.get(r.id) == m_id]
       for bld_idx, (bld_type, count) in enumerate(contribution.building_refs.items()):
           for b_sub in range(count):
               ...
               spawn_region = self._find_best_region_for_building(bld_type, module_regions)
   ```

Since no real module has `schema_version == "worldmodule.v2"`, **these branches are
dead code at runtime** — they have never executed against real data.

### `resolve_module_contribution()` (L652–794) — no branching except one

One `schema_version` check at L678–679:
```python
if normalized_module.schema_version == "worldmodule.v2":
    raise ResolverError("region", reg.id, ...)
```
This enforces stricter catalog validation for v2 regions. For v1, a region not in the
catalog is silently accepted. All other resolver logic (biome, ecology, relationship,
service, population, resource, building steps) is already unified — no branching.

### `_find_best_region_for_resource()` (L796–816) — heuristic

This method performs string-matching on region IDs and types against `preferred_biomes`
from the catalog resource definition. Fallback is `module_regions[0].id`. The matching
logic (L806–813) uses substring checks (`if pb in reg.id or pb in reg.type`) which are
non-deterministic order-dependent heuristics not governed by any catalog resolver.

`_find_best_region_for_building()` (L818–840) similarly uses substring checks on
`building_themes` from the catalog, and biome theme lookup via `catalog_repo.get_biome()`.

Both are only called from the dead v2 branches in `assemble()`. `BiomeResolver` and
`EcologyResolver` are already instantiated on `self` (L204–205) but not used for
region assignment in these methods.

### `test_real_module_normalized_snapshot.py` (L94)

Line 94 asserts `normalized_frontier.schema_version is not None` — this will need
updating when `schema_version` is removed from `NormalizedWorldModule`.

### Summary of v1/v2 split locations

| File | Line(s) | Type |
|---|---|---|
| `src/worldmodules/schema.py` | L52, L83–88 | Field declaration + validator |
| `src/worldmodules/normalizer.py` | L22 (`schema_version: str`) | Passthrough field in dataclass |
| `src/worldassembly/resolver.py` | L456, L508 | Dead runtime branches in `assemble()` |
| `src/worldassembly/resolver.py` | L678–679 | Stricter catalog check for v2 regions |
| `tests/integration/worldassembly/test_real_module_normalized_snapshot.py` | L94 | `schema_version is not None` assertion |

---

## Mechanics / Engine Constraints

- `docs/mechanics/06_worldbuilding_foundation.md` governs declarative topology. Module
  fields map to `RegionRecipeSpec`, `PopulationRecipeSpec`, `ResourceRecipeSpec`,
  `BuildingRecipeSpec` — all from `src/worldbuilding/recipe.py`. The unified format
  must continue to produce identical typed recipe objects downstream.
- `docs/engine/kernel.md`: world assembly is preprocessing — not part of the
  deterministic tick loop. No determinism hazard from removing `schema_version` gating,
  but `NormalizedWorldModule` fields must remain deterministically ordered for
  provenance fingerprinting (the fingerprint is computed from the raw YAML dict, not
  from the normalized form — so fingerprint is unaffected).
- `docs/world/assembly_contract.md` (WORLD-ASM-008): resolution sequence requires
  biomes → ecologies → regions → resources → buildings → populations. The unified
  `resolve_module_contribution()` already follows this order (L671–793). No reordering
  needed.
- `docs/world/modules_contract.md` (WORLD-MOD-001, WORLD-MOD-002): currently documents
  `schema_version` as required, with v2-only catalog ref fields. Both sections must be
  updated to reflect a single format.

---

## Parity Ledger Overlap

Relevant entries in `docs/parity_ledger/substrate.yaml`:

| Entry ID | Text | Status | Relevance |
|---|---|---|---|
| **SUBSTRATE-NEW-003** | WorldModuleAuthoringNormalizer produces NormalizedWorldModule: ref lists → Tuple[str,...], count maps → Dict[str,int] | `verified` P1 | Must update `v2_evidence` to remove schema_version references; normalizer behavior unchanged |
| **SUB-367** | v2 service_refs computed in resolve_module_contribution() but not assembled into WorldSpec | `divergent` P2 | Unaffected — service gap remains; no change required |

No other substrate entries directly reference `schema_version`, `worldmodule.v1`, or
`worldmodule.v2`. The dead v2 resource/building branches in `assemble()` are not
covered by any parity entry — their removal introduces no parity obligation.

`docs/world/modules_contract.md` is an authoritative doc. Updating it requires a
`make knowledge-index-update` run afterward.

---

## Prior Work

| Ticket | Relevance |
|---|---|
| TCK-20260605-PHASE27-WORLD-MODULE-COMPOSITION | Introduced `ResolvedModuleContribution`, `BiomeResolver`, `EcologyResolver`, `PopulationRecipeResolver` — all the resolvers this ticket will use for deterministic resolution |
| TCK-20260612-WORLDMODULES-CONTRACT | Wrote `docs/world/modules_contract.md` — will require update in this ticket |
| TCK-20260608-NORMALIZED-MODULE-REFS | Prior normalization work; investigation available in stored_artifacts |
| TCK-20260604-PHASE22-SCHEMA-NORMALIZATION | Phase 22 schema normalization; established `normalize_count_map` and `_normalize_ref_list` helpers |

`stored_artifacts/TCK-20260605-PHASE27-WORLD-MODULE-COMPOSITION/investigation.md`
contains only a stub ("Let's investigate...") — the actual findings are embedded in the
code that was produced.

---

## Key Changes Required

### 1. `src/worldmodules/schema.py`

**Remove** `@field_validator("schema_version")` (L83–88) and its decorator.

**Change** the `schema_version` field declaration from required to optional with a
fixed default:
```python
# Before:
schema_version: str = Field(..., description="Module spec schema, 'worldmodule.v1' or 'worldmodule.v2'")

# After (backward-compat: existing YAMLs that declare schema_version still load cleanly):
schema_version: str = Field("worldmodule.v1", description="Module schema identifier (unified format)")
```

This preserves backward compatibility for the 10 existing YAML files that declare
`schema_version: "worldmodule.v1"` — they will continue to load without changes.
Any YAML omitting the field will default to `"worldmodule.v1"`.

**Remove** the compliance comment referencing WORLD-MOD-002 from schema_version, since
WORLD-MOD-002 covers `REGISTERED_MODULE_TYPES` (module_type validation) — that remains
unchanged.

No other field changes needed: the v2 fields (`biomes`, `ecologies`, etc.) are already
present and default to empty.

### 2. `src/worldmodules/normalizer.py`

**Remove** `schema_version: str` from the `NormalizedWorldModule` dataclass (L22).
Nothing in the assembly pipeline uses `normalized_module.schema_version` for branching
logic after this ticket — the only callers (resolver.py L456, L508, L678) will be
updated.

`WorldModuleAuthoringNormalizer.normalize()` (L133–156): remove the
`schema_version=spec.schema_version` assignment in the `NormalizedWorldModule(...)` call.

The normalize function itself already handles all fields uniformly — no logic changes
required beyond removing the passthrough field.

### 3. `src/worldassembly/resolver.py`

**Remove** the v2-gated resource merge block (L456–481):
```python
# DELETE: lines 456–481
if spec.schema_version == "worldmodule.v2":
    module_regions = [r for r in regions.values() if entity_origins.get(r.id) == m_id]
    for res_idx, (res_type, count) in enumerate(contribution.resource_refs.items()):
        ...
```

**Remove** the v2-gated building merge block (L508–533):
```python
# DELETE: lines 508–533
if spec.schema_version == "worldmodule.v2":
    module_regions = [r for r in regions.values() if entity_origins.get(r.id) == m_id]
    for bld_idx, (bld_type, count) in enumerate(contribution.building_refs.items()):
        ...
```

**Replace** the v2 region strictness check in `resolve_module_contribution()` (L678–679):
```python
# Before:
if normalized_module.schema_version == "worldmodule.v2":
    raise ResolverError("region", reg.id, ...)

# After: always raise for any module referencing a non-catalog region
raise ResolverError("region", reg.id,
    f"referenced by module '{normalized_module.module_id}' but not found in catalog")
```
This is safe: existing modules either reference catalog regions or omit the catalog
check entirely (the `if self.catalog_repo.get_region(reg.id) is not None:` outer guard
at L675 still applies).

**Remove** `_find_best_region_for_resource()` (L796–816) — it becomes dead code once
the v2 resource merge block is deleted. No caller remains.

Keep `_find_best_region_for_building()` (L818–840) **only if** the v2 building merge
block replacement needs it. Since we are removing that block too, **also remove**
`_find_best_region_for_building()`.

> NOTE on resource/building dict assembly: `contribution.resource_refs` and
> `contribution.building_refs` are Dict[str, int] produced by `resolve_module_contribution()`.
> They are currently only consumed in the dead v2 branches. After those branches are
> removed, these dicts are computed but never used in `assemble()`. Two options:
>
> Option A (minimal): Remove the dead branches; `resource_refs` / `building_refs` remain
> computed in `resolve_module_contribution()` but unused in `assemble()` (parallel to
> the existing service_refs gap documented in SUB-367).
>
> Option B (complete): Wire `contribution.resource_refs` and `contribution.building_refs`
> into `assemble()` as the **unified** resource and building merge path, replacing the
> separate v1 loops that currently iterate `spec.resource_recipes` and
> `spec.building_recipes` directly. This is the correct architectural outcome: all
> modules using the count-map fields (`resources:`, `buildings:`) would go through the
> same assembled path.
>
> **Recommendation: Option B.** The 10 real modules use `resources: {key: count}` /
> `buildings: {key: count}` (count-map format), not `resource_recipes:` /
> `building_recipes:`. Their assembly currently goes through the v2 branches which are
> gated off. Under Option A they remain unassembled. Under Option B they assemble
> correctly. The region-assignment logic from `_find_best_region_for_resource()` must
> be replaced — use `""` (empty) as spawn_region for count-map resources, consistent
> with how the catalog resolver path works.
>
> Confirm with ticket scope: AC states "Remove `_find_best_region_for_resource()`
> replaced by deterministic catalog resolver call." The deterministic replacement is to
> use `self.resource_resolver.resolve(res_type)` for validation and assign
> `spawn_region=""` (no heuristic) or the first module region if one exists. Produce
> the `ResourceNodeSpec` directly from the count map.

### 4. `docs/world/modules_contract.md`

- Remove the `schema_version` row from the identity fields table.
- Collapse the "v2-only catalog reference fields" section header — rename to "Catalog
  reference fields (all formats)".
- Update WORLD-MOD-001 and WORLD-MOD-002 compliance ID descriptions accordingly.
- Remove all "v1"/"v2" format labels from field descriptions.
- Update the "Schema Contract" section to state: single unified format; `schema_version`
  is an optional human-readable label defaulting to `"worldmodule.v1"`.

### 5. `docs/parity_ledger/substrate.yaml`

- **SUBSTRATE-NEW-003**: Update `v2_evidence` to remove references to schema_version
  branching. Update `text` to state "WorldModuleAuthoringNormalizer produces
  NormalizedWorldModule with a single unified code path — no schema_version branching".
  Keep `status: verified`.

---

## Risks and Open Questions

### Risk 1: Count-map resource/building assembly gap (Option A vs B)
If Option A is chosen (remove dead branches without wiring count-map assembly), all 10
real modules' `resources:` and `buildings:` dicts will be validated (via
`resolve_module_contribution`) but produce no `ResourceNodeSpec` / `BuildingSpec` in
the assembled `WorldSpec`. This is the current state anyway (v2 branches never execute),
but it would be an unaddressed gap.

**Mitigation**: Choose Option B. Wire the unified resource and building merge loops from
`contribution.resource_refs` / `contribution.building_refs` in `assemble()` after the
v1 recipe loops, unconditionally — not gated on any version field.

### Risk 2: `schema_version` retention in `NormalizedWorldModule`
If downstream code (outside the resolver) reads `normalized_module.schema_version` for
logging or fingerprinting, removing it from the dataclass will break that code. Current
search confirms only the resolver uses it (3 locations, all being removed). The
`module_fingerprint()` is computed from the raw YAML dict — unaffected.

**Mitigation**: Before removing the field, `grep -r "schema_version"` across all of
`src/` and `tests/` to confirm no other consumer.

### Risk 3: Test assertion on `schema_version`
`test_real_module_normalized_snapshot.py:L94` asserts
`normalized_frontier.schema_version is not None`. If `schema_version` is removed from
`NormalizedWorldModule`, this test will fail with `AttributeError`.

**Mitigation**: Update the test to remove that specific assertion, or replace it with
a check on `normalized_frontier.module_type`.

### Risk 4: `extra="forbid"` in WorldModuleSpec
Existing YAML files declare `schema_version: "worldmodule.v1"`. Changing `schema_version`
to `Optional[str]` or defaulting it means these files will still load correctly since
the field continues to exist. No risk here — the field is retained as optional.

### Risk 5: `WorldAssemblyValidator` creates dummy WorldSpec (resolver.py:L78–100)
The validator builds a dummy `WorldSpec` from `module.regions`, `module.population_recipes`,
`module.resource_recipes`, `module.building_recipes`. After Option B, assembled resources
and buildings come from the count-map path, not from `spec.resource_recipes` /
`spec.building_recipes`. The validator's dummy WorldSpec still iterates
`module.resource_recipes` (v1 recipe lists), which will be empty for all real modules.
This is pre-existing behavior — the validator already sees empty recipe lists for the
real modules.

### Open Question 1
Should `schema_version` be completely removed from `NormalizedWorldModule`, or kept as
a cosmetic passthrough? AC says "Remove `@field_validator('schema_version')`" — the
field may remain on `WorldModuleSpec` as optional, but the NormalizedWorldModule
dataclass does not need it.

### Open Question 2
After removing `_find_best_region_for_resource()`, what is the correct region assignment
for count-map resources? The ticket AC says "replaced by deterministic catalog resolver
call." The deterministic approach is: validate the resource type via
`self.resource_resolver.resolve(res_type)` (already done in the v2 branch), assign
`spawn_region=""` (let world-level placement handle it), and only set an explicit region
if the module declares exactly one region (use its ID). This avoids the heuristic
substring matching.

---

## Anti-Drift Hazards

1. **The `assemble()` v2 service comment (L535–539)** references
   `spec.schema_version == "worldmodule.v2"` in its rationale. After removing v2
   branching, update the comment to reference only `SUB-367` and
   `v2_intentional_divergences.md` entry 2.19 — no schema_version mention.

2. **`NormalizedWorldModule.schema_version` passthrough**: If the field is kept in
   `NormalizedWorldModule` but the validator is removed from `WorldModuleSpec`, any
   YAML with `schema_version: "worldmodule.v3"` would silently load. Removing the field
   entirely from `NormalizedWorldModule` is cleaner.

3. **`docs/world/modules_contract.md` WORLD-MOD-002** currently describes
   `schema_version` validation as part of its scope. After this ticket, WORLD-MOD-002
   should describe only `REGISTERED_MODULE_TYPES` validation. Do not lose the
   `module_type` validation coverage in the updated doc.

4. **`test_real_module_normalized_snapshot.py:L94`** asserts `schema_version is not None`.
   This test will become an anti-drift guard after the field is removed from the
   dataclass — it will fail at attribute access, not just value. Must be updated.

5. **Count-map fields (`resources`, `buildings`) in the real YAML** are the primary
   way real modules declare resources and buildings. The v1 `resource_recipes` /
   `building_recipes` lists are empty in all 10 real modules. If only the v1 paths are
   kept in `assemble()` and the count-map path is not wired, these modules will produce
   no resources or buildings in the assembled WorldSpec — a silent correctness gap with
   no error. Tests must explicitly verify non-zero resource and building counts for
   modules that declare them.
