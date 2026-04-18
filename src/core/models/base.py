from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Type, Any
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_serializer
from types import MappingProxyType
import typing
import copyreg
import threading
import weakref

# AOA Mutation Tripwire: Prevents state mutation during AI decision phases.
_decision_context = threading.local()

class DecisionPhase:
    """Context manager to enforce read-only access during AI deliberation.
    
    Uses a generation counter to allow mutation of objects created DURING 
    the phase (proposals/updates) while protecting pre-existing state.
    """
    def __enter__(self) -> None:
        # Increment generation to mark the start of a new protected phase
        current = getattr(_decision_context, "generation", 0)
        _decision_context.generation = current + 1

    def __exit__(self, *args: Any) -> None:
        # Decrement to return to previous state (supports nesting)
        current = getattr(_decision_context, "generation", 0)
        _decision_context.generation = max(0, current - 1)

    @staticmethod
    def is_active() -> bool:
        return getattr(_decision_context, "generation", 0) > 0

    @staticmethod
    def current_generation() -> int:
        return getattr(_decision_context, "generation", 0)

# AOA Phase Boundary: Register MappingProxyType with copyreg to ensure 
# picklability/deepcopy safety in Python 3.13. This allows frozen models 
# to be deep-copied into snapshots without TypeError.
def _reconstruct_mapping_proxy(d: dict[Any, Any]) -> MappingProxyType:
    return MappingProxyType(d)

def _reduce_mapping_proxy(mp: MappingProxyType) -> tuple:
    return (_reconstruct_mapping_proxy, (dict(mp),))

copyreg.pickle(MappingProxyType, _reduce_mapping_proxy)

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

T = TypeVar("T", bound="Aspect")

class SimulationModel(BaseModel):
    """Base class for all sim state models that support runtime immutability."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    _frozen: bool = PrivateAttr(default=False)
    
    # Track which decision generation this instance was created in.
    # Instances from generation 0 (World/State) are protected from AI mutation.
    _creation_generation: int = PrivateAttr(default_factory=DecisionPhase.current_generation)
    
    # AOA Type Isolation: If True, this class is part of the core state and 
    # should be protected by the mutation tripwire during decision phases.
    TRIPWIRE_PROTECTED: typing.ClassVar[bool] = False

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        # Pydantic default_factory for PrivateAttr doesn't always trigger in manual __init__
        if not hasattr(self, "_creation_generation"):
            object.__setattr__(self, "_creation_generation", DecisionPhase.current_generation())

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
        # It is also marked with the CURRENT generation so it can be modified 
        # as a local work-object even during a decision phase.
        object.__setattr__(copy_obj, "_creation_generation", DecisionPhase.current_generation())
        object.__setattr__(copy_obj, "_frozen", False)
        
        if getattr(self, "_frozen", False):
            self._unfreeze_inplace(copy_obj)
        
        return copy_obj

    def _unfreeze_inplace(self, obj: Any) -> None:
        """Recursively resets _frozen and converts collections to mutable types in-place."""
        if isinstance(obj, SimulationModel):
            # AOA Stabilization: If it's already unfrozen, skip recursion
            if getattr(obj, "_frozen", False) is False:
                pass 

            # Reset frozen flag on this model
            object.__setattr__(obj, "_frozen", False)
            
            # Recurse into all fields
            fields = getattr(type(obj), "model_fields", None)
            if fields:
                for name in fields:
                    val = getattr(obj, name)
                    if val is not None:
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
            self._unfreeze_inplace(val)
            return val
        return val

    @model_serializer(mode='plain')
    def _serialize_aoa(self) -> dict[str, Any]:
        """AOA Phase 6: Custom serialization for frozen models."""
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
        if getattr(self, "_frozen", False):
            return 
        self.validate()
        object.__setattr__(self, "_frozen", True)
        
        fields = getattr(type(self), "model_fields", None)
        if fields:
            for name, field_info in fields.items():
                val = getattr(self, name)
                if val is not None:
                    if isinstance(val, dict):
                        expected_type = field_info.annotation
                        model_type = self._get_model_type(expected_type)
                        if model_type:
                            val = model_type.model_validate(val)
                            object.__setattr__(self, name, val)
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

    def _get_model_type(self, annotation: Any) -> type[SimulationModel] | None:
        """Helper to extract a SimulationModel subclass from a type annotation."""
        import typing
        if isinstance(annotation, type) and issubclass(annotation, SimulationModel):
            return annotation
        origin = typing.get_origin(annotation)
        if origin is typing.Union:
            model_types = [arg for arg in typing.get_args(annotation) 
                          if isinstance(arg, type) and issubclass(arg, SimulationModel)]
            if len(model_types) == 1:
                return model_types[0]
        return None

    def _freeze_recursive(self, val: Any) -> Any:
        """Recursively freeze models and convert collections to immutable equivalents."""
        if isinstance(val, SimulationModel):
            if not getattr(val, "_frozen", False):
                val.freeze()
            return val
        if isinstance(val, (list, tuple)):
            return tuple(self._freeze_recursive(item) for item in val)
        if isinstance(val, (dict, MappingProxyType)):
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
        # AOA Pillar 1: Mutation Tripwire (Optimized).
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        # Optimization: Only core state models (Entity, Aspect, WorldState) 
        # incur the tripwire overhead. Transient objects (Proposals, records) 
        # skip this entirely.
        if self.TRIPWIRE_PROTECTED:
            current_gen = getattr(_decision_context, "generation", 0)
            if current_gen > 0:
                # The tripwire fires if this object was created in an EARLIER generation
                # (meaning it is Sensing input, not a local work-object for the current phase).
                my_gen = getattr(self, "_creation_generation", 0)
                if my_gen < current_gen:
                    raise RuntimeError(
                        f"Cannot mutate {self.__class__.__name__}.{name} during Decision Phase. "
                        f"[Protected State Violation: Gen {my_gen} < {current_gen}]"
                    )
        
        # Finally, check for explicit frozen status (Snapshots used in Multi-Worker mode).
        if getattr(self, "_frozen", False):
            raise RuntimeError(f"Cannot mutate {self.__class__.__name__}.{name}: Object is Frozen.")
            
        object.__setattr__(self, name, value)

    def __getstate__(self) -> dict[str, Any]:
        """Custom pickle state to handle MappingProxyType."""
        state = self.__dict__.copy()
        for key, val in state.items():
            if isinstance(val, MappingProxyType):
                state[key] = dict(val)
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Custom pickle restoration."""
        for key, val in state.items():
            object.__setattr__(key, val)

class Aspect(SimulationModel):
    """Base class for all entity functional modules (Aspects/Components)."""
    TRIPWIRE_PROTECTED: typing.ClassVar[bool] = True
    _entity_ref: Any = PrivateAttr(default=None)

    def on_attach(self, entity: Entity) -> None:
        self._entity_ref = weakref.ref(entity)

    def on_tick(self, tick: int) -> None:
        pass
    
    @property
    def entity(self) -> Entity:
        entity = self._entity_ref() if self._entity_ref else None
        if entity is None:
            raise RuntimeError(f"Aspect {self.__class__.__name__} is not attached to an entity or entity has been GC'd.")
        return entity
