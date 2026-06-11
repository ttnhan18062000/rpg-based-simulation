---
status: authoritative
layer: core
authority: P0
audience: developer
last_verified: 2026-06-06
---

# Authoritative State Architecture

> [!IMPORTANT]
> **Immutability Law**: All state components and the `AuthoritativeState` container are `frozen=True` dataclasses. State transitions must produce a *new* state object. Mutation of existing objects is strictly forbidden and enforced via `ReadOnlyDict`.

## The State Container (`AuthoritativeState`)

The `AuthoritativeState` is the singular, immutable source of truth for the entire simulation. It is composed of highly-granular components, enabling efficient "shallow-copy" transitions.

### Key Components

| Component | Responsibility | Key Fields |
| :--- | :--- | :--- |
| **Identity** | Core identification and factional ties. | `entity_id`, `faction`, `role`, `learned_skills`. |
| **Combat** | Tactical status and health. | `hp`, `readiness`, `alive`, `wounds`, `scars`. |
| **Navigation** | Spatial position and movement intent. | `position`, `target`, `path`, `movement_mode`. |
| **Strategic** | Long-term mental state and objectives. | `projects`, `blockers`, `leads`, `concerns`. |
| **Inventory** | Item and resource ownership. | `gold`, `items`, `max_slots`. |
| **Biological** | Resource pressures and survival needs. | `sleep_debt`, `hunger`, `rest_pressure`. |
| **Lifecycle** | Aging, death, and heredity. | `age_ticks`, `generation`, `heirlooms`. |

---

## The "Frozen Lifecycle" Law

1. **Snapshotting**: Systems read a frozen `AuthoritativeState`.
2. **Deliberation**: Workers (Concurrent) generate `StateUpdate` proposals.
3. **Refinement**: The `AuthoritativeApplyPipeline` resolves proposals into a single `StateUpdate`.
4. **Transition**: `AuthoritativeState.apply(update)` produces the state for the *next* tick.

## Component Composition Pattern

Instead of a monolithic entity class, entities are composed of discrete, typed components.
- **Benefits**: Improved memory locality, deterministic serialization, and isolated logic domains.
- **Dependency Map**:
    - `Combat` depends on `Attributes` for max HP.
    - `Navigation` depends on `Combat` for move speed.
    - `Strategic` depends on `Navigation` for reaching leads.

### 🧩 Component Anatomy
Each component is a `@dataclass(frozen=True, slots=True)`. This ensures:
1. **No-Mutation**: Values cannot be changed after creation.
2. **Memory Efficiency**: `__slots__` significantly reduces the memory footprint of millions of components.
3. **Thread Safety**: Frozen objects are inherently safe to share across concurrent workers.

---

## Serialization & Canonical Truth

To ensure that state snapshots can be shared across machines or saved to disk, every component implements the `to_canonical_dict()` protocol.

### 📜 The Canonical Protocol
- **Determinism**: Dictionaries are always sorted by key during serialization.
- **Efficiency**: A hidden `_canonical_cache` stores the serialized result to avoid redundant work.
- **Comparison**: Two `EntityState` objects are considered bit-identical if their canonical dictionaries are identical.

## Regional State & Trauma
The world is divided into **Regions**, each with its own:
- **Hazard Level**: Affects resource drain.
- **Trauma Score**: Persistent 'scars' on the world from battles or raids.
- **Influence**: A floating-point value tracking the balance of power between Factions.
- **Suppression**: Regional laws that block specific worker actions (e.g., "No Sabotage").

---

## Performance & Optimization
- **Shallow Copying**: State transitions use `replace()` to only copy the components that actually changed.
- **Zero-Allocation ReadOnly Caching**: To prevent massive allocation overhead when workers access state collections (`entities`, `buildings`, `quests`, `items`, `factions`), `AuthoritativeState` maintains immutable cached `ReadOnlyDict` proxy views. These cached wrappers are reused across all property reads and are only invalidated when an authoritative state transition replaces the underlying collection reference. This reduces view generation overhead from O(N) to O(1) (sub-microsecond access).
- **Fingerprinting**: The `AuthoritativeState.fingerprint()` method provides a high-speed SHA-256 hash of the entire world for stability verification.
