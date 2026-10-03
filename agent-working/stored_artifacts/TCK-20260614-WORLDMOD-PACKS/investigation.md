---
ticket_id: TCK-20260614-WORLDMOD-PACKS
phase: investigation
---

# Investigation: Content Pack Dependency Validation at Assembly Time

## Findings

### `WorldCompositionSpec` (src/worldassembly/schema.py)

- Has `catalog_refs: List[str]` for catalog family paths — NOT for pack IDs.
- Has `module_refs: List[ModuleRefSpec]` for module assembly.
- `NormalizedWorldComposition` mirrors the spec but strips the `modules` shorthand.
- Both models use `ConfigDict(frozen=True, extra="forbid")` — must add `pack_refs` as a proper Pydantic field.
- `WorldCompositionNormalizer.normalize()` converts spec → normalized. Pack validation should occur before normalization uses the composition, so it fires on the raw spec.

### `WorldAssemblyResolver.assemble()` (src/worldassembly/resolver.py)

- Accepts `WorldCompositionSpec | dict`.
- First call is `WorldCompositionNormalizer.normalize(composition)`.
- Pack validation must be inserted between normalization and `enabled_refs` collection.
- To extract `pack_refs` from both dict and spec forms: check `isinstance(composition, WorldCompositionSpec)` vs dict.
- `AssemblyPackError` should live near the top of `resolver.py` with other exception-like classes (`AssemblyParameterError` is already imported from elsewhere).

### `ContentPackManifest` / `ContentPackManifestValidator` (src/content/pack_manifest.py)

- `ContentPackManifest` is a Pydantic model with: `pack_id`, `enabled`, `dependencies`, `included_families`, `sample_compositions`, `sample_scenarios`.
- `enabled: bool = True` — the field to check.
- `dependencies: List[str]` — list of pack IDs that must also be present and enabled.
- `ContentPackManifestValidator.validate(manifest, known_packs)` returns a list of error strings.
- For our use case: we load the manifest via `ContentPackManifest.model_validate(yaml_data)` and check `enabled` and `dependencies` manually (the validator is for cross-pack registry checks, not the per-pack enabled gate).

### Pack YAML files (`data/content/packs/`)

Two packs exist:
- `frontier_extended_pack.yaml` — `enabled: true`, `dependencies: []`
- `swamp_border_pack.yaml` — `enabled: true`, `dependencies: []`

Both have `sample_compositions` or `sample_scenarios` so they pass the consumer validation rule.

### Existing exception classes

- `AssemblyParameterError` imported from `src/worldmodules/evaluator.py`.
- `ResolverError` from `src/content/resolver.py`.
- We define `AssemblyPackError(ValueError)` in `resolver.py` to be consistent with existing naming conventions in that module.

### Impact on existing tests

- `WorldCompositionSpec` with `extra="forbid"` means adding a new field with a default is additive and safe.
- Existing YAML compositions without `pack_refs` will default to `[]` and skip validation — no breaking change.
- `NormalizedWorldComposition` intentionally does NOT get `pack_refs` (pack validation is assembly-gate, not carried into compilation context).

## No conflicts found

- No existing code uses `pack_refs`.
- No ticket in `tickets/done/` or `tickets/inprogress/` addresses this.
- `catalog_refs` is completely untouched.
