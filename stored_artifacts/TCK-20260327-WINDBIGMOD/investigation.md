# BIGMOD & Wind Pillar Investigation

## Codebase Findings

### 1. `src/core/models.py` Overgrowth
- **Current Size**: 792 lines (down from 1286 in the previous state, but still excessive).
- **Core issue**: `StatsShim` is a heavy-weight proxy class that manages equipment and buffs. It's a separate concern from the base `Entity` model.
- **Risk**: Circular dependencies if `stats_proxy.py` needs to import `Entity`.
- **Mitigation**: Use a protocol or abstract base class for delegation.

### 2. `src/ai/flow_fields.py` Status (Wind Pillar)
- **Current implementation**: `FlowField` uses a flat list of direction tuples. `get_vector` implements basic cardinal neighbor averaging.
- **Missing**: True bilinear interpolation for sub-tile precision. The current "smoothing" is a simple 5-direction average.
- **Missing**: Direct wiring into `NavigationHandler` and `TownHandler`.

### 3. Existing Patterns to Reuse
- **Hysteresis**: Use the `decision_lock` pattern from the "Ground Pillar" to avoid re-generating fields too often.
- **Memory**: The "Soul Pillar" already records some location metadata.

## Risks & Assumptions
- **Performance**: High-resolution flow fields (for a 512x512 grid) can consume ~2MB of float data. We assume this is acceptable.
- **Refactoring Migration**: `StatsShim` is an invasive change. We must ensure all `@property` delegations on `Hero` and `Mob` still work.
- **A* vs Flow Fields**: Flow fields are calculated to a specific point. They aren't useful for "wander" or "flee" (since flee is toward *away* from a target). They are best for "Return toward Town" or "Move toward Boss".
