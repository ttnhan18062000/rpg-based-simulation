# Investigation — TCK-20260607-ARCHETYPE-METADATA-EXPLICIT

## Current Behavior

### PopulationSpec — definition

File: `src/worldbuilding/schema.py` lines 51–58

```python
class PopulationSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., min_length=1, description="Unique population category identifier")
    count: int = Field(..., ge=0, description="Initial count of entities in this population group")
    role: str = Field(..., min_length=1, description="Combat or societal role of the entities")
    faction: str = Field(..., min_length=1, description="Faction affiliation")
    spawn_region: str = Field(..., min_length=1, description="Region where entities are spawned")
```

`PopulationSpec` has **no `archetype_id` field**. It carries role and faction as plain strings (copied from the resolved archetype), but has no typed reference back to which archetype originated it.

### PopulationSpec — construction sites (code-constructed, not YAML-authored)

`PopulationSpec` is **never deserialized directly from YAML by authors**. Every `PopulationSpec` instance observed in the codebase is constructed programmatically:

1. `src/worldassembly/resolver.py:755` — `resolve_module_contribution` (v2 populations path):
   ```python
   pop_key = f"{p_id}_{resolved_arch.archetype_id}"  # line 754
   resolved_population_specs.append(PopulationSpec(
       id=f"{prefix}{pop_key}",
       count=count,
       role=resolved_arch.role_id,
       faction=resolved_arch.faction_id,
       spawn_region=spawn_region
   ))
   ```
   The archetype identity is **encoded into the `id` string** as a suffix: `{population_recipe_id}_{archetype_id}`. The archetype_id is never stored as a separate field.

2. `src/worldassembly/resolver.py:89` — validator dummy spec (line 89): same pattern with `id=f"pop_{idx}"`.

3. `src/worldassembly/resolver.py:407–413` — v1 population recipes path: uses raw `pop_id` strings prefixed with module prefix, no archetype at all.

### Case 2 logic in PopulationRecipeResolver

File: `src/content/resolver.py` lines 577–584

```python
recipe = self._repo.get_population_recipe(population_id)
if recipe is None:
    # Case 2: shorthand — treat population_id as a direct archetype ID (count=1, no regions).
    archetype = self._repo.get_entity_archetype(population_id)
    if archetype is not None:
        resolved_arch = self._archetype_resolver.resolve(population_id)
        return [(resolved_arch, 1)], []
    raise ResolverError("population_recipe", population_id)
```

Case 2 is **already correct and already validates** the archetype ID before returning. The ticket description references "stripping a generated suffix" — this inference does **not** occur in `PopulationRecipeResolver.resolve()`. Instead, the suffix-stripping inference occurs in two other locations downstream.

### String-suffix inference sites (the actual fragile code)

**Site 1 — Provenance determination in `WorldAssemblyResolver._merge_module_contributions`:**
File: `src/worldassembly/resolver.py` lines 334–341

```python
# Attempt to determine archetype_id and population_recipe_id for provenance
archetype_id = None
pop_recipe_id = None
for pr in contribution.population_refs:
    if pr in pop.id:
        pop_recipe_id = pr
        archetype_id = pop.id.split(pr + "_")[-1]   # ← fragile string split
        break
```

This splits `pop.id` (e.g., `"goblin_camp_conflict_goblin_raiding_party_goblin_raider"`) on `pr + "_"` to extract the archetype ID suffix. If the population recipe ID or archetype ID format changes, this silently produces a wrong or empty `archetype_id`.

**Site 2 — CompileProfileResolver archetype lookup in `_build_compile_context`:**
File: `src/worldassembly/resolver.py` lines 901–908

```python
archetype_id = None
if "_" in key:
    # E.g., goblin_camp_conflict_goblin_raiding_party_goblin_raider
    # Let's extract the part after the population recipe if it matches an archetype ID
    for arch_key in self.repo.entity_archetypes:
        if key.endswith(f"_{arch_key}"):
            archetype_id = arch_key
            break
```

This iterates every archetype in the catalog and checks if the `PopulationSpec.id` key ends with `_{arch_key}`. This is an O(archetypes × entities) scan on every population entity, dependent on the generated ID format baked in at line 754.

### Option A vs Option B determination

`PopulationSpec` is **always constructed in code** (never deserialized from YAML author content). The archetype_id is an assembly-time artifact. This conclusively selects **Option B**: add `archetype_id` as an explicit field on `PopulationSpec` (or on a companion frozen dataclass `ExpandedPopulationMember`). Option A (YAML-authored field) is not applicable.

The cleanest execution of Option B is to add `archetype_id: Optional[str] = None` to `PopulationSpec`. This is the minimal, backward-compatible change: existing construction sites that do not pass `archetype_id` continue to work; the two inference sites in `WorldAssemblyResolver` are replaced with direct field reads. The ticket also mentions a new `ExpandedPopulationMember` dataclass as an alternative, but that would require changing `PopulationRecipeResolver`'s return type, which ripples into `resolve_module_contribution` and existing tests.

---

## Mechanics / Engine Constraints

- `PopulationSpec` is a frozen Pydantic model (`model_config = ConfigDict(frozen=True)`). Adding an optional field requires no migration of existing instances provided it has a default (`None`).
- `PopulationSpec` appears in `WorldSpec.entities` (list). `WorldSpec` is YAML-deserialized from authored world specs (`src/worldbuilding/schema.py`). If `archetype_id` is added, YAML-authored `WorldSpec` files must not be required to supply it (field must remain `Optional[str] = None`).
- Engine Contracts (`docs/engine/authoritative_pipeline.md`): entity identity must be stable and typed; no meaning encoded in free-form strings.
- Mechanics Bible (`docs/mechanics/01_entity_anatomy.md`): entity identity is the archetype definition, not a derived label.

---

## Parity Ledger Overlap

| Entry ID | File | Current Status | Relevance |
|---|---|---|---|
| TOWN-170 | `docs/parity_ledger/town_resource.yaml` | `verified` | Directly documents `PopulationRecipeResolver` three-case contract (Case 2 shorthand). Its `v2_evidence` references `PopulationRecipeResolver.resolve()` — this entry will need a note that `archetype_id` is now carried explicitly in the returned `ResolvedEntityArchetype`, not inferred downstream. No status change required if Case 2 logic in `resolver.py` is unchanged; update `v2_evidence` to reference the explicit field. |

No entries in `substrate.yaml` or `infrastructure.yaml` directly reference `PopulationSpec.archetype_id` or the suffix-splitting logic.

---

## Prior Work

| Ticket | Status | Relevance |
|---|---|---|
| TCK-20260604-PHASE25-ARCHETYPE-POPULATION-RESOLVER | DONE | Introduced `PopulationRecipeResolver`, `EntityArchetypeResolver`, `ResolvedEntityArchetype`. Established the `pop_key = f"{p_id}_{resolved_arch.archetype_id}"` construction that is the root of the fragile inference. |
| TCK-20260606-PHASE25-METADATA | DONE | Added `archetype_id`, `race_id`, `role_id`, etc. to `ResolvedEntityProfile`. Introduced Site 2 inference (`key.endswith(f"_{arch_key}")`). Introduced Site 1 inference (`pop.id.split(pr + "_")[-1]`). This is the direct origin of the fragile code this ticket repairs. |
| TCK-20260607-POPULATION-RECIPE-FALLBACK | DONE | Documented and validated Case 2 in `PopulationRecipeResolver.resolve()`. Added parity ledger entry TOWN-170. The Case 2 path is now correct; the fragile inference is *downstream* of this in `WorldAssemblyResolver`. |
| TCK-20260419-MD-TASK3-HARDEN-FALLBACK-AND-BOUNDS | DONE | Earlier fallback hardening work — confirms the fallback pattern was a known risk area. |
| TCK-20260421-P6-M2-T2-RPG-CORE-POPULATION | DONE | Early population model work; no direct overlap with current schema. |

---

## Risks and Open Questions

### Decided: Option B (add `archetype_id: Optional[str]` to `PopulationSpec`)

`PopulationSpec` is code-constructed, never YAML-authored by world module authors. Adding `Optional[str] = None` is backward-compatible. The two inference sites are replaced with direct field reads.

### Open Question 1 — `WorldSpec` YAML deserialization safety

`WorldSpec` in `src/worldbuilding/schema.py` contains `entities: List[PopulationSpec]`. Hand-authored `WorldSpec` YAML files (if any exist under `data/`) do not supply `archetype_id`. The field must remain `Optional[str] = None` with no `extra="forbid"` restriction on this field alone. Verify no `WorldSpec` YAML uses `extra="forbid"` that would reject the new field. Current `PopulationSpec` model config is `frozen=True` only — no `extra="forbid"` — so this is safe.

### Open Question 2 — `PopulationRecipeResolver` return type

The ticket proposes `ExpandedPopulationMember` as an alternative. If Option B is taken (field on `PopulationSpec`), `PopulationRecipeResolver.resolve()` returns `List[Tuple[ResolvedEntityArchetype, int]]` — archetype_id is already accessible as `resolved_arch.archetype_id`. The resolver return type does NOT need to change. The explicit `archetype_id` is populated at `resolve_module_contribution` line 755 when constructing `PopulationSpec`.

### Open Question 3 — Collision safety of suffix inference (Site 1)

Site 1 at line 340 uses `pop.id.split(pr + "_")[-1]`. If the population recipe ID appears multiple times in the full prefixed pop.id string (e.g., a module prefix contains the recipe ID substring), `split` returns more than 2 parts and `[-1]` gives the last fragment, which may be wrong. This is a real correctness hazard that disappears when `archetype_id` is an explicit field.

### Open Question 4 — Site 2 O(N) scan performance

Site 2 iterates all archetypes per entity. With large catalogs this degrades quadratically. Replacing with a direct field read eliminates the scan entirely.

---

## Anti-Drift Hazards

1. **`resolve_module_contribution` line 754 — `pop_key` format**: If this format string ever changes (e.g., separator changes from `_` to `.`), Site 1 and Site 2 break silently. After this ticket, the format string is only used for ID uniqueness; archetype identity is carried by the explicit field.

2. **`PopulationSpec` frozen model**: Adding a new field must maintain `frozen=True`. Do not remove `frozen=True`.

3. **`WorldSpec` YAML files**: After adding the field, world spec YAML files authored by humans must not be required to supply it. Pydantic will default to `None`. No doc update needed unless YAML authoring docs explicitly enumerate `PopulationSpec` fields.

4. **TOWN-170 parity entry**: Its `test_path` points to `test_case2_direct_archetype_id_returns_single_entity`. This test must continue to pass unchanged (Case 2 logic in `PopulationRecipeResolver` is not being changed).

5. **`ResolvedModuleContribution.resolved_population_specs`**: Declared as `List[PopulationSpec]` in `src/worldassembly/schema.py:117`. When `PopulationSpec` gains `archetype_id`, this field carries it automatically — no schema change needed in `ResolvedModuleContribution`.
