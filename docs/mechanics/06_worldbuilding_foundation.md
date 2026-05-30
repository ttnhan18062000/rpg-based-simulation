# Chapter 6: Worldbuilding Foundation

This chapter describes the "Structural Laws" governing the definition, validation, and compilation of world topologies, regions, factions, and entities from file-based declarations into runtime simulation states.

---

## 1. Declarative World Topology
Worlds are declared using the stable `WorldSpec` schema format, which decouples static definitions from the simulation state. The topology represents a discrete coordinate space.

### Topology Constraints
*   **Coordinate Bounds**: Must be defined using a 2D rectangular grid system.
*   **Dimensional Minimums**: Height and width must be integers greater than or equal to `1`.
*   **Coordinate System**: Currently strictly locked to `"grid"` to ensure deterministic boundaries.

---

## 2. Regional Boundaries & Sovereignty
Regions partition the world topology into distinct logical zones.

### Spatial Laws
*   **Bounds Definition**: Defined as `[min_x, min_y, max_x, max_y]`.
*   **Boundary Validity**: The minimum bounds must always be less than or equal to the maximum bounds (`min_x <= max_x` and `min_y <= max_y`).
*   **Topology Alignment**: All region boundaries must lie entirely within the world's topology dimensions.
*   **Overlap Policy**: By default, regional bounds are strictly disjoint (no overlapping). This is enforced unless `allow_overlapping_regions` is explicitly enabled in the validation spec.

---

## 3. Entity & Resource Distribution
The schema governs the initial distribution of all populations, resources, and structures.

### Spawn & Resource Rules
*   **Factions**: Factions must have a unique ID and type declared in the spec.
*   **Populations**: Population groups define initial entities, including counts, roles, factions, and spawn regions. Count must be a non-negative integer.
*   **Resource Nodes**: Depict the starting locations of gatherable items. Resource count must be greater than or equal to `1`.
*   **Buildings**: Represents the architectural foundation of settlement hubs within designated regions.

---

## 4. Kahn's Topological Sort Assembly
To build complex worlds dynamically from multiple modular specs and template dependencies, the V2 Engine employs a deterministic declarative assembly pipeline.

### Dependency Resolution
*   **Dependency DAG**: Factions, regions, populations, and structures are modeled as nodes in a Directed Acyclic Graph (DAG), where edges represent structural and referential dependencies (e.g., population groups relying on faction definitions and target regions).
*   **Assembly Order**: The pipeline uses **Kahn's Topological Sort Algorithm** to resolve dependencies. If a cycle is detected, assembly aborts immediately with a structural compilation error, preventing infinite loops or partial/unstable initializations.
*   **Deterministic Evaluation**: The topological sort guarantees a repeatable, identical ordering of assembly steps across all runs with the same input seed and specs.

---

## 5. Budget-Bounded Procedural Intent Specs
Procedural generation and dynamic expansion specs are bounded by hard, checkable budget guardrails to prevent unchecked entity bloat or starvation.

### Guardrail Laws
*   **Intent Specifications**: Procedural rules define target entity bounds, spawn weights, and distribution strategies rather than exact coordinate lists.
*   **Point-Buy & Resource Budgets**: Spawning and construction actions must consume points from a regional or faction-wide budget pool.
*   **Hard Bounds Checking**: During compilation and dynamic generation ticks, the engine validates that the sum of generated entities and structures does not exceed the predefined maximum thresholds established in the procedural budget intent spec.

---

## 6. Dynamic Compiler Overrides & CompileContext
The compiler supports late-binding overrides during the compilation phase to allow dynamic adjustments without mutating the underlying static schemas.

### Compilation Context Laws
*   **Context Injection**: The `WorldCompiler.compile` pipeline consumes an optional `CompileContext` container.
*   **Dynamic Overrides**: `CompileContext` contains maps for dynamic adjustments, including:
    *   **Entity Stats**: Dynamic HP, Attack, Defense, and starting inventory overrides based on target level or scenario parameters.
    *   **Resource Node Settings**: Custom harvest tick durations and yield scales.
    *   **Building Attributes**: Custom durability scales and faction ownership gates.
*   **No-Context Fallbacks**: To ensure perfect backward-compatibility, if no `CompileContext` is supplied, the compiler seamlessly falls back to standard schema-defined defaults (e.g., 100 HP for standard entities, 10 harvest ticks for resources, and 500 HP for buildings).

---

## 7. Integrity Validation Laws & Severity Gates
Before any spec can compile into an `AuthoritativeState`, it must satisfy multiple levels of validation under strict severity gates.

```
  YAML File / Modular Specs
      │
      ▼ (Level 1: Schema Check)
  Pydantic Validation
      │
      ▼ (Level 2: Structural Check)
  Spatial & Link Verification (DAG Cycle Detection)
      │
      ▼ (Level 3: Runtime Gated Compiler)
  Dynamic CompileContext Overrides & Budget Bounds
      │
      ▼ (Verification & Output)
  Deterministic Assembly & Provenance Manifest Sidecar
```

### Severity Gates
Validation rules are categorized into dynamic severity levels to allow flexible environment gating:
*   **ERROR**: Critical failures (e.g., topological cycles, out-of-bounds spatial overlaps, missing key dependencies) that abort the compilation pipeline immediately.
*   **WARNING**: Non-critical inconsistencies (e.g., sub-optimal resource density, unpopulated faction starting vaults) that are logged for developer visibility but do not halt compilation.
*   **Gating Profiles**: Production compilation profiles elevate warnings to errors, whereas development/procedural-testing profiles operate under relaxed warning tolerance.

---

## 8. Sidecar Provenance Manifests & Telemetry Joins
For complete traceability, every successfully compiled world state outputs a sidecar `provenance_manifest.json` file. This is the cornerstone of V2 observability.

### Provenance Tracking
*   **Sidecar Structure**: The provenance manifest contains detailed metadata maps tracking the origin of every compiled asset:
    *   **Entity Lineage**: Links unique entity IDs back to their parent population ID (`pop_key`) and generator rule.
    *   **Spatial Provenance**: Maps regions, buildings, and resource nodes to their source module specs, templates, and content catalog profiles.
*   **Late-Binding Telemetry Joins**: During post-run analysis, the `ProvenanceLookupService` reads the sidecar manifest to join static declaration origins with dynamic database records (such as ClickHouse run logs).
*   **Lineage Querying**: Analysts can invoke `ProvenanceLookupService.get_entity_origin` to pinpoint exactly which modular spec or catalog configuration was responsible for a specific entity performing a runtime action, completing the feedback loop between design-time specifications and runtime behavior.

---

## 📜 Compliance Status
All chapters are currently **Certified Level 2 (Authoritative V2)**. This means the documentation matches the current source code implementation as of Tick 0 of the V2 Engine deployment, including full declarative assembly, context-aware compilers, and post-run observability joins.
