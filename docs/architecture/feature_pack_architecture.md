---
status: authoritative
layer: architecture
authority: P1
audience: agent
---

# Feature Pack Architecture

**Status**: AUTHORITATIVE — E63A complete (gate verified, registry architecture defined).
**Tickets**: E63A (gate verify + registry architecture design).
**Implementation**: E63B (models), E63C (registry + loader + demo), E63D (balance + parity).

---

## Purpose

The Feature Pack system allows new quest types, world behaviors, and faction mechanics
to be added to the engine by dropping in a YAML manifest + Python module — without
modifying any file in `src/engine/` or `src/domains/`.

This generalizes the proven `enum → generator → scorer → mapper → tests` extension
pattern (used in adventure routing and world emergence) into a self-describing,
dependency-aware manifest system.

**Gate condition satisfied:** ≥3 independent features proven via existing extension
patterns; E53A–D (faction diplomacy at scale), E61 (progression), E62 (culture drift)
all complete. See `stored_artifacts/TCK-20260619-E63A-GATE-VERIFY/gate_verification_memo.md`.

---

## 1. FeaturePackManifest YAML Schema

A feature pack is declared by a YAML file at `content/packs/{pack_name}/manifest.yaml`.

```yaml
# content/packs/demo_escort_pack/manifest.yaml
name: demo_escort_pack
version: "1.0.0"
requires:
  - base  # every pack implicitly requires "base"
  # Additional pack dependencies by name
extension_points:
  - domain: adventure_routing
    class: demo_escort_pack.routes:EscortDignitaryGenerator
    registry_key: ESCORT_DIGNITARY
  - domain: adventure_routing
    class: demo_escort_pack.routes:EscortDignitaryScorer
    registry_key: ESCORT_DIGNITARY
balance_specs:
  - id: escort_pack_caution_baseline
    metric_path: motivation.caution_multiplier
    baseline_pack: base
    threshold: 0.1      # mean difference must exceed this
    tolerance: 0.05     # ± tolerance around threshold
```

### Schema Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | str | yes | Unique pack identifier (snake_case) |
| `version` | str | yes | Semantic version string |
| `requires` | list[str] | no | Dependency pack names (loaded before this pack) |
| `extension_points` | list[ExtensionPoint] | no | Domain registrations |
| `balance_specs` | list[BalanceExperimentSpec] | no | Declarative balance assertions |

### ExtensionPoint Fields

| Field | Type | Description |
|---|---|---|
| `domain` | str | Target domain: `adventure_routing`, `world_emergence`, `faction`, `narrative` |
| `class` | str | `module_path:ClassName` import path |
| `registry_key` | str | Key under which the class is registered in the domain registry |

---

## 2. RuntimeProfile Contract

`RuntimeProfile` selects which packs are active for a given simulation run.

```python
@dataclass(frozen=True)
class RuntimeProfile:
    active_pack_names: Tuple[str, ...]  # in declaration order; resolved to load order by CompatibilityResolver
```

**Storage**: `SimulationScenarioDefinition.runtime_profile: Optional[RuntimeProfile]`.
When `None`, the implicit profile is `RuntimeProfile(active_pack_names=("base",))`.

**Determinism**: The resolved load order (from `CompatibilityResolver.resolve()`) is
recorded in the scenario manifest at boot. Two runs with identical profiles and pack
versions produce identical load orders.

### Load Order Rules

1. `base` is always loaded first.
2. Dependencies are loaded before dependents.
3. Within the same dependency level, packs are loaded in lexicographic order of name.
4. Circular dependencies are a hard error (detected by `CompatibilityResolver`).

---

## 3. CompatibilityResolver Contract

`CompatibilityResolver.resolve(manifests) -> List[FeaturePackManifest]`

Returns pack manifests in resolved load order. Raises `PackDependencyError` on circular
dependencies or missing required packs.

### Algorithm

1. Build dependency graph: `{pack_name: set(requires)}`.
2. Topological sort via Kahn's algorithm (BFS).
3. Cycle detection: any node remaining after BFS → `PackDependencyError`.
4. Version constraint check: each `requires` entry may optionally specify `>=version`.
   If specified, the loaded pack's version must satisfy the constraint.

### Error Types

| Error | Condition |
|---|---|
| `PackDependencyError` | Circular dependency or missing required pack |
| `PackVersionError` | Required pack version constraint not satisfied |
| `PackConflictError` | Two packs register the same `registry_key` in the same domain |

### Conflict Detection

Two packs may not register the same `registry_key` in the same domain. If detected
during load, `PackConflictError` is raised before any extension point is registered.

---

## 4. FeatureRegistry[T] Pattern

### Problem

Python enums are closed — `RouteFamily`, `WorldEventCategory`, etc. cannot be extended
at runtime without modifying source code. Feature packs need to contribute new entries
without touching `src/domains/`.

### Solution

A generic `FeatureRegistry[T]` replaces the enum-lookup pattern for pack-contributed
extensions. Existing enum members remain as canonical IDs; packs add on top.

```python
class FeatureRegistry(Generic[T]):
    """Dict-based registry allowing dynamic registration of named entries.

    Existing enum members are pre-registered at boot. Feature packs register
    additional entries via FeaturePackLoader during scenario initialization.
    """

    def register(self, key: str, value: T) -> None:
        """Register a new entry. Raises PackConflictError on duplicate key."""

    def lookup(self, key: str) -> T:
        """Return registered entry or raise KeyError."""

    def list_all(self) -> List[Tuple[str, T]]:
        """Return all registered (key, value) pairs in registration order."""
```

### Bootstrapping

At engine boot (before `FeaturePackLoader` runs), the base domain registries are
pre-populated with entries from existing enums:

```python
# Conceptual bootstrap in FeaturePackLoader.load()
adventure_registry.register("EXPLORE", ExploreGenerator)
adventure_registry.register("TRADE", TradeGenerator)
# ... all existing RouteFamily enum values
# Then: for each active pack, register pack-contributed extensions
```

### Invariant

Existing enum values in `src/domains/adventure/schema.py`, `src/core/enums.py`, etc.
are **never removed or modified** by the pack system. They remain the canonical source
of truth for base game behavior. Packs extend — they do not replace.

---

## Integration Points

| Component | File | Role |
|---|---|---|
| `FeaturePackManifest` | `src/domains/feature_packs/manifest.py` | YAML-backed data model (E63B) |
| `RuntimeProfile` | `src/domains/feature_packs/profile.py` | Active pack selector (E63B) |
| `CompatibilityResolver` | `src/domains/feature_packs/manifest.py` | Dependency sort + conflict check (E63B) |
| `FeatureRegistry[T]` | `src/domains/feature_packs/registry.py` | Dict-based extension registry (E63C) |
| `FeaturePackLoader` | `src/domains/feature_packs/loader.py` | Discovers, resolves, loads packs (E63C) |
| `BalanceExperimentSpec` | `src/domains/feature_packs/balance_spec.py` | Declarative balance harness (E63D) |

---

## Parity Ledger References

| ID | Description |
|---|---|
| INFRA-PACK-001 | FeaturePackManifest YAML round-trips through Pydantic without data loss |
| INFRA-PACK-002 | CompatibilityResolver topological sort produces deterministic load order |
| INFRA-PACK-003 | Demo pack (demo_escort_pack) adds ESCORT_DIGNITARY RouteFamily without modifying any file in src/engine/ or src/domains/ |
