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

## 4. Integrity Validation Laws
Before any spec can compile into an `AuthoritativeState`, it must satisfy three levels of validation:

```
  YAML File
      │
      ▼ (Level 1: Schema Check)
  Pydantic Validation
      │
      ▼ (Level 2: Structural Check)
  Spatial & Link Verification
      │
      ▼ (Level 3: Runtime Compiler)
  Deterministic Initialization
```

### Validation Levels
1.  **Level 1: Schema Validation**: Checks for basic key presence, format correctness, and value ranges using Pydantic.
2.  **Level 2: Semantic Integrity**: Validates spatial alignment (e.g. regions within world bounds) and referential integrity (e.g. population groups referencing valid regions and factions).
3.  **Level 3: Compilation Completeness**: Confirms that initial entity counts satisfy the requested configuration thresholds (e.g., minimum total entities).

---

## 📜 Compliance Status
All chapters are currently **Certified Level 1 (Authoritative)**. This means the documentation matches the current source code implementation as of Tick 0 of the V2 Engine deployment.
