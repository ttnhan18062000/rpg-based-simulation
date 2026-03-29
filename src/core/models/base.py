from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Type, Any
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

T = TypeVar("T", bound="Aspect")

class Aspect(BaseModel):
    """Base class for all entity functional modules (Aspects/Components).
    
    Aspects are Pydantic models that hold both data and lifecycle hooks.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
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
