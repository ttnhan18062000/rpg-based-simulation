# Investigation: Provenance Manifest and Report Integration (Phase 7)

## Codebase Analysis

Currently:
- `ProvenanceManifest` is a small placeholder Pydantic model at `src/worldassembly/resolver.py` storing:
  - `world_id`
  - `catalog_fingerprint`
  - `module_fingerprints`
  - `entity_origins`

We will fully scale this up to the `provenancemanifest.v1` spec as defined in the Phase 7 roadmap. 

## Architectural Constraints

1. **Sidecar only**: We must ensure no fields are added to `EntityState` or any active runtime simulation loops; all metadata remains sidecar-only in the resolver package.
2. **Determinism**: Since the manifest matches structural elements using Pydantic, the fingerprints and UUID/IDs must be calculated deterministically so compiling the same composition twice yields identical manifest files.
3. **Pydantic mapping**: By declaring the models in `src/worldassembly/schema.py`, we prevent imports pollution and keep schemas localized.
