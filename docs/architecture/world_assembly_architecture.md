---
status: active
layer: architecture
authority: P1
audience: developer
---

# World Data Refactor and Assembly Boundaries

## Status
ACCEPTED

## Context
As the simulation matures, we are introducing a robust, module-based World Assembly platform. To prevent architectural drift, spaghetti dependencies, and runtime pollution, we must establish strict, non-negotiable boundaries.

## Architecture Boundaries & Package Ownership

We define the package structure and responsibility domains as follows:

- **`src/content`**
  - *Responsibility*: Static reusable content definitions and catalog schemas (YAML definitions of factions, roles, spawn pools, profiles, etc.).
  
- **`src/content_semantics`**
  - *Responsibility*: Code-based interpretation and semantic translation of catalog concepts (e.g. hostility calculations, query APIs for faction alignments, role capabilities).
  - *Constraint*: Must not execute any runtime simulation ticks, nor store mutable runtime state.
  
- **`src/worldmodules`**
  - *Responsibility*: Reusable structural world module definitions, schemas, and repository layer.
  
- **`src/worldassembly`**
  - *Responsibility*: Resolving compositions, executing `CompileProfileResolver` to bind profiles to templates, creating `ResolvedWorldBundle` containing clean `worldspec.v1`, and generating provenance sidecar manifests.
  - *Constraint*: Home of the `CompileProfileResolver` which maps catalog/profile/recipe references to fully resolved spec configurations.
  
- **`src/worldbuilding`**
  - *Responsibility*: Existing concrete `WorldSpec` schema definitions, catalog-independent world repository, compiler boundary, and compiler-level validators.
  - *Constraint*: Must remain agnostic to module composition, catalog details, or procedural generation modes.
  
- **`src/worldgen`**
  - *Responsibility*: Optional procedural generation or layout expansion algorithms.
  - *Constraint*: Must execute only after the structural assembly resolver has successfully run, or as an optional procedural generation pipeline step.
  
- **`src/engine`**
  - *Responsibility*: Deterministic execution of simulation rules, combat phases, policies, tick loop, and economic systems.
  - *Constraint*: Must NOT know anything about how the world was generated or assembled.

## Forbidden Dependency Paths

To keep modules highly cohesive and loosely coupled, the following dependency rules are strictly frozen:
1. `src/engine` must never import from `src/worldgen`.
2. `src/engine` must never import from `src/worldmodules`.
3. `src/core` must not depend on world generation, modules, or composition layers.
4. `WorldCompiler` must never receive a `WorldCompositionSpec` directly. It must only ever receive a clean, validated `worldspec.v1`.
5. `WorldCompiler` must never directly load catalog files or module files.
6. `worldspec.v1` must remain clean and strictly compiler-compatible. Enriched or procedural metadata (e.g. tracking which generator or module produced an entity) must live in a separate sidecar artifact, never directly polluting `worldspec.v1`.
7. Provenance metadata is stored exclusively in a sidecar `ProvenanceManifest` (JSON/YAML) and must never be added directly to the core runtime `EntityState`.

## CompileProfileResolver Placement
`CompileProfileResolver` is placed under `src/worldassembly` because its role is to translate catalog and profile references within recipes and templates into concrete, compiler-ready values before compilation begins. This ensures `src/worldbuilding/compiler.py` remains focused solely on converting valid specifications into initial simulation states.
