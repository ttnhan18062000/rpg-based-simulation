from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Type, Any
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_serializer
from types import MappingProxyType
import typing

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

T = TypeVar("T", bound="Aspect")

class SimulationModel(BaseModel):
    """Base class for all sim state models that support runtime immutability."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    _frozen: bool = PrivateAttr(default=False)

    def copy(self: T, deep: bool = True) -> T:
        """Copy for snapshot isolation or recovery. 
        
        AOA Pillar 1: Isolation. Copies are always unfrozen and mutable by default.
        By default, it uses deepcopy (deep=True). Use deep=False for shallow model-only copy.
        """
        return self.model_copy(deep=deep)

    def model_copy(self: T, **kwargs: Any) -> T:
        """Override Pydantic's model_copy to ensure private state reset and collection mutability."""
        # Call super().model_copy first. If deep=True (default/typical), it deep-copies all fields.
        copy_obj = super().model_copy(**kwargs)
        
        # AOA Pillar 1: Isolation. The new copy must be unfrozen and mutable.
        # We recursively unfreeze the copy_obj IN-PLACE (since it's a fresh copy).
        self._unfreeze_inplace(copy_obj)
        
        return copy_obj

    def _unfreeze_inplace(self, obj: Any) -> None:
        """Recursively resets _frozen and converts collections to mutable types in-place."""
        if isinstance(obj, SimulationModel):
            # AOA Stabilization: If it's already unfrozen, skip recursion
            # Unless we are doing this on a fresh deepcopy which might have 
            # inherited the 'True' flag but contains immutable collection types.
            if getattr(obj, "_frozen", False) is False:
                # Optimized Path: Check if it has any collections that need unfreezing
                # For now, we still need to check nested models, but we can skip
                # the flag setting and most of the overhead.
                pass 

            # Reset frozen flag on this model
            object.__setattr__(obj, "_frozen", False)
            
            # Recurse into all fields
            fields = getattr(type(obj), "model_fields", None)
            if fields:
                for name in fields:
                    val = getattr(obj, name)
                    if val is not None:
                        # Process the value and set it back on the object
                        new_val = self._unfreeze_val_recursive(val)
                        if new_val is not val:
                            object.__setattr__(obj, name, new_val)
            elif hasattr(obj, "__dict__"):
                for name, val in obj.__dict__.items():
                    if not name.startswith("_"):
                        new_val = self._unfreeze_val_recursive(val)
                        if new_val is not val:
                            object.__setattr__(obj, name, new_val)

    def _unfreeze_val_recursive(self, val: Any) -> Any:
        """Helper to process values during in-place unfreezing."""
        if isinstance(val, MappingProxyType):
            return {k: self._unfreeze_val_recursive(v) for k, v in val.items()}
            
        if isinstance(val, (tuple, list)):
            return [self._unfreeze_val_recursive(item) for item in val]
            
        if isinstance(val, (frozenset, set)):
            return set(self._unfreeze_val_recursive(item) for item in val)
            
        if isinstance(val, dict):
            return {k: self._unfreeze_val_recursive(v) for k, v in val.items()}

        if isinstance(val, SimulationModel):
            # If it's a model, it was already deep-copied by super().model_copy(deep=True).
            self._unfreeze_inplace(val)
            return val
            
        return val

    @model_serializer(mode='plain')
    def _serialize_aoa(self) -> dict[str, Any]:
        """AOA Phase 6: Custom serialization for frozen models.
        
        Converts MappingProxyType and deep tuples back to standard JSON-friendly 
        types without triggering Pydantic validation warnings.
        """
        # Internal state without private attributes
        data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        return self._serialize_recursive(data)

    def _serialize_recursive(self, val: Any) -> Any:
        """Helper for _serialize_aoa to deep-convert AOA types for the wire."""
        if isinstance(val, (MappingProxyType, dict)):
            return {str(k): self._serialize_recursive(v) for k, v in val.items()}
        if isinstance(val, (tuple, list, set, frozenset)):
            return [self._serialize_recursive(v) for v in val]
        if isinstance(val, SimulationModel):
            return val.model_dump()
        return val


    def freeze(self) -> None:
        """Lock the model for read-only access (Recursive). top-level and nested collections."""
        # Use getattr to safely check _frozen even if it's in slots or __dict__
        if getattr(self, "_frozen", False):
            return 
        
        # Run validation before freezing to ensure data integrity
        self.validate()
        
        # Use object.__setattr__ to bypass Pydantic's frozen check for initial flag
        object.__setattr__(self, "_frozen", True)
        
        # 1. Recursive freeze for nested SimulationModels and collections
        # Pydantic models have model_fields; if it's a standard dataclass or slotted object, 
        # we might need to use __slots__ or __dict__.
        fields = getattr(type(self), "model_fields", None)
        if fields:
            for name in fields:
                val = getattr(self, name)
                if val is not None:
                    # Always use object.__setattr__ during internal AOA freeze
                    object.__setattr__(self, name, self._freeze_recursive(val))
        elif hasattr(self, "__dict__"):
            for name, val in self.__dict__.items():
                if not name.startswith("_"):
                    object.__setattr__(self, name, self._freeze_recursive(val))
        elif hasattr(self, "__slots__"):
            for name in self.__slots__:
                if not name.startswith("_"):
                    val = getattr(self, name)
                    object.__setattr__(self, name, self._freeze_recursive(val))

    def _freeze_recursive(self, val: Any) -> Any:
        """Recursively freeze models and convert collections to immutable equivalents.
        
        Optimized to skip already frozen objects to avoid re-validation overhead.
        """
        # Pillar 1 & 2: AOA Immutability
        # If it has a freeze method, it's likely a SimulationModel or Aspect
        if hasattr(val, "freeze") and callable(val.freeze):
            if not getattr(val, "_frozen", False):
                val.freeze()
            return val
            
        if isinstance(val, (list, tuple)):
            # Handle both lists and tuples to ensure deep immutability
            # Only convert if not already a tuple of non-mutable items
            return tuple(self._freeze_recursive(item) for item in val)
            
        if isinstance(val, (dict, MappingProxyType)):
            # If it's already a MappingProxyType, it might still have nested mutable items
            # Recursively freeze values and wrap in MappingProxyType
            frozen_dict = {k: self._freeze_recursive(v) for k, v in val.items()}
            return MappingProxyType(frozen_dict)
            
        if isinstance(val, (bytearray, memoryview)):
            return bytes(val)
            
        if isinstance(val, set):
            return frozenset(self._freeze_recursive(item) for item in val)
            
        return val

    def validate(self) -> None:
        """Domain-specific invariant validation. Subclasses should override."""
        pass

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_frozen", False) and not name.startswith("_"):
            # Use self.__class__.__name__ for consistency with line 64
            raise RuntimeError(f"Cannot mutate frozen {self.__class__.__name__} (Field: {name})")
        object.__setattr__(self, name, value)

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
            object.__setattr__(self, key, val)

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
