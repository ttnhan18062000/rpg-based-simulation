---
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-06-27
---

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
To build complex worlds dynamically from multiple modular specs and template dependencies, the engine employs a deterministic declarative assembly pipeline.

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
For complete traceability, every successfully compiled world state outputs a sidecar `provenance_manifest.json` file. This is the cornerstone of engine observability.

### Provenance Tracking
*   **Sidecar Structure**: The provenance manifest contains detailed metadata maps tracking the origin of every compiled asset:
    *   **Entity Lineage**: Links unique entity IDs back to their parent population ID (`pop_key`) and generator rule.
    *   **Spatial Provenance**: Maps regions, buildings, and resource nodes to their source module specs, templates, and content catalog profiles.
*   **Late-Binding Telemetry Joins**: During post-run analysis, the `ProvenanceLookupService` reads the sidecar manifest to join static declaration origins with dynamic database records (such as ClickHouse run logs).
*   **Lineage Querying**: Analysts can invoke `ProvenanceLookupService.get_entity_origin` to pinpoint exactly which modular spec or catalog configuration was responsible for a specific entity performing a runtime action, completing the feedback loop between design-time specifications and runtime behavior.

---

---

## 9. Content Catalog Database Structure (data/content/)
The Content Catalog represents the authoritative, layered static database defining all core entities, attributes, and physics laws of the simulation. It is partitioned logically into directories under `data/content/`:

### Layer 1: Foundation (`foundation/`)
Defines the absolute constants of the simulation environment:
*   **Attributes**: Base attributes (strength, intelligence, physical limits) that scale entity progress.
*   **Elements**: Damage and affinity elements (physical, fire, magic).
*   **Materials**: Static physical properties of materials used in crafting and structures.
*   **Traits & Themes**: Static entity perks/flaws and aesthetic regional themes.

### Layer 2: Living (`living/`)
Defines biological and physiological configurations:
*   **Races**: Biological base templates.
*   **Body Models**: Structural slot mapping for items and armor.
*   **Profiles**: Need profiles (food, sleep), Sense profiles (sensory range), Drive profiles, and Cognition profiles governing bounded AI strategic intelligence.

### Layer 3: Social & Factions (`social/`)
Defines group mechanics and social alignments:
*   **Factions**: Faction identifiers, starter vaults, and configurations.
*   **Faction Relationships**: Initial diplomatic scores and modifiers.
*   **Roles & Perspectives**: Regional jobs/roles and factional alignment bias.

### Layer 4: Entity Archetypes (`entities/`)
Defines the blueprints for all NPC populations and creatures:
*   **Entity Archetypes**: Base NPC templates (warrior, wolf, merchant) linking to specific races and factions.
*   **Profiles**: Stats scaling profiles, Combat capability profiles, starting Inventory profiles, and Skill profiles.

### Layer 5: World & Economy (`world/`)
Defines items, structures, and regional ecologies:
*   **Items & Recipes**: The item database and crafting recipe requirements (gold cost, inputs, outputs, services).
*   **Terrain, Biomes, & Ecologies**: Topographical tile properties, biome templates, and creature population densities.
*   **Buildings & Services**: Structural blueprints and settlement affordances (craft, rest, trade).

---

## 📜 Compliance Status

| Chapter | Status | Last Action |
|---|---|---|
| 01 Entity Anatomy | Verified | Corrected: hunger threshold 95.0/+2dmg, sleep debt 98.0/+1dmg (TCK-20260619-P0-DOC-REPAIR) |
| 02 Combat Laws | Verified | Confirmed: COVER_REDUCTION=0.30, BOND_SYNERGY_BONUS=0.10 (TCK-20260627-P3C-DOC-CURRENCY) |
| 03 Economic Laws | Verified | Corrected: weight limit 50.0 kg, selling formula static 50% (TCK-20260627-P3C-DOC-CURRENCY) |
| 04 Strategic Cognition | Verified | Corrected: interruption formula uses resistance_multiplier (TCK-20260619-P0-DOC-REPAIR); blocker kinds, perception radius 10.0, info decay 50 ticks (TCK-20260627-P3C-DOC-CURRENCY) |
| 05 World Evolution | Partially verified | 2 uncertain claims remain: resource respawn interval, trauma delta per death (not traced to source) |
| 06 Worldbuilding Foundation | Verified | Structural claims confirmed (TCK-20260619-P0-DOC-REPAIR, TCK-20260627-P3C-DOC-CURRENCY) |

Chapters 01–04 and 06 are **Certified Level 1 (Authoritative)** as of 2026-06-27. Chapter 05 is **Partially Verified** — structural mechanics confirmed, 2 numeric constants unverified against source.
