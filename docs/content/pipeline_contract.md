---
status: authoritative
layer: systems
authority: P1
audience: agent
last_verified: 2026-06-12
tags: [content, catalog, pipeline, contract]
---

# Content Pipeline Contract

The content pipeline loads static catalog YAML data into a typed, validated in-memory repository before any simulation tick begins. Content state is **read-only** after load — no tick-path code writes to it.

The Compliance ID namespace for this subsystem is **WORLD-CAT-\*** and **WORLD-PATH-\***.  
For semantic defaults see `docs/content/content_semantics_contract.md` (**WORLD-SEM-\***).  
For pack YAML format see `docs/content/content_pack_format.md` (do not duplicate here).

---

## Authoritative Status

**NOT authoritative** — content catalog data is static reference data, not simulation state. It does not participate in the `AuthoritativeState` hash. It is loaded once at startup and consumed read-only by the compiler, resolvers, and world assembly pipeline.

---

## Content Path Layout

Defined in `src/content/paths.py` (WORLD-PATH-001):

| Field | Default path |
|---|---|
| `content_root` | `data/content/` |
| `world_modules_dir` | `data/content/world_modules/` |
| `world_compositions_dir` | `data/content/world_compositions/` |
| `simulation_scenarios_dir` | `data/content/simulation_scenarios/` |

`ContentPathConfig` is a frozen dataclass. All content-loading code must obtain paths from it — never hardcode content paths.

---

## Hot-Path Loading Prohibition (CONTENT-HOTPATH-GUARD)

**`CatalogRepository.load_all()` is forbidden while a kernel tick is executing.**

`Kernel.tick_once()` sets `_tick_context_active.active = True` (thread-local, `src/content/repository.py`) on entry and clears it in a `finally` block. If `load_all()` is called while this flag is set, `ContentHotPathViolation(RuntimeError)` is raised immediately with a descriptive message citing WORLD-CAT-004.

**Prevention**: `Kernel.__init__()` calls `ContentWarmupService.warmup()` after `validate()` to eagerly initialize all content singletons (faction semantics cache, etc.) before the first tick. This guarantees the guard never fires under normal operation.

`ContentWarmupService` (in `src/content/warmup.py`) provides:
- `warmup(repo=None)` — eager singleton initialization
- `is_warm() -> bool` — inspection
- `reset()` — test-only teardown (asserts `pytest` is in `sys.modules`)

---

## Load Pipeline

Entry point: `CatalogRepository.load_all()` (WORLD-CAT-004, WORLD-CAT-005).

Each content family is declared as a `ContentFamilySpec`:

| Field | Purpose |
|---|---|
| `family` | Dotted family name (e.g. `foundation.materials`) |
| `path` | File path relative to `content_root` |
| `schema` | Pydantic model class for validation |
| `repository_index` | Attribute name on CatalogRepository where records are stored |
| `required` | If True, missing file is a load error |
| `state_policy` | `active` or `deprecated` — deprecated families are loaded but flagged |

Load sequence per family:
1. Resolve path via `ContentPathConfig`
2. Read YAML file
3. Validate each record against `schema` (Pydantic — raises on schema violation)
4. Store parsed records in `CatalogRepository.<repository_index>` (dict keyed by record `id`)

All families in `CANONICAL_FAMILIES` are loaded by `load_all()`. Order is deterministic (definition order in the list).

---

## Resolver Layer

Defined in `src/content/resolver.py` (WORLD-CAT-024, WORLD-CAT-025).

Resolvers provide validated, deterministic access to catalog records. They do not run simulation behaviour.

| Resolver | Covers |
|---|---|
| `FoundationResolver` | attributes, materials, traits, themes, elements, relationship axes |
| `LivingResolver` | races, need/sense/body/drive/cognition profiles |
| `SocialResolver` | roles, factions, perspectives, faction relationships |
| `EntityResolver` | stat/combat/inventory/skill profiles, entity archetypes, population recipes |
| `WorldResolver` | resources, buildings, terrain, biomes, ecologies, regions, spawn tables |

**Resolution contract:** Every `resolve_<type>(id)` method raises `ResolverError` if the ID is not in the loaded catalog. `ResolverError` inherits from `KeyError` — callers may catch either.

```
ResolverError(family, missing_id, context="")
  .family      # e.g. "material"
  .missing_id  # the ID that was not found
  .context     # optional caller-provided detail
```

Resolvers are instantiated with a loaded `CatalogRepository`. They hold no mutable state.

---

## Reference Graph Rules

`src/content/reference_graph.py` provides two mappings for cross-reference traversal:

**`FAMILY_TO_SHORT`** — dotted family name → short type name used in cross-reference validation (e.g. `"foundation.materials"` → `"material"`).

**`FIELD_TO_TARGET`** — field name on a definition → expected target type name (e.g. `"species"` → `"species"`, `"compatible_roles"` → `"role"`).

Reference graph rules:
1. Every ID referenced in a definition's cross-reference fields must exist in the catalog under the target family.
2. Missing references are reported as `ValidationIssue(severity="ERROR")` — they block compilation.
3. Cycles in cross-references are not structurally prevented but must not be relied upon for meaning; the reference graph is a DAG for validation purposes.

---

## ContentUsageMatrix

`src/content/matrix.py` tracks implementation status for every content family. It is the single source of truth for content family status — agents must not duplicate this table.

`ContentFamilyMatrixEntry.implementation_state` values:

| State | Meaning |
|---|---|
| `RESOLVED_PARTIALLY` | Loaded into repository and resolvable; not yet consumed by runtime simulation |
| `RUNTIME_AUTHORITATIVE` | Loaded, resolved, and consumed by the live simulation tick path |
| `PROJECTED_TO_LEGACY` | Resolved and projected into a legacy enum value for backward compatibility |
| `DESIGN_ONLY` | Defined in YAML but not yet loaded or validated by any running code |

**Policy (from matrix.py:9-11):** YAML comments (e.g. `# STATE: ...`) are planning notes only. They must never be parsed by validators or the engine. `implementation_state` is the only authoritative status gate.

---

## ContentPackManifest Validation Rules

`src/content/pack_manifest.py` — schema version `content_pack.v1`.

**Hard validation rules (raise `ContentPackValidationError` on failure):**

1. `pack_id` must match `^[a-z][a-z0-9_]*$` — lowercase, starts with letter, underscores only.
2. Pack must have at least one consumer: `sample_compositions` or `sample_scenarios` must be non-empty. Packs with no consumers are rejected (pack_manifest.py:38-44).
3. `dependencies` must list only known `pack_id` values — validated by `ContentPackManifestValidator`.
4. `included_families` keys must be valid family paths (dot-notation or slash-notation).

---

## Catalog Validation (src/content/validator.py)

Compliance IDs: WORLD-CAT-006, WORLD-CAT-007.

`CatalogValidator` runs after `load_all()` and produces a list of `ValidationIssue` records:

- **Semantic cross-reference checks** — every referenced ID exists in the correct family.
- **Dead record detection** — records present in YAML but not referenced by any composition or scenario.
- **Matrix evidence validation** — `validate_matrix_evidence()` verifies that every `ContentFamilyMatrixEntry.evidence_tests` path exists and the evidence is executable.

`CatalogValidationError` is raised if ERROR-severity issues are found.

**`_FAMILY_KEY_OVERRIDES`** (validator.py) maps family paths where the dot-notation key does not match the CONTENT_USAGE_MATRIX key — add overrides there when a new family's key diverges from convention.

---

## Compliance ID Index

| ID | Source file | Line | Description |
|---|---|---|---|
| WORLD-CAT-001 | src/content/schema.py | 1 | CatalogBaseDefinition base schema |
| WORLD-CAT-002 | src/content/schema.py | 1 | Foundation model schema definitions |
| WORLD-CAT-003 | src/content/schema.py | 1 | Living/social/entity/world schema definitions |
| WORLD-CAT-004 | src/content/repository.py | 1 | CatalogRepository load contract |
| WORLD-CAT-005 | src/content/repository.py | 1 | ContentFamilySpec declaration contract |
| WORLD-CAT-006 | src/content/validator.py | 1 | CatalogValidator semantic rules |
| WORLD-CAT-007 | src/content/validator.py | 1 | Dead record and matrix evidence validation |
| WORLD-CAT-024 | src/content/resolver.py | 1 | Foundation/living/social resolver contract |
| WORLD-CAT-025 | src/content/resolver.py | 1 | Entity archetype and population resolver contract |
| WORLD-PATH-001 | src/content/paths.py | 1 | ContentPathConfig canonical path layout |
