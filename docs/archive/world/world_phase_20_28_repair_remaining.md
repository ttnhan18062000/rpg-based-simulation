---
status: archive
authority: P2
audience: historical
layer: world
original_date: unknown
---

# Implementation Plan: Remaining Phase 20–28 Repair

## 1. Goal

Finish the remaining Phase 20–28 repair work by removing drift risks that still exist after the repaired implementation.

Current implementation is already much better: it has real `data/content/world_modules` tests, real module normalization tests, registry parity tests, and runtime relation projection coverage. For example, tests now verify default content paths, strict load behavior, module count preservation, and real module contribution resolution.   

This plan focuses only on the remaining cleanup.

---

## 2. Scope

This plan covers:

```text
- old explicit path drift
- raw vs normalized world module boundary
- loose v2 module normalized fields
- fragile archetype metadata propagation
- adapter heuristic isolation
- matrix evidence hardening
- combat reward classification legacy enum debt
```

---

## 3. Non-goals

This plan does **not** cover:

```text
- rewriting the whole combat system
- removing legacy compatibility completely
- changing EntityState structure broadly
- adding new content packs
- implementing Phase 29+
- parsing YAML comments
- changing YAML # STATE comments into runtime data
```

YAML comments remain human planning notes only.

---

## 4. Source of truth

| Area                    | Source of truth                          |
| ----------------------- | ---------------------------------------- |
| Catalog content         | `data/content`                           |
| World modules           | `data/content/world_modules`             |
| World compositions      | `data/content/world_compositions`        |
| Simulation scenarios    | `data/content/simulation_scenarios`      |
| Legacy structural tests | Explicitly marked old-path tests only    |
| Runtime proof           | Integration tests, not matrix text alone |

---

## 5. Global anti-drift contract

The implementer must preserve:

```text
- Option A: YAML comments remain human-only.
- Existing legacy tests unless explicitly migrated.
- Existing catalog-backed module/composition integration tests.
- Existing registry parity tests.
- Existing relation projection runtime tests.
```

The implementer must not:

```text
- parse # STATE comments
- silently fall back from data/content to data/world_modules
- weaken fail-closed validation to pass tests
- manually inject v2 modules as the only proof
- hide gameplay projection in adapters without mode/reporting
- remove legacy fallback without an explicit compatibility test
- rewrite unrelated runtime systems
```

---

# Phase summary table

| Repair phase | Goal                                                    | Main output                                                                            | Main tests                        | Risk        |
| ------------ | ------------------------------------------------------- | -------------------------------------------------------------------------------------- | --------------------------------- | ----------- |
| R1           | Remove old explicit path drift                          | All default executable flows use `ContentPathConfig`                                   | content path + CLI/worldgen tests | High        |
| R2           | Harden normalized module boundary                       | `resolve_module_contribution()` accepts only normalized input or normalizes internally | resolver boundary tests           | High        |
| R3           | Finish typed v2 module normalization                    | Replace loose `List[Any]` for v2 refs                                                  | normalizer tests                  | Medium      |
| R4           | Make archetype metadata explicit                        | No suffix-based archetype inference                                                    | compile context metadata tests    | High        |
| R5           | Tighten registry adapter modes                          | Heuristics migration-only and reportable                                               | strict adapter tests              | Medium-high |
| R6           | Strengthen matrix evidence                              | Evidence test names must exist and map to real tests                                   | matrix evidence tests             | Medium      |
| R7           | Move reward classification behind compatibility service | Reduce direct `EntityRole.MONSTER/HERO` reward logic                                   | combat reward tests               | Medium      |

---

# Phase R1 — Remove old explicit path drift

## Phase goal

Ensure `data/content/*` is the default executable source everywhere, not only in new tests.

## Why this phase exists

`ContentPathConfig` and `WorldModuleRepository()` default behavior were added, but some existing tests and flows still explicitly instantiate `WorldModuleRepository("data/world_modules")`. The repaired tests include content-path assertions, but old-path fixtures still remain in worldassembly/worldgeneration tests.   

---

## Task R1.1 — Replace default executable path usage with `ContentPathConfig`

### Objective

Remove hardcoded executable uses of:

```text
data/world_modules
data/worlds
```

where the code is supposed to run catalog-backed content.

### Problem / current behavior

Some tests and older flows still use:

```python
WorldModuleRepository("data/world_modules")
```

even though the new default repository path is expected to be `data/content/world_modules`. 

### Expected behavior

Normal executable flow should use:

```python
paths = ContentPathConfig()
WorldModuleRepository(paths.world_modules_dir)
```

or:

```python
WorldModuleRepository()
```

where the default is already `data/content/world_modules`.

### Technical direction

* Search for hardcoded `data/world_modules`.
* Classify each usage as:

  * `legacy fixture`
  * `old baseline test`
  * `normal executable path`
  * `CLI/runtime path`
* Replace normal executable path usages with `ContentPathConfig`.
* Keep old path usages only if test name/marker says `legacy`.

### Affected components

```text
src CLI resolve flow
src worldgeneration flow
tests/unit/worldassembly/*
tests/unit/worldgeneration/*
tests/unit/worldmodules/*
```

### Test plan

Add/update:

```text
tests/unit/content/test_content_paths.py
tests/unit/worldgeneration/test_generator.py
tests/unit/worldassembly/test_assembly.py
```

Required tests:

```text
- default generator repos use ContentPathConfig
- default worldassembly repos use data/content/world_modules
- explicit legacy module repo test is marked legacy
- CLI resolve path uses ContentPathConfig
```

### Acceptance checklist

* [ ] No normal executable flow hardcodes `data/world_modules`.
* [ ] No normal executable flow hardcodes `data/worlds` for catalog-backed compositions.
* [ ] Old-path tests are explicitly marked legacy.
* [ ] `ContentPathConfig` is the only default path source.
* [ ] Existing real `data/content/world_modules` tests still pass.
* [ ] Failure message clearly says which path was used.

### Anti-drift notes

* Do not delete old path fixtures unless the related tests are migrated.
* Do not silently fallback to old paths when new path is missing.
* Do not make `WorldModuleRepository` search both old and new paths automatically.

### Output evidence

```text
pytest tests/unit/content/test_content_paths.py
pytest tests/integration/worldassembly/test_real_content_world_modules.py
pytest tests/unit/worldgeneration/test_generator.py
```

---

## Task R1.2 — Add architecture guard for old structural paths

### Objective

Prevent future reintroduction of `data/world_modules` as a default executable path.

### Problem / current behavior

Even after fixing current files, another agent can reintroduce:

```python
WorldModuleRepository("data/world_modules")
```

without noticing.

### Expected behavior

Architecture test fails if old path appears outside allowlisted legacy tests.

### Technical direction

Add:

```text
tests/architecture/test_no_old_structural_content_paths.py
```

Rules:

```text
Forbidden outside allowlist:
- "data/world_modules"
- "data/worlds" as composition source
- "data/scenarios" as simulation_scenarios source

Allowed:
- explicitly named legacy tests
- migration documentation
- compatibility fixtures
```

### Acceptance checklist

* [ ] Architecture guard exists.
* [ ] Allowlist is explicit.
* [ ] Guard fails on new default old-path usage.
* [ ] Guard does not fail on documentation.
* [ ] Failure message tells implementer to use `ContentPathConfig`.

### Anti-drift notes

* Do not make the allowlist too broad.
* Do not allow entire directories unless necessary.

### Output evidence

```text
pytest tests/architecture/test_no_old_structural_content_paths.py
```

---

# Phase R2 — Harden raw vs normalized world module boundary

## Phase goal

Make module contribution resolution safe and unambiguous.

## Why this phase exists

Real module normalization tests now exist, and count preservation is tested. However, `resolve_module_contribution()` is still a risky boundary if it accepts raw `WorldModuleSpec` while downstream logic expects normalized maps. The old normalizer used list conversion, and repaired tests now assert dict/list count behavior, so this boundary must be made strict.  

---

## Task R2.1 — Make `resolve_module_contribution()` accept only `NormalizedWorldModule`

### Objective

Remove ambiguous support for raw `WorldModuleSpec` from contribution resolution.

### Problem / current behavior

The resolver path is safer when assembly normalizes first, but direct callers can still pass raw specs. If resolver code assumes `.resources.items()` or `.services.items()`, raw list-based inputs can break.

### Expected behavior

Preferred clean boundary:

```python
def resolve_module_contribution(self, module: NormalizedWorldModule) -> ResolvedModuleContribution:
    ...
```

Any raw module must go through:

```python
WorldModuleAuthoringNormalizer.normalize(raw_spec)
```

before resolution.

### Technical direction

* Change type signature to `NormalizedWorldModule`.
* Add runtime guard:

```python
if not isinstance(module, NormalizedWorldModule):
    raise TypeError("resolve_module_contribution expects NormalizedWorldModule")
```

* Update all callers to normalize first.
* Keep a helper only if needed:

```python
resolve_raw_module_contribution(raw_spec: WorldModuleSpec)
```

but do not use it internally as default.

### Affected components

```text
src/worldassembly/resolver.py
src/worldmodules/normalizer.py
tests/unit/worldassembly/*
tests/integration/worldassembly/*
```

### Test plan

Add:

```text
tests/unit/worldassembly/test_module_resolver_boundary.py
```

Cases:

```text
- normalized module resolves
- raw WorldModuleSpec is rejected clearly
- assembly normalizes before resolving
- real module matrix still resolves
```

### Acceptance checklist

* [ ] `resolve_module_contribution()` accepts only `NormalizedWorldModule`.
* [ ] Raw module input fails clearly.
* [ ] `WorldAssemblyResolver.assemble()` normalizes before resolving.
* [ ] Existing real module integration tests still pass.
* [ ] No caller relies on raw module resolution.

### Anti-drift notes

* Do not support both raw and normalized forms in the same internal method.
* Do not fix by converting `.items()` calls defensively everywhere.
* Keep normalization as a single boundary.

### Output evidence

```text
pytest tests/unit/worldassembly/test_module_resolver_boundary.py
pytest tests/integration/worldassembly/test_real_content_world_modules.py
```

---

## Task R2.2 — Add normalized contribution snapshot test

### Objective

Prove the normalized contribution shape is stable.

### Problem / current behavior

The system has tests proving individual count fields, but less proof that a full normalized module contribution remains stable.

### Expected behavior

For one representative module, test a stable normalized snapshot:

```text
module_id
regions
population_refs
resource_refs
building_refs
service_refs
relationship_refs
```

### Technical direction

Use a real module from `data/content/world_modules`, such as:

```text
frontier_village_core
old_mine_resource_loop
goblin_camp_conflict
```

### Acceptance checklist

* [ ] Snapshot test uses a real YAML module.
* [ ] Snapshot includes count maps.
* [ ] Snapshot includes typed refs.
* [ ] Snapshot does not include raw YAML-only fields.
* [ ] Changes to normalized shape are intentional.

### Anti-drift notes

* Do not snapshot entire raw YAML.
* Do not make snapshot too large.

---

# Phase R3 — Finish typed v2 module normalization

## Phase goal

Remove remaining loose `List[Any]` fields from important v2 normalized module data.

## Why this phase exists

The repaired implementation fixed count maps for resources/buildings/services, but v2 fields like `biomes`, `ecologies`, `populations`, and `relationships` still appear loosely typed in tests and normalizer behavior. The current repaired tests show v2 biomes normalize to simple refs, but this area still needs clearer typing. 

---

## Task R3.1 — Rename normalized v2 fields to explicit ref names

### Objective

Make normalized v2 module contribution fields clearly represent references.

### Problem / current behavior

Fields like:

```python
biomes
ecologies
populations
relationships
```

can mean either inline definitions or references.

### Expected behavior

Normalized model should expose:

```python
biome_refs: tuple[str, ...]
ecology_refs: tuple[str, ...]
population_refs: tuple[str, ...]
relationship_refs: tuple[str, ...]
resource_refs: dict[str, int]
building_refs: dict[str, int]
service_refs: dict[str, int]
```

### Technical direction

* Keep raw `WorldModuleSpec` flexible.
* Convert in normalizer.
* Support list of strings.
* Support list of dicts only if clearly normalized to IDs.
* Reject unresolvable dicts without `id`.

### Affected components

```text
src/worldmodules/normalizer.py
src/worldassembly/resolver.py
src/content/reference_graph.py
tests/unit/worldmodules/test_modules.py
tests/integration/worldassembly/test_real_content_world_modules.py
```

### Test plan

Add tests:

```text
- list biome refs normalize to tuple
- dict biome objects normalize to IDs
- dict without id fails
- relationship refs normalize to tuple
- duplicate refs fail clearly
```

### Acceptance checklist

* [ ] Normalized module uses `*_refs` names.
* [ ] Important v2 refs are typed as tuples.
* [ ] Duplicate refs fail.
* [ ] Dict-with-id authoring is normalized to ID.
* [ ] Dict-without-id authoring fails.
* [ ] Existing real module tests still pass.

### Anti-drift notes

* Do not keep both old and new normalized field names long-term.
* Do not allow arbitrary `Any` for core v2 fields.
* Do not make resolver inspect raw dict shapes.

---

## Task R3.2 — Update reference graph to consume normalized refs

### Objective

Ensure graph edges are built from normalized module refs, not raw module fields.

### Problem / current behavior

Graph validation is more reliable when it consumes normalized structure instead of raw schema variants.

### Expected behavior

Graph building flow:

```text
WorldModuleSpec
→ WorldModuleAuthoringNormalizer
→ NormalizedWorldModule
→ ContentReferenceGraph edges
```

### Technical direction

Add module edge builder:

```python
ContentReferenceGraph.add_module_edges(normalized_module)
```

Edges:

```text
module -> biome
module -> ecology
module -> population
module -> relationship
module -> resource
module -> building
module -> service
```

### Acceptance checklist

* [ ] Graph uses normalized module refs.
* [ ] Resource/building/service count metadata survives.
* [ ] Unknown refs fail with family-aware error.
* [ ] Existing graph tests still pass.
* [ ] No graph code parses YAML comments.

### Anti-drift notes

* Do not duplicate normalizer logic inside graph.
* Do not parse raw YAML in graph.

---

# Phase R4 — Make archetype metadata propagation explicit

## Phase goal

Stop relying on suffix/key guessing to preserve archetype identity.

## Why this phase exists

The repaired implementation proves that archetype/race/profile metadata can reach `CompileContext`, but the implementation is still fragile if archetype ID is inferred from generated keys. The plan needs the archetype ID to travel explicitly from population expansion into compile/runtime metadata.

---

## Task R4.1 — Add explicit archetype source field to expanded population entities

### Objective

Carry `archetype_id` explicitly from population resolution into world assembly.

### Problem / current behavior

Current metadata preservation works for existing cases, but suffix-based matching is fragile. If generated entity IDs change, metadata can silently break.

### Expected behavior

Population expansion should produce an internal record like:

```python
ExpandedPopulationMember(
    archetype_id="goblin_raider",
    count=4,
    spawn_region="goblin_camp",
    source_population_id="goblin_raiding_party",
)
```

### Technical direction

* Add internal dataclass/model for expanded population members.
* Population resolver returns explicit archetype IDs.
* World assembly uses `archetype_id` directly.
* CompileContext overlays are keyed from explicit source metadata, not guessed keys.

### Affected components

```text
src/content/resolvers.py
src/worldassembly/resolver.py
src/worldbuilding/compiler.py
tests/unit/content/test_resolvers.py
tests/unit/worldassembly/test_assembly.py
```

### Test plan

Add:

```text
tests/unit/worldassembly/test_archetype_metadata_propagation.py
```

Cases:

```text
- population member carries archetype_id
- compile profile contains archetype_id/race_id/profile IDs
- generated entity key change does not lose archetype metadata
```

### Acceptance checklist

* [ ] Population expansion returns explicit archetype IDs.
* [ ] World assembly does not infer archetype from generated string suffix.
* [ ] CompileContext preserves archetype ID.
* [ ] CompileContext preserves race/profile/traits/themes.
* [ ] Test proves metadata survives even if generated entity ID format changes.

### Anti-drift notes

* Do not depend on string suffix matching.
* Do not catch resolver errors silently.
* Do not drop metadata just because runtime does not consume it yet.

---

## Task R4.2 — Fail loudly on archetype metadata resolution errors

### Objective

Prevent silent metadata loss.

### Problem / current behavior

If archetype profile resolution fails and the code catches the exception broadly, metadata can disappear while assembly still succeeds.

### Expected behavior

In catalog-backed strict mode:

```text
archetype metadata resolution failure = ResolverError
```

In compatibility/migration mode:

```text
failure = warning/report entry
```

### Technical direction

* Add `strict_metadata` flag to assembly resolver or compile context builder.
* Default strict for catalog-backed tests.
* Add report entry for migration mode.

### Acceptance checklist

* [ ] Missing archetype profile fails in strict mode.
* [ ] Migration mode reports warning, not silent pass.
* [ ] Error includes population ID and archetype ID.
* [ ] Existing valid content still passes.

### Anti-drift notes

* Do not swallow exceptions with bare `except`.
* Do not convert all failures to warnings.

---

# Phase R5 — Tighten registry adapter modes

## Phase goal

Keep compatibility heuristics available only in explicit migration mode, while making catalog-backed strict projection schema-driven.

## Why this phase exists

Registry parity tests now exist, and catalog mode avoids some fallback records, but adapters still contain heuristics when `migration_mode=True`. The source shows adapter branches where fields like `required_tool`, `base_difficulty`, and resource defaults are inferred in migration mode, and `seed_phase1_content()` defaults `migration_mode=True`.  

---

## Task R5.1 — Introduce explicit `RuntimeContentMode`

### Objective

Replace ambiguous `migration_mode=True/False` with clearer runtime modes.

### Problem / current behavior

`migration_mode=True` is useful, but too vague. Another agent can leave it on and think catalog-backed mode is clean.

### Expected behavior

Supported modes:

```text
catalog_strict
catalog_with_compatibility
legacy_fallback
test_manual
```

### Technical direction

Map behavior:

```text
catalog_strict:
    no heuristic projection
    no fallback records
    missing projection fields fail

catalog_with_compatibility:
    compatibility projection allowed
    migration heuristics reported

legacy_fallback:
    old fallback content allowed

test_manual:
    direct builders/tests allowed
```

### Affected components

```text
src/core/registries.py
src/content/runtime_mode.py
tests/integration/content/test_registry_projection_parity.py
```

### Test plan

Add:

```text
tests/unit/content/test_runtime_content_mode.py
```

Cases:

```text
- catalog_strict rejects heuristic-only projection
- catalog_with_compatibility reports heuristic usage
- legacy_fallback allows old fallback records
- test_manual bypasses catalog requirements
```

### Acceptance checklist

* [ ] Runtime modes exist.
* [ ] `migration_mode` is replaced or wrapped by runtime mode.
* [ ] Strict mode fails on heuristic-only adapter projection.
* [ ] Compatibility mode reports heuristic usage.
* [ ] Legacy fallback mode still works.
* [ ] Existing parity tests run under explicit mode.

### Anti-drift notes

* Do not use boolean flags for complex runtime source behavior.
* Do not default clean catalog tests to heuristic migration mode.
* Do not remove legacy fallback yet.

---

## Task R5.2 — Add adapter heuristic usage report

### Objective

Make every heuristic projection visible.

### Problem / current behavior

Heuristics can still happen inside adapters without a structured report.

### Expected behavior

Each adapter returns:

```python
AdapterProjectionResult(
    records=...,
    heuristic_usages=[...],
    fallback_usages=[...],
    errors=[...],
)
```

or stores a report accessible after adaptation.

### Technical direction

Track:

```text
record_id
family
adapter
heuristic_type
reason
strict_mode_allowed
```

### Acceptance checklist

* [ ] Item adapter reports class-fit/use-kind heuristics.
* [ ] Resource adapter reports required-tool/base-difficulty heuristics.
* [ ] Service adapter reports generated/default services.
* [ ] Enemy adapter reports fallback records.
* [ ] Strict mode fails if heuristic usages are non-empty.
* [ ] Compatibility mode exposes report.

### Anti-drift notes

* Do not hide reports in logs only.
* Do not treat heuristic usage as success in strict tests.

---

## Task R5.3 — Split registry parity tests by runtime mode

### Objective

Avoid proving parity only under migration behavior.

### Problem / current behavior

The registry parity fixture seeds content using `migration_mode=True`, which proves default behavior but not clean strict behavior. 

### Expected behavior

Add two parity suites:

```text
catalog_strict parity
catalog_with_compatibility parity
```

### Acceptance checklist

* [ ] Strict parity test exists.
* [ ] Compatibility parity test exists.
* [ ] Fallback-only records excluded from strict parity.
* [ ] Compatibility projections verified separately.
* [ ] Heuristic usage report asserted.

### Anti-drift notes

* Do not remove existing migration parity immediately.
* Do not mix strict and compatibility expectations in one test.

---

# Phase R6 — Strengthen matrix evidence

## Phase goal

Make `ContentUsageMatrix` evidence hard to fake.

## Why this phase exists

Matrix entries now contain evidence fields, but they are still strings. The implementation should verify evidence references actual tests or explicitly mark evidence as planned.

---

## Task R6.1 — Validate evidence test references

### Objective

Ensure `evidence_tests` entries point to real test files/functions.

### Problem / current behavior

A matrix entry can claim:

```text
evidence_tests = ["tests/integration/foo.py::test_bar"]
```

even if that test does not exist.

### Expected behavior

Matrix validation should check:

```text
test file exists
test function exists
test path is syntactically valid
```

### Technical direction

Add lightweight evidence validator:

```python
ContentUsageEvidenceValidator.validate(matrix, project_root)
```

It does not run tests. It only verifies references exist.

### Test plan

Add:

```text
tests/unit/content/test_content_usage_evidence.py
```

Cases:

```text
- valid test reference passes
- missing test file fails
- missing test function fails
- planned evidence must be marked explicitly
```

### Acceptance checklist

* [ ] Evidence validator exists.
* [ ] Matrix references real tests.
* [ ] Missing evidence fails.
* [ ] Planned evidence requires `evidence_status="planned"`.
* [ ] `RUNTIME_AUTHORITATIVE` cannot use planned evidence.

### Anti-drift notes

* Do not run pytest inside matrix validation.
* Do not allow broad file-only evidence for runtime-authoritative claims.

---

## Task R6.2 — Add implementation-state transition guard

### Objective

Prevent families from being marked more complete than their proof allows.

### Expected behavior

Rules:

```text
LOADED_ONLY:
    requires repository evidence

VALIDATED_ONLY:
    requires validator evidence

RESOLVED_PARTIALLY:
    requires resolver evidence

PROJECTED_TO_LEGACY:
    requires adapter/projection evidence

RUNTIME_AUTHORITATIVE:
    requires runtime consumer evidence
```

### Acceptance checklist

* [ ] State transition rules are encoded.
* [ ] `RUNTIME_AUTHORITATIVE` requires runtime consumer evidence.
* [ ] `COMPATIBILITY` families cannot be runtime-authoritative.
* [ ] Resolver-only families cannot claim runtime-authoritative.
* [ ] Tests cover invalid state/evidence combinations.

### Anti-drift notes

* Do not use YAML comments for state.
* Do not infer state from file names.

---

# Phase R7 — Move combat reward classification behind compatibility service

## Phase goal

Reduce direct role-enum dependency in reward/outcome semantics without rewriting combat.

## Why this phase exists

Relation projection now affects attack legality/tactical hostile selection, but reward/outcome logic still directly checks `EntityRole.MONSTER` and `EntityRole.HERO` in several combat paths.   

This is acceptable debt after Phase 28, but it should be isolated before later migration phases.

---

## Task R7.1 — Add `CombatRewardClassificationService`

### Objective

Centralize reward classification instead of scattering direct enum checks.

### Problem / current behavior

Combat reward code does:

```python
if defender.identity.role == EntityRole.MONSTER:
    ...
elif defender.identity.role == EntityRole.HERO:
    ...
```

in single attack, multi-attack, and skill usage paths.   

### Expected behavior

Replace with:

```python
classification = CombatRewardClassificationService.classify_defeated_target(
    attacker,
    defender,
    state,
)
```

Return:

```text
hostile_creature
hero_actor
neutral_actor
protected_civilian
unknown_legacy
```

### Technical direction

Implementation order:

```text
1. clean identity / relation projection if available
2. compatibility mapping
3. legacy enum fallback
```

### Affected components

```text
src/combat/resolution.py
src/combat/rewards.py
tests/unit/combat/*
```

### Test plan

Add:

```text
tests/unit/combat/test_reward_classification.py
```

Cases:

```text
- legacy monster gives same XP/gold as before
- legacy hero gives same rebirth/permadeath behavior
- clean hostile archetype classifies as hostile_creature
- neutral merchant does not get monster reward
- unknown classification returns zero reward unless legacy fallback applies
```

### Acceptance checklist

* [ ] Reward classification service exists.
* [ ] Single attack uses service.
* [ ] Multi-attack uses service.
* [ ] Skill usage uses service.
* [ ] Existing quest/combat reward tests still pass.
* [ ] Legacy enum fallback remains.
* [ ] Clean identity path is tested.

### Anti-drift notes

* Do not change reward numbers.
* Do not rewrite progression system.
* Do not remove hero rebirth/permadeath behavior.
* Do not require full relation projection everywhere yet.

---

## Task R7.2 — Add reward classification trace

### Objective

Make reward source explainable.

### Expected behavior

Combat trace includes:

```text
reward_classification
reward_classification_source
```

Examples:

```text
hostile_creature / relation_projection
hostile_creature / legacy_enum
hero_actor / legacy_enum
neutral_actor / clean_identity
```

### Acceptance checklist

* [ ] Combat trace contains classification.
* [ ] Tests assert source for clean path.
* [ ] Tests assert source for legacy fallback.
* [ ] No reward behavior changes unexpectedly.

### Anti-drift notes

* Do not add large provenance objects to `EntityState`.
* Keep trace as combat result metadata only.

---

# Execution order

| Order | Phase/task                                 | Reason                                      |
| ----: | ------------------------------------------ | ------------------------------------------- |
|     1 | R2.1 normalized resolver boundary          | Prevents hidden runtime breakage.           |
|     2 | R1.1/R1.2 path drift removal               | Prevents reintroducing old source truth.    |
|     3 | R3.1/R3.2 typed v2 refs                    | Finishes module normalization quality.      |
|     4 | R4.1/R4.2 explicit archetype metadata      | Removes fragile suffix matching.            |
|     5 | R5.1–R5.3 runtime mode / adapter reporting | Clarifies strict vs compatibility behavior. |
|     6 | R6.1/R6.2 matrix evidence hardening        | Prevents future overclaiming.               |
|     7 | R7.1/R7.2 reward classification service    | Reduces enum debt after Phase 28.           |

---

# Final definition of done

This remaining repair is complete only when:

```text
- no normal executable flow hardcodes old structural paths
- module contribution resolver has one clear normalized boundary
- normalized v2 fields are typed refs/maps
- archetype metadata is propagated explicitly
- registry adapter heuristics are mode-specific and reportable
- matrix evidence references real tests
- combat reward classification is centralized behind a compatibility service
```

And the core content pipeline still passes:

```text
real data/content files
→ canonical repository path
→ fail-closed schema
→ structure-preserving normalizer
→ typed reference graph
→ resolver
→ assembly / registry / runtime consumer
→ test evidence
```

# Expected score after this repair

| Area                                | Current score |     Target score |
| ----------------------------------- | ------------: | ---------------: |
| Phase 20–28 repaired implementation |     ~7.4 / 10 | **8.7–9.0 / 10** |

This will not fully retire legacy logic, but it will make the Phase 20–28 repair clean enough to build Phase 29+ without hidden source-of-truth drift.
