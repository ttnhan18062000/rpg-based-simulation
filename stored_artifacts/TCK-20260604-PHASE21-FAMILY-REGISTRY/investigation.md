---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260604-PHASE21-FAMILY-REGISTRY
artifact_type: investigation
tags: [phase21, family, registry]
---

# Investigation: Content Family Registry & Strict Load Report

## Requirements
1. **Central registry**:
   Create a structure describing each content family:
   ```python
   ContentFamilySpec(
       family="entities.entity_archetypes",
       path="entities/entity_archetypes.yaml",
       schema=EntityArchetypeDefinition,
       repository_index="entity_archetypes",
       required=True,
       state_policy="active",
   )
   ```
2. **Dynamic load pipeline**:
   `CatalogRepository.load_all(strict=False)` (or a strict-mode setting) should walk the registry and load files, checking for:
   - Missing required files.
   - Optional missing files (just reported).
   - Ignored files/unknown extra files.
   - Duplicate family paths.
   - Schema errors during Pydantic parsing.
3. **Load report**:
   Return or store a diagnostic report:
   ```text
   loaded_families: list[str]
   loaded_files: list[str]
   record_counts: dict[str, int]
   missing_required_files: list[str]
   missing_optional_files: list[str]
   ignored_files: list[str]
   duplicate_ids: list[str]
   schema_errors: dict[str, str]
   fingerprint: str
   ```
4. **Existing validation compatibility**:
   Ensure existing tests still pass.

## Refactoring CatalogRepository
Currently:
```python
    def load_all(self) -> None:
        self.materials = self._load_file("foundation/materials.yaml", MaterialDefinition)
        # ...
```
We want to change this to:
```python
    def load_all(self, strict: bool = False) -> CatalogLoadReport:
        # Loop over CANONICAL_FAMILIES
        # Track loaded files, missing, counts, schema errors
        # If strict and missing_required_files: raise ValueError
        # Compute fingerprint
```
Wait, is `strict` enabled by default? Let's check:
"Unknown declared required family fails in strict mode. Missing required files fail in strict mode."
If we add a `strict: bool = False` keyword argument to `load_all(self, strict: bool = False)` (or a field on repository), it will be fully backward-compatible since existing calls without arguments will run with `strict=False` (or we can set default to `False` to prevent breaking existing tests/loaders, and pass `strict=True` in strict tests).
Wait, what are "ignored files"?
If a file exists under `data/content/` (excluding gitkeeps, and maybe some folders) but is NOT declared in any `ContentFamilySpec`, it is an "ignored file" or "unknown extra file".
We should scan `data/content/` for all `.yaml`/`.yml` files and compare them with the registered paths to populate `ignored_files`.
Let's list all files in `data/content/` during loading to find unknown files.
