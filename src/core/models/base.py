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

    def freeze(self) -> None:
        """Lock the model for read-only access (Recursive). top-level and nested collections."""
        if self._frozen: return # Avoid redundant work or loops
        self._frozen = True
        
        # 1. Recursive freeze for nested SimulationModels
        # 2. Immutable conversion for collections
        for name in type(self).model_fields:
            val = getattr(self, name)
            if hasattr(val, "freeze"):
                val.freeze()
            elif isinstance(val, list):
                # Convert to tuple (cannot append/remove)
                # We bypass __setattr__ since we are freezing
                super().__setattr__(name, tuple(val))
            elif isinstance(val, dict):
                # Wrap in MappingProxyType (cannot __setitem__)
                super().__setattr__(name, MappingProxyType(val))

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_frozen", False) and not name.startswith("_"):
            raise RuntimeError(f"Cannot mutate frozen {self.__class__.__name__} (Field: {name})")
        super().__setattr__(name, value)

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
