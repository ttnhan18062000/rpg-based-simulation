# Migration Debt & Compatibility Layer Log

This document provides a formal audit of current compatibility adapters, legacy logic, and fallback defaults implemented in the worldbuilding compilation pipelines to ensure safe and deterministic system migration paths.

## Current Migration Debt Items

### 1. `get_role_enum` Direct Use
- **Current Use**: Direct mapping of raw strings (e.g. `"citizen"`, `"guard"`, `"monster"`) using basic text search checks when resolving entity roles in `src/worldbuilding/compiler.py`.
- **Desired Replacement**: Fully route role translation through content-resolved `CompileContext` legacy role mappings populated by semantic services.
- **Migration Risk**: Low. Fallback mappers are fully thread-safe and isolated.
- **Is Replacement Required Now?**: Optional. Adapters are kept active to maintain 100% backward compatibility with legacy test specifications that do not use catalog-resolved profiles.

### 2. `get_faction_enum` Direct Use
- **Current Use**: Parsing string alignments (e.g. `"villagers"`, `"monsters"`) to map them to the Faction enum in `src/worldbuilding/compiler.py`.
- **Desired Replacement**: Dynamic retrieval from `CompileContext.legacy_factions` mapped during the content catalog semantical resolution phase.
- **Migration Risk**: Low. Text mappers are standard and safe.
- **Is Replacement Required Now?**: Optional. Preserved for legacy spec compatibility.

### 3. Direct Faction Enum Checks
- **Current Use**: Explicit checks for specific factions (`Faction.HERO_GUILD`, `Faction.MONSTER_HORDE`, `Faction.TOWN_COUNCIL`) inside the compiler's faction treasury starting vaults block.
- **Desired Replacement**: Generalize faction treasury starting vaults so that any custom faction registered in the content catalog/economy profile can be initialized without hardcoded enum branching.
- **Migration Risk**: Medium. Changing structural naming conventions of default vault paths in `global_resources` could affect downstream queries and legacy simulation tests.
- **Is Replacement Required Now?**: No. Must be retained until all downstream telemetry consumers migrate away from fixed vault resource keys.

### 4. Compiler Fallback Defaults
- **Current Use**: Compiler defaults of HP `100`, ATK `10`, HP `500` for buildings, and required harvest ticks `10` for resources.
- **Desired Replacement**: Direct lookup from Content Catalog globals semantics service.
- **Migration Risk**: Low. Already partially integrated.
- **Is Replacement Required Now?**: No. Essential for no-context fallback compilation compatibility.
