# API and Architecture Audit: RPG Simulation Engine

## Overview
This audit evaluates the current state of the RPG Simulation Engine's API and core architecture against established design principles and industry best practices.

## 🟢 Strengths
- **Clean API Versioning**: `/api/v1` is used consistently, allowing for future breaking changes without affecting current consumers.
- **Snapshot Isolation**: The use of immutable snapshots for the API layer ensures that simulation state isn't modified by concurrent web requests.
- **Logical Route Grouping**: Metadata, Map, Control, and State are separated, making the API intuitive for frontend developers.
- **Pydantic Schemas**: Response models are strictly typed, providing clear contracts and validation.

## ⚠️ Architectural Issues (High Priority)
### 1. EngineManager as a God Object
The `EngineManager` class in `src/api/engine_manager.py` is overloaded. It handles:
- **Simulation Lifecycle**: Starting, stopping, and pausing the thread.
- **World Generation**: Complex Voronoi region placement and town initialization.
- **Data Coordination**: Aggregating events and snapshots.
- **Persistence**: Kafka recovery logic.
**Recommendation**: Decompose into `SimulationEngine`, `WorldGenerator`, and `Coordinator` components.

### 2. Leaky Abstractions (API Layer)
Business logic and RPG-specific game data are leaking into `src/api/routes/state.py`.
- Hardcoded sets like `_MAGICAL_SKILLS` and `_SKILL_ELEMENTS` should be in the core data models or registries.
- Manual serialization of complex entities within the route functions makes the code brittle and hard to test.

### 3. Mixing Static vs. Dynamic State
The `/static` endpoint returns some fields that are actually dynamic, such as `resource_nodes.remaining`. This can lead to stale data in the frontend if not polled frequently, which defeats the purpose of a static endpoint.

## 🛠️ API Design Violations
- **Manual Mapping**: Routes are doing a lot of "heavy lifting" to convert core models to schemas. This should be handled by model methods (`to_schema`) or a dedicated mapper layer.
- **Missing Field Documentation**: While schemas exist, `Field(description=...)` is rarely used, leaving the API's purpose unclear to external consumers.
- **Inconsistent Naming**: Some enums are serialized as `name.lower()` while others are preserved.

## 🚀 Priority Action List
1. **Refactor Game Data out of API**: Move `_MAGICAL_SKILLS` and element mapping into `src/core/classes.py`.
2. **Standardize Serialization**: Implement `to_summary_schema` and `to_detail_schema` patterns in core models or a mapper.
3. **Decompose EngineManager**: Extract the `WorldGenerator` logic into a separate utility.
4. **Audit Static vs. Dynamic Paths**: Ensure `/static` only contains truly invariant data (map layout, building positions).
