# Remaining Repair Plan — After Full Source Review

## Goal

Finish the remaining cleanup after the Phase 20–28 repair so the implementation is safer for future AI-agent work.

Current state is already solid enough to continue, but it still has these confirmed weak points:

```text
1. RuntimeContentMode is too coarse: only MIGRATION and V2.
2. Adapter reporting only exposes heuristic_count.
3. Normalized module v2 refs are typed but still named like raw fields.
4. Reward classification is centralized but still EntityRole-based.
5. Reward trace coverage is incomplete.
6. Normalized module snapshot test is too synthetic.
```

The full source confirms `RuntimeContentMode` currently has only `MIGRATION` and `V2`, and tests assert exactly two modes.
The adapter result currently exposes only `heuristic_count`, not detailed heuristic records.
The combat reward service tests still call `CombatRewardClassificationService.classify(EntityRole.MONSTER/HERO)`, so reward classification is centralized but still legacy-role based.

---

# Scope

This repair plan covers:

```text
- runtime content mode clarity
- detailed adapter heuristic reporting
- normalized module field naming
- real-module normalized snapshot proof
- combat reward classification API cleanup
- reward trace coverage
```

---

# Non-goals

This repair plan does **not** cover:

```text
- removing all legacy fallback logic
- rewriting combat resolution
- changing EntityState structure broadly
- implementing Phase 29+
- parsing YAML comments
- adding new content packs
```

YAML comments like `# STATE: ...` remain human planning notes only.

---

# Phase summary table

| Phase | Goal                                                      |    Priority | Main output                                                                      |
| ----- | --------------------------------------------------------- | ----------: | -------------------------------------------------------------------------------- |
| R1    | Replace vague runtime modes                               |        High | `CATALOG_STRICT`, `CATALOG_WITH_COMPATIBILITY`, `LEGACY_FALLBACK`, `TEST_MANUAL` |
| R2    | Replace `heuristic_count` with detailed heuristic records |        High | `AdapterHeuristicUsage` list                                                     |
| R3    | Rename normalized v2 module fields to `*_refs`            |      Medium | clearer normalized module contract                                               |
| R4    | Add real-module normalized snapshot test                  |      Medium | realistic contribution snapshot                                                  |
| R5    | Upgrade combat reward classification API                  | Medium-high | `classify_defeated_target(attacker, defender, state)`                            |
| R6    | Add reward trace tests                                    |      Medium | trace proof for single/multi/skill paths                                         |

---

# Phase R1 — Replace vague `RuntimeContentMode`

## Phase goal

Make runtime content mode explicit enough to prevent future confusion between clean catalog mode, compatibility mode, legacy fallback, and manual test mode.

## Current issue

Current implementation has only:

```python
RuntimeContentMode.MIGRATION
RuntimeContentMode.V2
```

and tests assert `len(RuntimeContentMode) == 2`.

This is too vague because `V2` can mean:

```text
strict catalog?
catalog with compatibility?
no heuristics?
some heuristics?
```

That ambiguity is dangerous for future AI-agent work.

---

## Task R1.1 — Introduce explicit runtime modes

### Objective

Replace the two-mode enum with a more precise enum.

### Expected behavior

Use:

```python
class RuntimeContentMode(Enum):
    CATALOG_STRICT = "catalog_strict"
    CATALOG_WITH_COMPATIBILITY = "catalog_with_compatibility"
    LEGACY_FALLBACK = "legacy_fallback"
    TEST_MANUAL = "test_manual"
```

Migration mapping:

```text
old V2        → CATALOG_STRICT
old MIGRATION → CATALOG_WITH_COMPATIBILITY
legacy None   → LEGACY_FALLBACK
manual tests  → TEST_MANUAL
```

### Technical direction

Update:

```text
src.core.registries
adapter constructors
seed_phase1_content()
registry parity tests
runtime content mode tests
```

### Test plan

Update/add:

```text
tests/unit/content/test_runtime_content_mode.py
```

Test cases:

```text
- RuntimeContentMode has four explicit modes.
- CATALOG_STRICT rejects heuristic-only projection.
- CATALOG_WITH_COMPATIBILITY allows compatibility projection but reports heuristics.
- LEGACY_FALLBACK allows hardcoded fallback.
- TEST_MANUAL does not require catalog.
```

### Acceptance checklist

- [ ] `RuntimeContentMode.MIGRATION` is removed or kept only as deprecated alias.
- [ ] `RuntimeContentMode.V2` is removed or kept only as deprecated alias.
- [ ] Strict catalog mode has no heuristic fallback.
- [ ] Compatibility mode reports heuristic usage.
- [ ] Legacy fallback mode is explicit.
- [ ] Existing registry parity tests are updated to use explicit modes.

### Anti-drift notes

- Do not use another boolean flag like `migration_mode=True`.
- Do not make `CATALOG_STRICT` silently behave like compatibility mode.
- Do not delete legacy fallback yet.

---

# Phase R2 — Replace `heuristic_count` with detailed heuristic records

## Phase goal

Make adapter heuristic behavior traceable by record, family, adapter, and reason.

## Current issue

Current adapter result only returns:

```python
heuristic_count: int
```

inside `AdapterProjectionResult`.

This is not enough. If the count is `5`, we do not know:

```text
which records used heuristics
which adapter used heuristics
which fields were inferred
whether this is allowed in the selected runtime mode
```

---

## Task R2.1 — Add `AdapterHeuristicUsage`

### Objective

Replace anonymous count reporting with structured heuristic records.

### Expected behavior

Add:

```python
@dataclass(frozen=True)
class AdapterHeuristicUsage:
    record_id: str
    family: str
    adapter: str
    heuristic_type: str
    reason: str
    mode: RuntimeContentMode
```

Then update:

```python
@dataclass(frozen=True)
class AdapterProjectionResult:
    mode: RuntimeContentMode
    item_count: int
    service_count: int
    resource_count: int
    heuristic_usages: tuple[AdapterHeuristicUsage, ...]
```

Optional compatibility property:

```python
@property
def heuristic_count(self) -> int:
    return len(self.heuristic_usages)
```

### Technical direction

Track heuristic usage in:

```text
CatalogToItemRegistryAdapter
CatalogToServiceRegistryAdapter
CatalogToResourceRegistryAdapter
ArchetypeToEnemyRegistryAdapter if fallback/projection heuristic occurs
```

Examples:

```text
item.use_kind inferred from categories
item.class_fit inferred from item ID
resource.required_tool defaulted
resource.base_difficulty defaulted
service default generated
fallback enemy added
```

### Test plan

Add:

```text
tests/unit/content/test_adapter_heuristic_reporting.py
```

Test cases:

```text
- item adapter records use_kind heuristic with record_id.
- item adapter records class_fit heuristic with record_id.
- resource adapter records required_tool/default difficulty heuristic.
- service adapter records generated service heuristic.
- strict mode fails if heuristic_usages is non-empty.
- compatibility mode returns heuristic_usages.
```

### Acceptance checklist

- [ ] `AdapterProjectionResult` exposes detailed heuristic usages.
- [ ] `heuristic_count` is derived, not source truth.
- [ ] Every heuristic has record ID.
- [ ] Every heuristic has adapter name.
- [ ] Every heuristic has reason.
- [ ] Strict mode rejects heuristic usages.
- [ ] Compatibility mode reports heuristic usages.

### Anti-drift notes

- Do not hide heuristic details in logs only.
- Do not keep only aggregate count.
- Do not treat heuristic projection as clean strict behavior.

---

## Task R2.2 — Split strict and compatibility registry parity tests

### Objective

Prevent registry parity tests from proving only compatibility behavior.

### Current issue

The current tests seed with `RuntimeContentMode.MIGRATION` and assert aggregate `heuristic_count`.

### Expected behavior

Separate tests:

```text
catalog_strict parity
catalog_with_compatibility parity
legacy_fallback seeding
```

### Test plan

Update:

```text
tests/integration/content/test_registry_projection_parity.py
```

Cases:

```text
- strict mode has zero heuristic_usages.
- strict mode projects explicit catalog fields only.
- compatibility mode may have heuristic_usages but reports them.
- legacy fallback seeds hardcoded records only when selected.
```

### Acceptance checklist

- [ ] Strict parity test exists.
- [ ] Compatibility parity test exists.
- [ ] Legacy fallback test exists.
- [ ] Strict mode does not accept heuristic projection.
- [ ] Compatibility mode asserts heuristic details, not only count.

---

# Phase R3 — Rename normalized v2 module fields to `*_refs`

## Phase goal

Make normalized module data clearly different from raw authoring data.

## Current issue

The full source shows normalized v2 refs are typed better now, but still named:

```python
biomes
ecologies
populations
relationships
```

The normalizer converts values through `_normalize_ref_list`, but the names still look like raw authoring fields.

The reference graph tests also build `NormalizedWorldModule` with fields named `biomes`, `ecologies`, `populations`, and `relationships`.

---

## Task R3.1 — Rename normalized fields

### Objective

Make normalized model explicit.

### Expected behavior

Change:

```python
biomes
ecologies
populations
relationships
```

to:

```python
biome_refs
ecology_refs
population_refs
relationship_refs
```

Keep existing count maps:

```python
resources: dict[str, int]
buildings: dict[str, int]
services: dict[str, int]
```

or optionally rename later to:

```python
resource_refs
building_refs
service_refs
```

### Technical direction

Update:

```text
NormalizedWorldModule
WorldModuleAuthoringNormalizer
WorldAssemblyResolver
ContentReferenceGraph
tests/unit/content/test_reference_graph.py
tests/unit/worldmodules/test_modules.py
tests/integration/worldassembly/*
```

Temporary compatibility properties can be added:

```python
@property
def biomes(self) -> tuple[str, ...]:
    return self.biome_refs
```

but new code should use `*_refs`.

### Test plan

Add/update tests:

```text
- normalized module exposes biome_refs.
- old biomes property is compatibility-only or removed.
- graph uses biome_refs/ecology_refs/population_refs/relationship_refs.
- resolver uses population_refs instead of raw populations.
```

### Acceptance checklist

- [ ] `NormalizedWorldModule` has `biome_refs`.
- [ ] `NormalizedWorldModule` has `ecology_refs`.
- [ ] `NormalizedWorldModule` has `population_refs`.
- [ ] `NormalizedWorldModule` has `relationship_refs`.
- [ ] Graph consumes normalized ref fields.
- [ ] Resolver consumes normalized ref fields.
- [ ] Raw authoring fields do not leak into resolver logic.

### Anti-drift notes

- Do not keep both naming systems indefinitely.
- Do not make resolver inspect raw dict/list authoring fields.
- Do not weaken the normalizer.

---

# Phase R4 — Add real-module normalized snapshot proof

## Phase goal

Prove normalized module shape using real content, not only a synthetic empty module.

## Current issue

The current snapshot/boundary proof is useful, but the normalized contribution snapshot is synthetic. The reference graph tests use synthetic helper modules too.

That is acceptable for unit tests, but the repair plan needs one realistic normalized snapshot.

---

## Task R4.1 — Add real module normalized snapshot test

### Objective

Use real YAML from `data/content/world_modules`.

### Expected behavior

For a real module, assert normalized shape:

```text
module_id
module_type
biome_refs
ecology_refs
population_refs
relationship_refs
resources/buildings/services count maps
```

Recommended modules:

```text
frontier_village_core
old_mine_resource_loop
goblin_camp_conflict
```

### Test plan

Add:

```text
tests/integration/worldassembly/test_real_module_normalized_snapshot.py
```

Test flow:

```text
WorldModuleRepository()
→ load_all()
→ get_module("frontier_village_core")
→ WorldModuleAuthoringNormalizer.normalize()
→ assert normalized snapshot
```

### Acceptance checklist

- [ ] Test uses real `data/content/world_modules`.
- [ ] Test asserts typed ref fields.
- [ ] Test asserts count maps.
- [ ] Test asserts no raw dicts remain in normalized refs.
- [ ] Test does not manually inject module objects.

### Anti-drift notes

- Do not snapshot the entire YAML file.
- Do not create a synthetic module for this test.
- Keep snapshot focused on normalized contract.

---

# Phase R5 — Upgrade combat reward classification API

## Phase goal

Move reward classification from role-only compatibility toward clean identity/relation-aware classification.

## Current issue

The service exists, but it still classifies only by `EntityRole`:

```python
CombatRewardClassificationService.classify(EntityRole.MONSTER)
CombatRewardClassificationService.classify(EntityRole.HERO)
```

The tests confirm this role-only API.

The combat code still passes `defender.identity.role` into the service.

This is better than scattered enum checks, but not clean-data aware yet.

---

## Task R5.1 — Add `classify_defeated_target()`

### Objective

Introduce a new API that can later use clean identity and relation projection.

### Expected behavior

Add:

```python
class CombatRewardClassificationService:
    @staticmethod
    def classify_defeated_target(
        attacker: EntityState,
        defender: EntityState,
        state: AuthoritativeState,
    ) -> RewardClassification:
        ...
```

Resolution order:

```text
1. clean identity / relation projection if available
2. compatibility mapping
3. legacy EntityRole fallback
```

For this repair, clean path can be minimal:

```text
- if relation projection says enemy/threat → hostile_creature
- if defender role HERO → hero_actor through legacy fallback
- if defender role MONSTER → hostile_creature through legacy fallback
- neutral role → none
```

### Technical direction

Keep old API as compatibility wrapper:

```python
classify(entity_role: EntityRole)
```

but internal combat code should move to:

```python
classify_defeated_target(attacker, defender, state)
```

### Affected components

```text
src.engine.combat_rewards
src.engine.combat
tests/unit/combat/test_combat_rewards.py
tests/unit/combat/test_direct_combat_outcomes.py
```

### Test plan

Add tests:

```text
- legacy monster defender classifies as MONSTER_KILL.
- legacy hero defender classifies as HERO_KILL.
- clean hostile relation classifies as hostile creature.
- neutral merchant/citizen gives RewardCategory.NONE.
- old classify(EntityRole) still works as compatibility wrapper.
```

### Acceptance checklist

- [ ] `classify_defeated_target()` exists.
- [ ] Combat resolution uses `classify_defeated_target()`.
- [ ] Old `classify(EntityRole)` remains for compatibility tests.
- [ ] Legacy reward numbers do not change.
- [ ] Clean identity/relation path has at least one test.
- [ ] Neutral targets do not produce monster rewards.

### Anti-drift notes

- Do not rewrite reward math.
- Do not remove rebirth/permadeath behavior.
- Do not remove legacy role fallback.
- Do not require full relation migration everywhere.

---

# Phase R6 — Add reward trace coverage

## Phase goal

Make reward classification source observable and testable across combat paths.

## Current issue

`resolve_attack()` writes `trace["REWARD_SOURCE"] = classification.source`.

But `resolve_skill_usage()` calculates classification and reward without clearly returning a trace with `REWARD_SOURCE`.

Existing skill reward tests only check XP/intents, not reward source trace.

---

## Task R6.1 — Add reward source trace to all reward paths

### Objective

Ensure all reward-producing combat paths include classification source.

### Expected behavior

Every reward-producing `CombatUpdate.trace` should include:

```text
REWARD_CATEGORY
REWARD_SOURCE
```

Examples:

```text
MONSTER_KILL / legacy_role
HERO_KILL / legacy_role
MONSTER_KILL / relation_projection
NONE / clean_identity
```

### Technical direction

Update:

```text
resolve_attack
resolve_skill_usage
multi-attack reward path if separate
```

### Test plan

Add/update:

```text
tests/unit/combat/test_combat_reward_trace.py
```

Cases:

```text
- single attack monster kill trace includes REWARD_SOURCE.
- skill kill trace includes REWARD_SOURCE.
- hero defeat trace includes HERO_KILL source.
- neutral target trace includes NONE or no reward intent, depending current design.
```

### Acceptance checklist

- [ ] Single attack reward trace includes source.
- [ ] Skill attack reward trace includes source.
- [ ] Multi-attack reward trace includes source if applicable.
- [ ] Tests assert trace source.
- [ ] Reward values remain unchanged.

### Anti-drift notes

- Do not add reward trace to EntityState.
- Keep trace in combat update/result metadata.
- Do not change reward calculation.

---

# Execution order

| Order | Task                                 | Reason                                               |
| ----: | ------------------------------------ | ---------------------------------------------------- |
|     1 | R1.1 explicit runtime modes          | Prevents more mode ambiguity before adapter changes. |
|     2 | R2.1 heuristic usage records         | Makes adapter behavior auditable.                    |
|     3 | R2.2 split parity by runtime mode    | Proves strict vs compatibility behavior separately.  |
|     4 | R3.1 rename normalized refs          | Cleans module contract before more module features.  |
|     5 | R4.1 real module normalized snapshot | Adds realistic proof after naming cleanup.           |
|     6 | R5.1 reward classification API       | Moves reward logic toward clean identity/relation.   |
|     7 | R6.1 reward trace coverage           | Makes reward source testable.                        |

---

# Final definition of done

This repair is complete when:

```text
- RuntimeContentMode has explicit clean/compat/legacy/manual modes.
- AdapterProjectionResult reports detailed heuristic usages.
- Strict catalog mode rejects heuristic projection.
- Compatibility mode reports heuristic projection.
- NormalizedWorldModule uses clear *_refs fields.
- One real module snapshot proves normalized contract.
- Combat reward classification uses classify_defeated_target().
- Reward trace covers single attack and skill usage reward paths.
```

Target score after this repair:

```text
Current: ~7.8 / 10
Target: 8.8–9.0 / 10
```

This does not require full legacy retirement. It only makes the repaired Phase 20–28 foundation much harder for future AI agents to misinterpret.
