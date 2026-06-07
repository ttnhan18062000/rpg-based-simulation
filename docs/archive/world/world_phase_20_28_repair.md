# Implementation Repair Plan: Phase 20–28

## 1. Goal

Repair the current Phase 20–28 implementation so that the content pipeline is proven by real executable flow, not only by component existence, schema acceptance, or manually injected test objects.

The repaired implementation must prove this path:

```text
real data/content file
→ canonical repository path
→ fail-closed schema
→ structure-preserving normalizer
→ typed reference graph
→ resolver
→ assembly / registry / runtime consumer
→ test evidence
```

## 2. Scope

This repair plan covers Phase 20–28 only:

```text
Phase 20 — Content usage contract and test map
Phase 21 — Content family registry and strict load report
Phase 22 — Fail-closed schema and authoring-form normalization
Phase 23 — Global content reference graph and active-data validation
Phase 24 — Resolver layer for foundation, living, and social defaults
Phase 25 — Entity archetype and population resolution
Phase 26 — World content projection and runtime registry adapters
Phase 27 — World module and composition usage correction
Phase 28 — Perspective/relation usage and legacy-safe migration
```

## 3. Non-goals

This repair must not become a broad rewrite.

Out of scope:

```text
- Do not rewrite the whole combat engine.
- Do not rewrite EntityState.
- Do not delete legacy fallback paths unless a specific task says so.
- Do not add new fantasy content packs.
- Do not implement Phase 29+ runtime entity factory work.
- Do not move provenance into EntityState.
- Do not introduce a behavior scripting language.
- Do not change observability/reporting systems unless a test directly requires a path update.
```

## 4. Source of truth

### Authoritative direction

```text
world_phase_20_28.md
```

### Canonical executable content paths after repair

```text
data/content/world_modules
data/content/world_compositions
data/content/simulation_scenarios
```

### Legacy or compatibility-only paths

```text
data/world_modules
data/worlds
manual injected module objects in tests
```

These may remain for compatibility/regression tests, but they must not be the default proof of the repaired content pipeline.

## 5. Decision: YAML comments are human-only

YAML comments such as:

```yaml
# STATE: REDESIGNED-CORE
# STATE: LEGACY-EXPORT
# STATE: ADDITIONAL
# STATE: COMPATIBILITY
```

are implementation planning notes for humans.

They must not be parsed by the engine.

They must not be used by validators.

They must not be used for per-record maturity validation.

Implementation status is tracked only at the content-family level through:

```text
ContentUsageMatrix
ContentFamilySpec
resolver coverage
runtime/compile consumer evidence
tests
```

Valid implementation states remain:

```text
LOADED_ONLY
VALIDATED_ONLY
RESOLVED_PARTIALLY
PROJECTED_TO_LEGACY
RUNTIME_AUTHORITATIVE
DESIGN_ONLY
```

## 6. Global anti-drift contract

The implementer must preserve:

```text
- Existing arena/certification tests unless a task explicitly migrates them.
- Existing legacy fallback behavior unless a task explicitly restricts it.
- EntityState structure.
- YAML comments as human planning notes only.
- Sidecar provenance model.
- Existing v1 module compatibility unless a task explicitly changes it.
```

The implementer must not:

```text
- Parse YAML comments for engine behavior.
- Use manual object injection as the only proof of implementation.
- Make WorldCompiler load raw catalog YAML directly.
- Silently fallback from data/content paths to old paths.
- Make tests pass by weakening validation.
- Bless heuristic behavior as the desired target behavior.
- Add active content without a consumer path.
- Rewrite unrelated runtime systems.
- Convert a focused repair task into a broad architecture migration.
```

## 7. Phase issue table

| Phase      | Issue                                                                                                                  |    Severity | Risk                                                                     | Repair direction                                                                                                                      | Evidence required                                              | Status   |
| ---------- | ---------------------------------------------------------------------------------------------------------------------- | ----------: | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | -------- |
| Phase 20   | `ContentUsageMatrix` can still overclaim usage if state is manually declared without executable evidence.              |      Medium | False completion status.                                                 | Keep implementation state family-level. Require evidence test for `RUNTIME_AUTHORITATIVE`. Do not parse YAML comments.                | Matrix test + evidence-test field validation.                  | ✅ Done  |
| Phase 21   | Executable content paths are ambiguous. Some repositories/tests still rely on `data/world_modules` or `data/worlds`.   |        High | New `data/content/*` files may not be used by executable world assembly. | Add canonical content path config. Make `data/content/world_modules` and `data/content/world_compositions` default executable source. | Path config tests + real file loading tests.                   | ✅ Done  |
| Phase 22.1 | Fail-closed schemas exist, but strictness is not enough if real content files are not loaded through the default path. |      Medium | Schema correctness without executable proof.                             | Keep fail-closed schema and pair it with real-file integration tests.                                                                 | Unknown-field failure on real `data/content` files.            | ✅ Done  |
| Phase 22.2 | Composition normalization exists, but must be proven against real `data/content/world_compositions`.                   |      Medium | Composition authoring form may normalize only in isolated tests.         | Test real composition files. Preserve `default_perspectives`. Fail mixed `modules`/`module_refs`.                                     | Real composition matrix test.                                  | ✅ Done  |
| Phase 22.3 | Module normalization is broken/incomplete. Dict fields can be converted with `list(...)`, losing counts.               |    Critical | Real module meaning changes silently.                                    | Replace list-based v2 refs with typed count maps.                                                                                     | Unit count-preservation tests + real module integration tests. | ✅ Done  |
| Phase 23   | Reference graph must not enforce per-record maturity from comments. It also needs typed module v2 edges.               |        High | Invalid confidence in active/dead data validation.                       | Validate references and family-level consumer paths only. Add typed module/composition/scenario edges.                                | Graph edge tests + no comment parsing test.                    | ✅ Done  |
| Phase 24   | Foundation/living/social resolvers mostly prove fetch/resolve, not runtime behavior.                                   |      Medium | Families may be marked too complete.                                     | Keep these as `RESOLVED_PARTIALLY` unless runtime consumer tests exist.                                                               | Resolver tests + matrix state tests.                           | ✅ Done  |
| Phase 25   | Archetype/population resolution exists, but output may collapse into legacy `role/faction/count`.                      |        High | Archetype data is lost before runtime/compile.                           | Preserve archetype/race/profile metadata through `CompileContext`.                                                                    | Metadata survival tests.                                       | ✅ Done  |
| Phase 26   | Registry adapters exist but still encode heuristic/fallback gameplay truth.                                            |        High | Legacy logic remains hidden inside catalog-backed mode.                  | Move projection meaning into schema/compatibility data. Add generic registry parity tests.                                            | Registry parity tests + strict fallback reporting.             | ✅ Done  |
| Phase 27   | Tests manually inject v2 modules and treat heuristics as success.                                                      |    Critical | Fake migration confidence.                                               | Use real `data/content/world_modules` and real compositions in integration tests.                                                     | Real module/composition matrix.                                | ✅ Done  |
| Phase 28   | Relation projection exists but is not proven in a high-impact runtime consumer.                                        | Medium-High | Service exists but simulation behavior still follows legacy buckets.     | Integrate projection into one runtime decision first, preferably combat target classification.                                        | Runtime classification test + legacy fallback regression.      | ✅ Done  |

## 8. Phase summary table

| Phase | Goal                         | Main output                                         | Main tests                     | Risk        | Status  |
| ----- | ---------------------------- | --------------------------------------------------- | ------------------------------ | ----------- | ------- |
| 20    | Strengthen usage contract    | Evidence-backed `ContentUsageMatrix`                | content usage matrix tests     | Medium      | ✅ Done |
| 21    | Unify executable paths       | `ContentPathConfig` and path-aware loaders          | content path tests             | High        | ✅ Done |
| 22    | Fix schema/normalization     | Count-preserving `NormalizedWorldModule`            | normalizer + real module tests | Critical    | ✅ Done |
| 23    | Strengthen reference graph   | Typed graph edges and family-level usage validation | graph tests                    | High        | ✅ Done |
| 24    | Clarify resolver completion  | Partial resolver status only                        | resolver + matrix tests        | Medium      | ✅ Done |
| 25    | Preserve archetype data      | Compile context metadata survival                   | archetype/population tests     | High        | ✅ Done |
| 26    | Clean registry projection    | Explicit schema/compat adapter projection           | registry parity tests          | High        | ✅ Done |
| 27    | Prove real content execution | Real module/composition integration matrix          | integration tests              | Critical    | ✅ Done |
| 28    | Prove relation runtime usage | First runtime consumer using projection             | combat classification test     | Medium-High | ✅ Done |

---

# Phase 20 — Content usage contract repair

## Phase goal

Ensure implementation status is tracked at content-family level and backed by evidence, not YAML comments or manual claims.

## Dependencies

```text
- Existing ContentUsageMatrix or equivalent report exists.
- ContentFamilySpec exists or is planned in Phase 21.
```

## Tasks

### Task 20.1 — Enforce new decision in `ContentUsageMatrix`

#### Objective

Make it explicit that YAML comments are human-only and not engine validation input.

#### Problem / current behavior

The implementation can confuse two separate concepts:

```text
YAML comments = content maturity / planning note
implementation_state = engine usage status
```

If validators or tests infer maturity from comments, the repair will drift.

#### Expected behavior

`ContentUsageMatrix` validates by family only:

```text
family path
schema class
repository index
validator
resolver
consumer
implementation_state
evidence test
```

It does not validate individual records based on `# STATE:` comments.

#### Technical direction

- Add a policy note to matrix/report output.
- Ensure matrix loader does not parse YAML comments.
- Keep `implementation_state` at family level.
- Add an `evidence_tests` or `evidence` field for claims above `VALIDATED_ONLY`.

#### Affected components

```text
src/content/usage_matrix.py
src/content/repository.py
tests/unit/content/test_content_usage_matrix.py
```

Names may differ in implementation; keep the responsibility boundaries.

#### Test plan

Add/update:

```text
test_yaml_state_comments_are_ignored
test_every_family_has_implementation_state
test_runtime_authoritative_requires_evidence
test_compatibility_family_not_runtime_authoritative
```

#### Acceptance checklist

- [x] No source code parses `# STATE:` comments.
- [x] No validator depends on YAML comments.
- [x] Every content family has exactly one `implementation_state`.
- [x] `RUNTIME_AUTHORITATIVE` requires at least one evidence test.
- [x] `COMPATIBILITY` family cannot be marked `RUNTIME_AUTHORITATIVE`.
- [x] Matrix report states comments are planning-only.

#### Verification Status
- Status: Completed on 2026-06-06.
- Changes made: Added evidence validation to matrix entry schema and report generation. Added static checks to verify no parser/validator processes "STATE:" comments. Added checks ensuring exactly one implementation state and valid compatibility constraints. All matrix tests pass.

#### Anti-drift notes

- Do not add `state` fields to every YAML record for this repair.
- Do not create per-record maturity validation.
- Do not mark a family complete just because it loads.

#### Output evidence

- Passing content usage matrix tests.
- Matrix report showing family-level states and evidence links.

### Task 20.2 — Downgrade overclaimed implementation states

#### Objective

Prevent families from being marked more complete than their actual consumer path.

#### Problem / current behavior

A family can appear complete because it has schemas, validators, and resolvers, while runtime still does not consume the resolved output.

#### Expected behavior

Families are classified honestly:

```text
LOADED_ONLY            → parsed only
VALIDATED_ONLY         → schema/ref validation only
RESOLVED_PARTIALLY     → resolver exists but runtime does not fully consume output
PROJECTED_TO_LEGACY    → reaches runtime through compatibility adapter
RUNTIME_AUTHORITATIVE  → real runtime/compile consumer proven by test
DESIGN_ONLY            → intentionally non-executable now
```

#### Technical direction

- Review all content family entries.
- Downgrade foundation/living/social families to `RESOLVED_PARTIALLY` if they only resolve but do not affect runtime behavior.
- Mark compatibility families as `PROJECTED_TO_LEGACY` or adapter-only.
- Mark scenario family as `DESIGN_ONLY` if no scenario resolver is currently active.

#### Test plan

Add/update:

```text
test_no_active_family_is_loaded_only_without_explicit_design_only
test_resolved_partially_allowed_for_resolver_only_family
test_runtime_authoritative_requires_runtime_consumer_evidence
```

#### Acceptance checklist

- [x] Family states reflect actual implementation.
- [x] No family is upgraded based on documentation text only.
- [x] Resolver-only families are not marked runtime-authoritative.
- [x] Compatibility families are adapter-only.

#### Verification Status
- Status: Completed on 2026-06-06.
- Changes made: Verified all family entries are correctly defined, downgraded `simulation_scenarios` to `DESIGN_ONLY`. Added corresponding matrix constraints tests which pass.

#### Anti-drift notes

- Do not make runtime code changes just to satisfy matrix labels.
- First classify honestly, then implement missing consumer paths in later phases.

---

# Phase 21 — Content family registry and executable path repair

## Phase goal

Make `data/content/*` structural paths the canonical executable source for Phase 20–28 content work, or explicitly mark old paths as legacy/test-only.

## Dependencies

```text
- CatalogRepository exists.
- WorldModuleRepository exists.
- Composition loader/normalizer exists.
```

## Tasks

### Task 21.1 — Add canonical `ContentPathConfig`

#### Objective

Create one source of truth for content paths.

#### Problem / current behavior

Some tests and loaders still use old paths like:

```text
data/world_modules
data/worlds
```

while proposed content lives under:

```text
data/content/world_modules
data/content/world_compositions
```

This allows the migration to look implemented while executable logic bypasses the new content.

#### Expected behavior

Default executable paths are:

```text
content_root = data/content
world_modules_dir = data/content/world_modules
world_compositions_dir = data/content/world_compositions
simulation_scenarios_dir = data/content/simulation_scenarios
```

#### Technical direction

Add a config object such as:

```python
@dataclass(frozen=True)
class ContentPathConfig:
    content_root: str = "data/content"
    world_modules_dir: str = "data/content/world_modules"
    world_compositions_dir: str = "data/content/world_compositions"
    simulation_scenarios_dir: str = "data/content/simulation_scenarios"
```

Use this config in:

```text
CatalogRepository
WorldModuleRepository
composition loader
scenario loader if present
CLI resolve command if present
validation commands if present
```

#### Affected components

```text
src/content/paths.py
src/content/repository.py
src/worldmodules/repository.py
src/worldassembly/*
src/worldbuilding/*
tests/unit/content/test_content_paths.py
```

#### Test plan

Add:

```text
test_default_content_paths_point_to_data_content
test_world_module_repository_default_uses_content_path
test_composition_loader_default_uses_content_path
test_old_world_modules_path_not_used_by_default
```

#### Acceptance checklist

- [x] One config object owns structural content paths.
- [x] Default module repository path is `data/content/world_modules`.
- [x] Default composition path is `data/content/world_compositions`.
- [x] Default scenario path is `data/content/simulation_scenarios` or family is marked design-only.
- [x] Old `data/world_modules` path is explicit legacy/test-only.
- [x] Tests fail if default loader silently uses old path.

#### Verification Status
- Status: Completed on 2026-06-06.
- Changes made: Added `ContentPathConfig` inside `src/content/paths.py`. Updated `CatalogRepository` and `WorldModuleRepository` to default to these structural paths when constructed without overrides. Added test cases in `tests/unit/content/test_content_paths.py` verifying correct defaults.

#### Output evidence

- Passing content path tests.
- A short printed/debug report showing configured paths.

#### Anti-drift notes

- Do not delete old paths in this task.
- Do not make loaders silently fallback to old paths.
- Do not fix path ambiguity by duplicating content files.

#### Output evidence

- Passing content path tests.
- A short printed/debug report showing configured paths.

### Task 21.2 — Harden strict load report around structural paths

#### Objective

Ensure strict loading reports unknown, missing, duplicate, and ignored structural content clearly.

#### Problem / current behavior

Strict loading may focus on schema errors and missing required files, while ignored files or empty active families can remain weakly enforced.

#### Expected behavior

Strict mode fails on:

```text
missing required files
schema errors
duplicate IDs
duplicate family paths
unknown active YAML files
empty required active families
```

Optional missing files are report-only unless configured otherwise.

#### Technical direction

Update load report to include:

```text
loaded_families
loaded_files
record_counts
missing_required_files
missing_optional_files
ignored_files
duplicate_ids
schema_errors
fingerprint
```

Ensure strict mode acts on the report.

#### Test plan

Add/update:

```text
test_strict_load_fails_on_duplicate_id
test_strict_load_fails_on_ignored_active_yaml
test_strict_load_fails_on_empty_required_family
test_optional_missing_file_is_reported_not_failed
test_load_report_fingerprint_changes_when_content_changes
```

#### Acceptance checklist

- [x] Strict load fails on duplicate IDs.
- [x] Strict load fails on ignored active YAML files.
- [x] Strict load fails on empty required active families.
- [x] Load report is stored and accessible after `load_all()`.
- [x] Fingerprint changes when loaded content changes.
- [x] Existing catalog tests still pass.

#### Verification Status
- Status: Completed on 2026-06-06.
- Changes made: Hardened `load_all(strict=True)` to raise `ValueError` on duplicate IDs, unknown active YAML files (ignored files), or empty required active families. The load report is saved to `self.last_report` after loading. Added unit tests for these validation checks.

#### Anti-drift notes

- Do not weaken strict schema validation to pass old files.
- Do not ignore unknown files without reporting them.

---

# Phase 22 — Fail-closed schema and normalization repair

## Phase goal

Ensure active authoring forms are fail-closed and normalization preserves structure.

## Dependencies

```text
- ContentPathConfig from Phase 21.
- Existing WorldModuleSpec / WorldCompositionSpec.
- Existing normalizers.
```

## Tasks

### Task 22.1 — Keep fail-closed schemas tied to real files

#### Objective

Ensure fail-closed schemas are tested against real `data/content` files, not only synthetic models.

#### Problem / current behavior

Schema tests can pass while real executable path still bypasses the new files.

#### Expected behavior

Unknown fields fail in active schemas when loading real files through canonical paths.

#### Technical direction

- Keep active Pydantic models as `extra="forbid"` or equivalent.
- Allow extensions only under explicit metadata/extension fields if already designed.
- Make error messages include file/family/record ID.

#### Test plan

Add/update:

```text
test_unknown_field_in_real_world_module_fails
test_unknown_field_in_real_composition_fails
test_allowed_metadata_field_does_not_fail_if_model_supports_it
```

#### Acceptance checklist

- [x] Active schemas reject unknown top-level fields.
- [x] Real files are loaded through canonical path in tests.
- [x] Error includes file/family/record ID.
- [x] Existing validator tests still pass.

#### Verification Status
- Status: Completed on 2026-06-06.
- Changes made: Added Try-Except wrapper around WorldModuleSpec and WorldCompositionSpec validation, raising standard error with file, family, and record ID context. Verified with unit tests.

#### Anti-drift notes

- Do not loosen schemas to pass bad data.
- Do not add catch-all `extra` fields without a clear metadata boundary.

### Task 22.2 — Validate composition normalization with real files

#### Objective

Prove composition authoring forms normalize correctly from real `data/content/world_compositions` files.

#### Problem / current behavior

`modules` shorthand may be unit-tested, but real composition files may not be part of executable tests.

#### Expected behavior

Both forms normalize into one executable representation:

```text
modules shorthand → module_refs
module_refs       → module_refs
```

Mixed forms fail.

`default_perspectives` must be preserved separately and not silently dropped.

#### Technical direction

- Ensure `WorldCompositionNormalizer` handles real files.
- Resolver receives normalized composition only.
- Composition fingerprint uses normalized content deterministically.

#### Test plan

Add/update:

```text
test_real_composition_modules_shorthand_normalizes
test_real_composition_referenced_modules_exist
test_mixed_modules_and_module_refs_fails
test_default_perspectives_preserved
test_composition_fingerprint_deterministic
```

#### Acceptance checklist

- [x] Existing `module_refs` tests still pass.
- [x] Real `modules` shorthand works.
- [x] Mixed authoring forms fail clearly.
- [x] Unknown composition fields fail clearly.
- [x] `default_perspectives` survives normalization.
- [x] Normalized composition is deterministic.

#### Verification Status
- Status: Completed on 2026-06-06.
- Changes made: Added unit tests verifying real composition normalization. Verified `default_perspectives` survives normalization and mixed declaration types raise a `ValueError`.

#### Anti-drift notes

- Do not make the world compiler understand multiple raw forms.
- Normalize first, then assemble.

### Task 22.3 — Fix module v2 normalization count loss

#### Objective

Preserve structured module contribution data.

#### Problem / current behavior

The normalizer can convert mappings with `list(...)`, causing count loss:

```yaml
resources:
  wood_node: 2
```

can become:

```text
["wood_node"]
```

This is a critical bug because it silently changes authoring meaning.

#### Expected behavior

Mapping authoring preserves counts:

```yaml
resources:
  wood_node: 2
```

normalizes to:

```python
resource_refs = {"wood_node": 2}
```

List shorthand normalizes to count `1`:

```yaml
resources:
  - wood_node
```

normalizes to:

```python
resource_refs = {"wood_node": 1}
```

#### Technical direction

Replace list-based v2 contribution fields with typed maps:

```python
resource_refs: dict[str, int]
building_refs: dict[str, int]
service_refs: dict[str, int]
```

Use named ref fields for other refs:

```python
biome_refs: tuple[str, ...]
ecology_refs: tuple[str, ...]
population_refs: tuple[str, ...]
relationship_refs: tuple[str, ...]
faction_refs: tuple[str, ...]
```

Add helper:

```python
def normalize_count_map(value, *, field_name: str) -> dict[str, int]: ...
```

Validation:

```text
- positive integer count required
- zero count rejected unless explicitly allowed
- negative count rejected
- non-string keys rejected
- duplicate list values either fail or aggregate deterministically; choose one and test it
```

Recommended: fail duplicate list values to avoid ambiguity.

#### Affected components

```text
WorldModuleAuthoringNormalizer
NormalizedWorldModule
ResolvedModuleContribution
WorldAssemblyResolver
ContentReferenceGraph
world module tests
```

#### Test plan

Add/update:

```text
test_list_resources_normalize_to_count_one
test_dict_resources_preserve_counts
test_dict_buildings_preserve_counts
test_dict_services_preserve_counts
test_negative_count_fails
test_zero_count_fails
test_duplicate_list_refs_fail_or_are_deterministically_aggregated
test_real_world_module_preserves_resource_counts
```

#### Acceptance checklist

- [x] Dict resource counts are preserved.
- [x] Dict building counts are preserved.
- [x] Dict service counts are preserved.
- [x] List shorthand becomes count `1`.
- [x] Invalid counts fail clearly.
- [x] `NormalizedWorldModule` no longer uses `List[Any]` for important v2 refs.
- [x] Existing v1 module tests still pass.
- [x] No test accepts count loss as expected behavior.

#### Verification Status
- Status: Completed on 2026-06-06.
- Changes made: Added services count mapping support, implemented `normalize_count_map`, and updated assembly resolver loops to process count dicts. All module and assembly tests pass.

#### Anti-drift notes

- Do not solve this by changing YAML only.
- Do not manually inject module objects as the only proof.
- Do not add behavior scripts to modules.
- Do not call heuristic expansion the target behavior.

#### Output evidence

- Before/after normalized output for at least one real module.
- Passing unit and real-file integration tests.

---

# Phase 23 — Reference graph and family-level usage repair

## Phase goal

Validate typed references and family-level consumer paths without using YAML comments as data.

## Dependencies

```text
- Phase 20 new decision confirmed.
- Phase 22 normalized module fields exist.
```

## Tasks

### Task 23.1 — Remove comment-state assumptions from graph validation

#### Objective

Ensure `ContentReferenceGraph` ignores YAML comments and validates only parsed content and family-level usage.

#### Problem / current behavior

Dead-active-data validation can drift into trying to use `# STATE:` comments as machine-readable maturity.

#### Expected behavior

Graph responsibilities:

```text
all IDs exist
all references resolve
reverse references can be queried
family-level consumer path exists
compatibility records point to clean source data
```

Graph non-responsibilities:

```text
parse YAML comments
decide per-record maturity from comments
```

#### Technical direction

- Remove any code/test that depends on comment text.
- Keep unused-data checks at family level.
- Use `ContentUsageMatrix` to decide whether a family needs a consumer path.

#### Test plan

Add/update:

```text
test_graph_ignores_yaml_comments
test_family_without_declared_consumer_fails_usage_contract
test_design_only_family_may_have_no_runtime_consumer
test_compatibility_family_points_to_clean_source
```

#### Acceptance checklist

- [x] Graph ignores YAML comments.
- [x] No per-record maturity validation exists.
- [x] Family-level consumer validation exists.
- [x] Compatibility references validate against clean source data.

#### Verification Status
- Status: Completed on 2026-06-06.
- Changes made: Added unit tests verifying graph ignores comments, family-level consumer paths are validated based on CONTENT_USAGE_MATRIX, and compatibility entries only reference valid archetypes.

#### Anti-drift notes

- Do not introduce metadata fields just to replace comments in this repair.
- Do not create one-off rules per content record.

### Task 23.2 — Add typed edges for module/composition/scenario refs

#### Objective

Make the graph understand real Phase 20–28 content relationships.

#### Problem / current behavior

Generic field scanning can miss or weaken module v2 relationships, especially dictionary fields with counts.

#### Expected behavior

Graph includes typed edges:

```text
composition -> module
module -> biome
module -> ecology
module -> population
module -> relationship
module -> resource
module -> building
module -> service
scenario -> composition
scenario -> perspective
```

For count maps:

```yaml
resources:
  iron_vein: 8
```

edge:

```text
module:old_mine_resource_loop -> resource:iron_vein
metadata: {count: 8}
```

#### Technical direction

- Use normalized module fields as graph input.
- Store count metadata on edges or keep it in normalized data and expose lookup.
- Add reverse lookup support.

#### Test plan

Add/update:

```text
test_module_resource_dict_creates_typed_edges
test_module_building_dict_creates_typed_edges
test_module_service_dict_creates_typed_edges
test_composition_module_edges
test_scenario_edges_if_scenario_family_executable
test_reverse_lookup_for_population_to_modules
```

#### Acceptance checklist

- [x] Module resource refs become graph edges.
- [x] Module building refs become graph edges.
- [x] Module service refs become graph edges.
- [x] Composition module refs become graph edges.
- [x] Scenario refs become graph edges if scenario family is executable.
- [x] Counts are preserved as edge metadata or normalized contribution data.

#### Verification Status
- Status: Completed on 2026-06-06.
- Changes made: Added edge metadata mapping inside ContentReferenceGraph and explicitly scanned module count maps and composition modules during graph construction. Checked counts are preserved in edge metadata using tests.

#### Anti-drift notes

- Do not rely on string matching alone if typed fields exist.
- Do not run full-world content validation during partial module validation.

---

# Phase 24 — Resolver layer claim repair

## Phase goal

Keep resolver families honest: resolver existence is not runtime authority.

## Dependencies

```text
- ContentUsageMatrix repaired.
- Foundation/living/social schemas and resolvers exist.
```

## Tasks

### Task 24.1 — Downgrade resolver-only families to `RESOLVED_PARTIALLY`

#### Objective

Prevent resolver-only data from being marked runtime-authoritative.

#### Problem / current behavior

Foundation/living/social resolvers may fetch data correctly, but many fields do not yet affect behavior:

```text
need_profiles
sense_profiles
drive_profiles
body_model
relationship_axes in all runtime systems
```

#### Expected behavior

Families stay `RESOLVED_PARTIALLY` until runtime consumer tests exist.

#### Technical direction

- Update `ContentUsageMatrix` state for foundation/living/social families.
- Ensure tests assert the correct non-final state.
- Keep resolver unit tests focused on fetch/merge/default behavior.

#### Test plan

Add/update:

```text
test_living_family_marked_resolved_partially_until_runtime_consumer
test_foundation_resolver_fetches_known_ids
test_missing_foundation_id_fails_clearly
test_social_resolver_resolves_relationships_without_claiming_all_runtime_usage
```

#### Acceptance checklist

- [x] Resolver tests prove fetch/merge/default behavior.
- [x] Matrix does not claim runtime behavior prematurely.
- [x] Runtime-authoritative status is reserved for actual consumer tests.
- [x] Later phases can upgrade state when behavior consumers exist.

#### Verification Status
- Status: Completed on 2026-06-06.
- Changes made: Downgraded all foundation, living, and social families to RESOLVED_PARTIALLY, adding new unit tests that assert this status and check resolver fetch/error behavior. All tests pass.

#### Anti-drift notes

- Do not implement full motivation/perception behavior in this repair.
- Do not mark a resolver as runtime-authoritative because it returns data.

### Task 24.2 — Add resolver output evidence fields

#### Objective

Show what each resolver contributes without claiming full runtime behavior.

#### Expected behavior

Matrix/report can say:

```text
resolver_evidence: FoundationResolver resolves traits/materials/themes
runtime_consumer_evidence: none yet
implementation_state: RESOLVED_PARTIALLY
```

#### Acceptance checklist

- [x] Resolver evidence and runtime evidence are separate.
- [x] Report makes partial status obvious.
- [x] No agent can confuse resolver completion with runtime migration completion.

#### Verification Status
- Status: Completed on 2026-06-06.
- Changes made: Added separate `resolver_evidence` and `runtime_consumer_evidence` columns to the `ContentFamilyMatrixEntry` pydantic model, populated them for all entries in the matrix, and updated `generate_matrix_report` to format them. Verified matrix tests and checked generated markdown output.


---

# Phase 25 — Entity archetype and population resolution repair

## Phase goal

Preserve archetype and population metadata through compile/assembly boundaries.

## Dependencies

```text
- EntityArchetypeResolver exists.
- PopulationRecipeResolver exists.
- CompileContext exists.
- World assembly path exists.
```

## Tasks

### Task 25.1 — Preserve archetype metadata in resolved outputs

#### Objective

Ensure archetype data does not collapse into legacy `role/faction/count` only.

#### Problem / current behavior

Archetype/population resolution may exist, but executable world assembly can still reduce entities to:

```text
role
faction
count
spawn_region
```

This loses clean identity and profile source data.

#### Expected behavior

Resolved archetype/population output preserves:

```text
archetype_id
race_id
role_id
faction_id
stat_profile_id
combat_profile_id
cognition_profile_id
drive_profile_id
need_profile_id
sense_profile_id
inventory_profile_id
skill_profile_id
traits
themes
```

#### Technical direction

- Extend `ResolvedEntityArchetype` if needed.
- Extend population expansion output if needed.
- Extend `CompileContext` metadata sidecar/overlays if needed.
- Keep legacy `role/faction/count` as compatibility output, not the only output.

#### Test plan

Add/update:

```text
test_resolved_archetype_preserves_identity_metadata
test_population_expansion_preserves_archetype_ids
test_compile_context_contains_archetype_and_race_ids
test_compile_context_contains_profile_source_ids
test_legacy_role_faction_count_path_still_works
```

#### Acceptance checklist

- [x] Population resolver outputs archetype IDs.
- [x] CompileContext keeps archetype/race/profile metadata.
- [x] World assembly uses archetype-native populations for new modules.
- [x] Legacy `role/faction/count` remains compatibility authoring.
- [x] Tests assert metadata survives resolution.

#### Verification Status
- Status: Completed on 2026-06-06.
- Changes made: Extended `ResolvedEntityProfile` in `src/worldassembly/models.py` with full archetype identity and profile ID fields (`archetype_id`, `race_id`, `role_id`, `faction_id`, `traits`, `themes`, `stat_profile_id`, `combat_profile_id`, `cognition_profile_id`, `drive_profile_id`, `need_profile_id`, `sense_profile_id`, `inventory_profile_id`, `skill_profile_id`). `CompileProfileResolver.resolve` now calls `EntityArchetypeResolver` to populate these fields when the entity key matches a known archetype ID. Also fixed a bug where an incorrect call to `self.profile_resolver.faction_semantics.resolve_faction_defaults` was replaced with the correct `self.catalog_repo.get_faction` lookup. Tests added in `tests/unit/worldassembly/test_archetype_preservation.py`. All 159 tests (26 worldassembly + 133 content) pass.

#### Anti-drift notes

- Do not rewrite `EntityState` in this task.
- Do not implement runtime entity factory here.
- Do not drop legacy compatibility path.

### Task 25.2 — Validate population preferred regions against assembled regions

#### Objective

Ensure population recipes do not reference regions that never exist in the selected module/composition.

#### Problem / current behavior

Population recipe validation may check ID existence globally but not selected-world availability.

#### Expected behavior

During module/composition assembly, preferred spawn regions are validated against the resolved composition contribution.

#### Technical direction

- Validate after module contribution merge, not during standalone catalog load.
- Produce clear warning/error depending on context.
- Keep module-level partial validation structural only.

#### Test plan

Add/update:

```text
test_population_preferred_region_exists_in_composition
test_population_preferred_region_missing_fails_or_warns_by_context
test_standalone_population_catalog_load_does_not_require_world_context
```

#### Acceptance checklist

- [x] Population preferred regions are checked against assembled regions.
- [x] Standalone catalog loading does not require world context.
- [x] Error includes population ID and missing region ID.

#### Verification Status
- Status: Completed on 2026-06-06.
- Changes made: Added preferred spawn region validation in `WorldAssemblyResolver.resolve_module_contribution` (lines 707–712). After resolving a population recipe, the module's region IDs are cross-checked against the preferred regions list; missing regions raise `ResolverError` with the population recipe ID and missing region ID. Error message format: `[region] '{region_id}' not found — preferred spawn region in population recipe '{recipe_id}' is missing from module regions`. Tested in `test_population_preferred_region_validation_fails_on_missing_region`.

#### Anti-drift notes

- Do not run full world validation while loading standalone populations.

---

# Phase 26 — Registry adapter repair

## Phase goal

Make registry projection explicit and testable, not hidden inside heuristic/fallback code.

## Dependencies

```text
- CatalogRepository loads runtime catalog families.
- Registry adapters exist or can be introduced.
- seed_phase1_content exists.
```

## Tasks

### Task 26.1 — Move adapter meaning into explicit schema or compatibility data

#### Objective

Reduce hidden gameplay truth in adapter code.

#### Problem / current behavior

Adapter/seeding logic may infer:

```text
item kind from categories
class fit from item ID
resource legacy ID remapping
required-tool heuristics
service affordances/defaults
fallback enemies such as rat
```

This keeps legacy gameplay truth hidden inside catalog-backed mode.

#### Expected behavior

Adapters use explicit data first:

```text
ItemDefinition.use_kind
ItemDefinition.class_fit
ItemDefinition.equipment_slot
ResourceDefinition.runtime_kind
ResourceDefinition.legacy_id
ResourceDefinition.required_tool
ServiceDefinition.provided_items
ServiceDefinition.provided_recipes
ServiceDefinition.affordances
Compatibility legacy enemy projection
Compatibility migration map
```

#### Technical direction

- Add schema fields only where needed.
- Prefer compatibility data for legacy mappings.
- Keep heuristics only in explicit legacy/migration mode.
- Make fallback usage visible in report.

#### Test plan

Add/update:

```text
test_item_adapter_uses_explicit_use_kind
test_item_adapter_uses_explicit_class_fit
test_resource_adapter_uses_explicit_legacy_id
test_service_adapter_does_not_inject_default_service_in_catalog_mode
test_fallback_enemy_not_seeded_in_catalog_mode
test_fallback_usage_reported_in_legacy_mode
```

#### Acceptance checklist

- [x] Adapters use explicit schema fields first.
- [x] Heuristics are migration-only, not normal catalog-backed mode.
- [x] Fallback enemy records are not seeded in catalog-backed mode.
- [x] Service defaults are catalog records or compatibility records.
- [x] Adapter errors include source record ID.

#### Verification status

- Status: Completed on 2026-06-06.
- Changes made: Added explicit fields to `ItemDefinition`, `ResourceDefinition`, and `ServiceProfileDefinition`. Updated adapters to check explicit fields first. Disabled heuristics in normal catalog-backed mode (`migration_mode=False`). Disabled `rat` enemy seeding in catalog mode. Disabled hometown services seeding in catalog mode. Verified with unit tests in `tests/unit/core/test_registry_adapters.py`.

#### Anti-drift notes

- Do not remove all fallback immediately.
- Do not keep hidden heuristics under new class names.
- Do not make schema fields optional if strict mode needs them.

### Task 26.2 — Add generic registry parity tests

#### Objective

Prove catalog records reach runtime registries.

#### Problem / current behavior

Tests may check a few known records but not prove all active catalog records are projected.

#### Expected behavior

Data-driven parity tests:

```text
for each active item definition → ItemRegistry contains projected item
for each active recipe definition → RecipeRegistry contains projected recipe
for each active service definition → ServiceRegistry contains projected service
for each active runtime region → RegionRegistry contains projected region
for each compatibility enemy projection → EnemyRegistry contains projected enemy
```

Use family-level state, not YAML comments, to decide active/in-scope families.

#### Test plan

Add:

```text
tests/integration/content/test_registry_projection_parity.py
```

Cases:

```text
test_item_registry_parity
test_recipe_registry_parity
test_service_registry_parity
test_region_registry_parity
test_enemy_projection_registry_parity
```

#### Acceptance checklist

- [x] Item parity test exists.
- [x] Recipe parity test exists.
- [x] Service parity test exists.
- [x] Region parity test exists.
- [x] Enemy projection parity test exists.
- [x] Tests fail if adapter silently skips a record.
- [x] Fallback-only records are excluded explicitly.

#### Verification status

- Status: Completed on 2026-06-06.
- Changes made: Implemented data-driven integration parity tests in `tests/integration/content/test_registry_projection_parity.py`. Verified that active catalog records (items, recipes, services, regions, enemy projections) are projected correctly to registries, excluding fallback-only records explicitly.

#### Anti-drift notes

- Do not create one test per item.
- Use data-driven iteration.
- Do not make parity pass by seeding fallback records in catalog mode.

---

# Phase 27 — World module and composition usage repair

## Phase goal

Prove that real `data/content/world_modules` and `data/content/world_compositions` are executable.

## Dependencies

```text
- Phase 21 canonical paths.
- Phase 22 count-preserving module normalizer.
- Phase 23 typed graph edges.
```

## Tasks

### Task 27.1 — Add real module integration matrix

#### Objective

Replace manual-injection proof with real-file proof.

#### Problem / current behavior

A test can manually create a module object, inject it into a repository, and call that implementation proof. This bypasses file loading, schema validation, path configuration, and real authoring data.

#### Expected behavior

Real files under `data/content/world_modules` are loaded, validated, normalized, graph-checked, and resolved.

Minimum module matrix:

```text
frontier_village_core
wolf_den_near_forest
goblin_camp_conflict
old_mine_resource_loop
bandit_road_trade_pressure
moon_cult_ruins
undead_battlefield
```

#### Technical direction

For each module:

```text
load from canonical path
validate schema
normalize
build typed reference edges
resolve contribution
assert counts preserved where applicable
```

#### Test plan

Add:

```text
tests/integration/worldassembly/test_real_content_world_modules.py
```

Cases:

```text
test_real_world_modules_load_from_data_content
test_real_world_modules_normalize
test_real_world_modules_preserve_count_maps
test_real_world_modules_resolve_contributions
test_real_world_modules_reference_graph_edges_exist
```

#### Acceptance checklist

- [x] Real module files are loaded from `data/content/world_modules`.
- [x] Real modules pass schema validation.
- [x] Real modules normalize without structure loss.
- [x] Real modules assemble into contributions.
- [x] Manual injection tests are secondary only.
- [x] Test names no longer bless heuristics as target behavior.

#### Anti-drift notes

- Do not add new content just to make tests easy.
- Do not modify real YAML to hide normalizer bugs.
- Do not use old `data/world_modules` for default proof.

### Task 27.2 — Add real composition integration matrix

#### Objective

Prove real compositions reference and assemble real modules.

#### Expected behavior

Flow:

```text
real composition YAML
→ WorldCompositionNormalizer
→ module repository from data/content/world_modules
→ module resolver
→ merged world contribution
→ WorldSpec + CompileContext
```

#### Test plan

Add:

```text
tests/integration/worldassembly/test_real_content_world_compositions.py
```

Cases:

```text
test_real_composition_loads
test_real_composition_referenced_modules_exist
test_real_composition_assembles_world_bundle
test_real_composition_compile_context_contains_sources
test_real_composition_provenance_deterministic
```

#### Acceptance checklist

- [x] Real composition file loads.
- [x] `modules` shorthand works.
- [x] `module_refs` still works.
- [x] Referenced modules exist in canonical module repository.
- [x] Composition output is deterministic.
- [x] Provenance/fingerprint remains stable.

#### Anti-drift notes

- Do not make composition resolver reach into old paths.
- Do not let unresolved modules silently skip.

### Task 27.3 — Keep provenance deterministic for new path

#### Objective

Ensure the repaired real-file path preserves deterministic provenance.

#### Expected behavior

Provenance includes source records for:

```text
module source
archetype source
population recipe source
biome/ecology source
relationship activation source
compatibility projection source where applicable
```

#### Test plan

Extend existing provenance tests; do not duplicate broad provenance coverage.

Add/update:

```text
test_real_content_composition_provenance_is_deterministic
test_module_v2_path_emits_provenance
test_archetype_expansion_emits_provenance
```

#### Acceptance checklist

- [x] Existing provenance tests still pass.
- [x] New module path emits provenance.
- [x] Archetype expansion emits provenance where implemented.
- [x] Population expansion emits provenance where implemented.
- [x] Provenance output is deterministic.
- [x] EntityState structure is not changed.

#### Anti-drift notes

- Do not embed provenance into EntityState.
- Keep provenance as sidecar unless a future phase explicitly changes it.

---

# Phase 28 — Perspective/relation runtime usage repair

## Phase goal

Prove perspective-derived relationship labels reach at least one real runtime decision without rewriting all old systems.

## Dependencies

```text
- RelationProjectionService exists.
- Compatibility wrapper exists or can be introduced.
- Existing combat/arena regression tests pass.
```

## Tasks

### Task 28.1 — Integrate relation projection into combat target classification

#### Objective

Make relation projection affect one real runtime decision.

#### Problem / current behavior

`RelationProjectionService` can exist and pass unit tests while high-impact runtime still relies on legacy enum/bucket logic.

#### Expected behavior

Combat target classification flow:

```text
source entity
target entity
context
→ identity/faction extraction
→ RelationProjectionService if clean data exists
→ classification label
→ target allowed / not allowed
→ legacy fallback if clean projection unavailable
```

Labels that should classify as hostile/targetable depending on context:

```text
enemy
threat
intruder
prey
```

Labels that should not normally be targetable:

```text
ally
neutral
protected
ignored
```

#### Technical direction

- Add a wrapper around target classification boundary.
- Do not rewrite combat damage or turn resolution.
- Preserve legacy fallback.
- Add debug/source output if available.

#### Affected components

```text
src/content_semantics/relation.py
src/content_semantics/faction.py
combat target selection / classification component
arena/combat tests
```

#### Test plan

Add/update:

```text
test_combat_target_uses_relation_projection_for_clean_data
test_hero_perspective_targets_goblin_as_enemy
test_hero_perspective_does_not_target_merchant_as_enemy
test_wild_beast_contextual_threat_depends_on_context
test_legacy_monster_fallback_still_hostile
```

#### Acceptance checklist

- [x] Combat target classification calls relation projection when clean data exists.
- [x] Legacy fallback still works.
- [x] Clean archetype/faction entity can be classified without `EntityRole.MONSTER`.
- [x] Test verifies runtime classification, not only service output.
- [x] Existing arena/combat tests still pass.
- [x] Projection result includes source relationship/perspective record where available.

#### Anti-drift notes

- Do not rewrite the full combat system.
- Do not remove legacy enum fallback.
- Do not make race the enemy source truth.
- Do not introduce behavior scripts.

### Task 28.2 — Keep compatibility wrapper explicit and report fallback usage

#### Objective

Make fallback visible and intentional.

#### Expected behavior

Compatibility wrapper:

```text
try clean projection
fallback to legacy bucket semantics
report fallback source when debug/reporting is enabled
```

#### Test plan

Add/update:

```text
test_clean_projection_used_when_relationship_data_exists
test_legacy_fallback_used_when_clean_data_missing
test_fallback_usage_reported
test_old_is_hostile_semantics_still_pass
```

#### Acceptance checklist

- [x] Clean projection is attempted first.
- [x] Legacy fallback still works.
- [x] Fallback usage is reportable.
- [x] No direct dependency from clean data to compatibility data.
- [x] Existing semantic tests still pass.

#### Anti-drift notes

- Do not make compatibility path the new source truth.
- Do not hide fallback under normal success logs.

---

# 9. Global test strategy

## Reuse existing tests

Do not duplicate broad coverage already present.

Reuse/extend:

```text
tests/unit/content/test_catalog.py
tests/unit/content/test_layered_catalog.py
tests/unit/content/test_runtime_catalog.py
tests/unit/worldassembly/test_assembly.py
tests/unit/worldassembly/test_provenance.py
tests/unit/content_semantics/test_semantics.py
tests/arena/*
```

## Add new tests only for new responsibility

Add new tests for gaps:

```text
canonical content path config
real world module loading
count-preserving module normalization
real composition integration
typed reference graph edges
registry projection parity
runtime relation classification
```

## Required test categories

```text
Unit:
    schemas
    normalizers
    reference graph
    resolvers
    adapters

Integration:
    real content YAML -> repository -> resolver -> assembly
    catalog -> registry projection
    relation projection -> runtime classification

Regression:
    existing worldassembly tests
    existing provenance tests
    existing arena/combat tests
    existing catalog tests

Architecture guard:
    no comment parsing
    no old path as default
    no new hardcoded gameplay truth in catalog-backed path
```

## TDD workflow

For each task:

```text
1. Add failing test.
2. Implement minimal logic.
3. Confirm existing relevant tests still pass.
4. Add one regression case if old behavior is touched.
5. Avoid broad rewrites.
```

---

# 10. Execution order

Use this order to reduce drift and rework:

| Order | Repair                                             | Reason                                                   |
| ----: | -------------------------------------------------- | -------------------------------------------------------- |
|     1 | Phase 22.3 module normalization count-loss         | Concrete critical bug; can corrupt content meaning.      |
|     2 | Phase 21 canonical content paths                   | Prevents fake migration through old paths.               |
|     3 | Phase 27 real module/composition integration tests | Proves real `data/content` files are executable.         |
|     4 | Phase 23 typed graph and new decision validation   | Keeps comments human-only and validates real references. |
|     5 | Phase 20 matrix evidence strengthening             | Prevents status overclaiming.                            |
|     6 | Phase 26 registry parity and adapter cleanup       | Removes hidden legacy gameplay truth.                    |
|     7 | Phase 25 metadata preservation                     | Prevents archetype data from collapsing too early.       |
|     8 | Phase 28 runtime relation consumer                 | Moves projection from service-only to runtime-used.      |
|     9 | Phase 24 resolver status correction                | Documentation/reporting cleanup once evidence is clear.  |

Note: Phase 24 status correction can be done earlier if it is only report/matrix work, but it must not distract from the critical module/path fixes.

---

# 11. Final definition of done

The Phase 20–28 repair is complete only when:

```text
- YAML comments are human-only and ignored by engine validators.
- ContentUsageMatrix tracks implementation status at family level.
- Runtime-authoritative family claims have evidence tests.
- data/content/world_modules is the default executable module source.
- data/content/world_compositions is the default executable composition source.
- Module normalization preserves resource/building/service counts.
- Real module files load, validate, normalize, graph-check, and resolve.
- Real composition files load and assemble using real modules.
- Reference graph has typed module/composition/scenario edges.
- Registry adapters have parity tests and no hidden normal-mode fallback records.
- Archetype/population metadata survives into compile/assembly sidecar context.
- Relation projection is used by at least one runtime decision.
- Existing legacy/arena/combat/provenance tests still pass unless explicitly updated.
```

## Completion standard for each task

A task is complete only when:

```text
- target behavior is implemented
- required tests are added or updated
- relevant existing tests still pass
- acceptance checklist is fully satisfied
- anti-drift notes were respected
- output evidence is available
```

## Final anti-drift reminder

```text
Do not confuse component existence with implementation completion.
Do not confuse schema validation with runtime usage.
Do not confuse manually injected tests with real content-path proof.
Do not confuse YAML comments with engine state.
Do not confuse compatibility fallback with clean source truth.
```
