from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Type, Any
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from types import MappingProxyType

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

T = TypeVar("T", bound="Aspect")

class SimulationModel(BaseModel):
    """Base class for all sim state models that support runtime immutability."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    _frozen: bool = PrivateAttr(default=False)

    def copy(self: T) -> T:
        """Deep copy for snapshot isolation."""
        return self.model_copy(deep=True)

    def freeze(self) -> None:
        """Lock the model for read-only access (Recursive). top-level and nested collections."""
        if self._frozen: return 
        
        # Run validation before freezing to ensure data integrity
        self.validate()
        
        self._frozen = True
        
        # 1. Recursive freeze for nested SimulationModels and collections
        for name in type(self).model_fields:
            val = getattr(self, name)
            if val is not None:
                super().__setattr__(name, self._freeze_recursive(val))

    def _freeze_recursive(self, val: Any) -> Any:
        """Recursively freeze models and convert collections to immutable equivalents."""
        if hasattr(val, "freeze") and callable(val.freeze):
            val.freeze()
            return val
            
        if isinstance(val, list):
            return tuple(self._freeze_recursive(item) for item in val)
            
        if isinstance(val, dict):
            # Recursively freeze values and wrap in MappingProxyType
            frozen_dict = {k: self._freeze_recursive(v) for k, v in val.items()}
            return MappingProxyType(frozen_dict)
            
        if isinstance(val, (bytearray, memoryview)):
            return bytes(val)
            
        # For tuples, we still need to recursively check items
        if isinstance(val, tuple):
            return tuple(self._freeze_recursive(item) for item in val)

        return val

    def validate(self) -> None:
        """Domain-specific invariant validation. Subclasses should override."""
        pass

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_frozen", False) and not name.startswith("_"):
            # Use self.__class__.__name__ for consistency with line 64
            raise RuntimeError(f"Cannot mutate frozen {self.__class__.__name__} (Field: {name})")
        super().__setattr__(name, value)

    def __getstate__(self) -> dict[str, Any]:
        """Custom pickle state to handle MappingProxyType."""
        state = self.__dict__.copy()
        # MappingProxyType is not picklable; convert back to dict for the wire
        for key, val in state.items():
            if isinstance(val, MappingProxyType):
                state[key] = dict(val)
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Custom pickle restoration."""
        for key, val in state.items():
            super().__setattr__(key, val)

class Aspect(SimulationModel):
    """Base class for all entity functional modules (Aspects/Components).
    
    Aspects are Pydantic models that hold both data and lifecycle hooks.
    """
    
    # Internal reference to the parent entity (not serialized)
    _entity: Any = PrivateAttr(default=None)

    def on_attach(self, entity: Entity) -> None:
        """Called when the aspect is added to an entity."""
        self._entity = entity

    def on_tick(self, tick: int) -> None:
        """Lifecycle hook called every world tick."""
        pass
    
    @property
    def entity(self) -> Entity:
        if self._entity is None:
            raise RuntimeError(f"Aspect {self.__class__.__name__} is not attached to an entity.")
        return self._entity
