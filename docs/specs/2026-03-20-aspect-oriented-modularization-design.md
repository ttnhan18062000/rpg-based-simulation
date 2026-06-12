---
status: archive
authority: P2
audience: historical
layer: core
original_date: 2026-03-20
---

# Design Spec: Aspect-Oriented Entity Modularization

## Purpose
The `Entity` class in `src/core/models.py` has become a "god-object" with over 100 fields, leading to high coupling and making it difficult to maintain, serialize, and test. This design proposes a full Aspect-Oriented (ECS-like) decomposition to move toward a composition-based architecture.

## Goals
- **Decoupling**: Separate concerns (Combat, Inventory, AI, Progression) into independent modules.
- **Type Safety**: Use Pydantic V2 for all Aspects to ensure data validation and easy serialization.
- **Flexibility**: Allow entities to have dynamic sets of behaviors by attaching/detaching Aspects.
- **Incremental Migration**: Provide a path to refactor the codebase without breaking existing systems.

## Solution

### 1. Base Framework
We will introduce a base `Aspect` class and a revised `Entity` container.

#### Aspect Base (`src/core/base.py`)
```python
from pydantic import BaseModel, ConfigDict
from typing import TYPE_CHECKING, TypeVar, Type

if TYPE_CHECKING:
    from src_legacy.core.models import Entity

class Aspect(BaseModel):
    """Base class for all entity functional modules."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Parent reference (internally managed)
    _entity: "Entity | None" = None

    def on_attach(self, entity: "Entity") -> None:
        self._entity = entity
        
    def on_tick(self, tick: int) -> None:
        """Lifecycle hook called every world tick."""
        pass
```

#### Entity Container (`src/core/models.py`)
```python
class Entity(BaseModel):
    id: int
    kind: str
    aspects: dict[str, Aspect] = Field(default_factory=dict)
    
    def on_tick(self, tick: int) -> None:
        for aspect in self.aspects.values():
            aspect.on_tick(tick)
```

### 2. Core Aspects
The following Aspects will be implemented to replace flat fields:

| Aspect | Fields Covered | Responsibilities |
| :--- | :--- | :--- |
| **Identity** | `display_name`, `faction`, `role`, `tier` | Faction relations, display names. |
| **Spatial** | `pos`, `region_id`, `home_pos`, `leash_radius` | Coordinates, regions, world positioning. |
| **Combat** | `hp`, `max_hp`, `stats`, `effects` | Health, combat stats, status effects. |
| **Inventory** | `items`, `weapon`, `armor`, `accessory` | Item management, equipment bonuses. |
| **Progression** | `level`, `xp`, `gold`, `skills`, `mastery` | Levelling, attribute points, skill learning. |
| **Mind** | `ai_state`, `goals`, `memory`, `threat_table` | Decision making, memory, aggro storage. |

### 3. Data Flow & Hooks
- **Lifecycle**: `Entity.on_tick()` delegates to all attached Aspects.
- **Behavioral Hooks**: Future hooks like `on_damage(amount, source)` or `on_move(from, to)` can be added to specific Aspects to implement reactive logic (e.g., thorns effects, traps).
- **Projections**: For API consumers (FastAPI/Poll/Stream), the `Entity.to_slim_schema()` will be updated to project data from multiple Aspects into the expected flat format.

### 4. Implementation Strategy
1. **Foundation**: Build the `Aspect` base and the `SpatialAspect` (as a test case).
2. **Bridge Phase**: Introduce Aspects into the `Entity` class while maintaining the original fields as `@property` shims. (**STATUS: ACTIVE - Used for Combat/Identity/Spatial/Progression**)
   ```python
   @property
   def hp(self) -> int:
       return self.get_aspect(CombatAspect).hp
   ```
3. **Migration**: Systematically update subsystems (`CombatActions`, `AISystems`) to use `entity.get_aspect(T)` or direct aspect access.
4. **Cleanup**: Remove legacy field shims and redundant `Entity` methods.

## Verification Plan
- **Unit Tests**: Each Aspect will have dedicated unit tests in `tests/unit/core/aspects/`.
- **Regression**: The existing `619` tests must pass in "Bridge" mode.
- **E2E**: Verify that replay determinism is maintained with Aspect-based state.
