---
ticket_id: TCK-20260614-WORLDMOD-PACKS
phase: plan
---

# Plan: Content Pack Dependency Validation at Assembly Time

## Step 1: Add `pack_refs` field to `WorldCompositionSpec`

**File:** `src/worldassembly/schema.py`

Add after the existing `catalog_refs` field (line 30), before `module_refs`:

```python
pack_refs: List[str] = Field(default_factory=list, description="Content pack IDs required by this composition (validated at assembly time)")
```

Constraint: `catalog_refs` is NOT modified. The new field is purely additive.

`NormalizedWorldComposition` does NOT need `pack_refs` — pack validation runs on the raw `WorldCompositionSpec` before normalization so the normalized form stays clean.

## Step 2: Define `AssemblyPackError` in `src/worldassembly/resolver.py`

Add after the existing imports, near the top of the file (before `ResolvedWorldBundle`):

```python
class AssemblyPackError(ValueError):
    """Raised when a composition references a pack that is missing or disabled."""
```

## Step 3: Add pack validation at the START of `WorldAssemblyResolver.assemble()`

Immediately after `normalized_comp = WorldCompositionNormalizer.normalize(composition)` and before the `enabled_refs` collection line.

Logic:
1. If `composition` is a `dict`: extract `pack_refs` from it. If `composition` is a `WorldCompositionSpec`: use `composition.pack_refs`.
2. If `pack_refs` is empty: skip validation entirely (no breaking change).
3. For each `pack_id` in `pack_refs`:
   a. Try to load `data/content/packs/<pack_id>.yaml` using `yaml.safe_load` + `ContentPackManifest.model_validate`.
   b. If `FileNotFoundError`: raise `AssemblyPackError(f"Pack '{pack_id}' not found")`.
   c. If `manifest.enabled == False`: raise `AssemblyPackError(f"Pack '{pack_id}' is disabled")`.
   d. For each `dep` in `manifest.dependencies`:
      - Try to load `data/content/packs/<dep>.yaml` the same way.
      - If missing: raise `AssemblyPackError(f"Pack '{pack_id}' requires pack '{dep}' which is disabled")`.
      - If `dep_manifest.enabled == False`: raise `AssemblyPackError(f"Pack '{pack_id}' requires pack '{dep}' which is disabled")`.

Imports needed at top of `resolver.py`:
- `import yaml` (add to existing imports)
- `from pathlib import Path` (add if not present)
- `from src.content.pack_manifest import ContentPackManifest, ContentPackManifestValidator`

## Step 4: Create `tests/unit/worldassembly/test_pack_validation.py`

Four tests using `unittest.mock.patch` to mock file loading:
1. `test_disabled_pack_raises_assembly_pack_error` — disabled pack raises `AssemblyPackError` with pack_id in message
2. `test_missing_pack_raises_assembly_pack_error` — missing manifest (FileNotFoundError) raises `AssemblyPackError` with pack_id
3. `test_unsatisfied_dependency_raises_assembly_pack_error` — pack with a dependency that is disabled raises `AssemblyPackError` naming the dependency
4. `test_empty_pack_refs_passes_without_error` — empty `pack_refs` skips all validation and does not raise

## Step 5: Extend integration test

Add to `tests/integration/worldassembly/test_real_content_world_compositions.py`:
- A test using `frontier_extended_pack` (which exists in `data/content/packs/`) mocked as disabled, verifying `AssemblyPackError` is raised.

## Key Constraints

- Do NOT modify `catalog_refs` handling anywhere.
- `assemble()` accepts both `WorldCompositionSpec` and `dict` — pack_refs extraction must handle both forms.
- Use `ContentPackManifest.model_validate` for loading (matches existing API).
- Pack manifests at `data/content/packs/<pack_id>.yaml`.
