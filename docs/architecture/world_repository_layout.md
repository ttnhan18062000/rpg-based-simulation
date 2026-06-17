---
status: active
layer: architecture
authority: P1
audience: developer
---

# World Repository Layout and WorldCompositionSpec Discovery

## Status
ACCEPTED

## Context
With the introduction of the new module-based world assembly system, we are introducing a new source schema called `worldcomposition.v1`. We must decide where these source files live, how they are indexed by the repository layer, and where resolved compiler-ready artifacts are output.

## Proposed Strategy & Layout

### 1. Unified Directory Layout
Rather than creating separate directories for raw templates, specs, and compositions, we will maintain the existing unified world repository root at `data/worlds/`. Each world scenario is identified by its unique folder name under `data/worlds/<world_id>/`.

The root source file inside a world folder is always `world.yaml`. The schema version within the YAML determines how the repository indexes it.

```text
data/worlds/<world_id>/world.yaml
```

The file's top-level `schema_version` field can be one of:
- `worldspec.v1`: Legacy direct specification (compiler-ready).
- `worldtemplate.v1`: Legacy template requiring procedural expansion.
- `worldcomposition.v1`: New module-based composition manifest.

### 2. Discovered Artifact Output Separation
To prevent pollution of the source file, a composition source (`worldcomposition.v1`) is NEVER passed directly to the `WorldCompiler`. Instead, the `WorldAssemblyResolver` processes the composition and outputs a fully resolved compiler-ready specification and its supporting sidecars.

The resolved files must be written to a dedicated `resolved/` sub-directory within the world directory:

```text
data/worlds/<world_id>/resolved/world.resolved.yaml    # Normalized worldspec.v1 output
data/worlds/<world_id>/resolved/provenance_manifest.json # Audit trail metadata
data/worlds/<world_id>/resolved/assembly_report.json    # Phase-by-phase resolution log
data/worlds/<world_id>/resolved/validation_report.json  # Schema and context validation results
data/worlds/<world_id>/resolved/compile_report.json     # Final compiler output logs
```

### 3. Backwards Compatibility
All existing tools, scripts, and tests that load `worldspec.v1` and `worldtemplate.v1` from `data/worlds/<world_id>/world.yaml` must remain fully supported and unaltered. When a direct compile request is made for a scenario whose source is `worldcomposition.v1`, the repository loader will direct the caller to locate the compiler input from the `resolved/world.resolved.yaml` artifact instead of the source `world.yaml`.
