from __future__ import annotations
from typing import TYPE_CHECKING, Any, TypeVar, Generic
import logging

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState
    from src.engine.phases.context import EngineContext
    from src.engine.phases.contract import PhaseContract

logger = logging.getLogger(__name__)

T = TypeVar("T")

class EngineContextProxy(Generic[T]):
    """A non-invasive proxy for EngineContext that enforces PhaseContract permissions."""
    
    def __init__(self, ctx: EngineContext, contract: PhaseContract):
        # We use object.__setattr__ to avoid triggering our own __setattr__ during init
        object.__setattr__(self, "_ctx", ctx)
        object.__setattr__(self, "_contract", contract)
        from src.engine.phases.contract import PhaseAccess
        object.__setattr__(self, "_PhaseAccess", PhaseAccess)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            return getattr(self._ctx, name)
            
        # Special handling for emission based on contract
        if name == "emit":
            if not self._contract.allow_emit:
                raise RuntimeError(f"Phase '{self._contract.name}' attempted to EMIT but 'allow_emit' is False.")
            return getattr(self._ctx, name)

        from src.engine.phases.contract import PhaseAccess
        permission = self._contract.permissions.get(name, PhaseAccess.NONE)
        
        # AOA Stabilization: Strict Enforcement of READ permissions
        if not (permission & PhaseAccess.READ):
            raise RuntimeError(
                f"Phase '{self._contract.name}' attempted to READ unauthorized field '{name}'"
            )
        
        return getattr(self._ctx, name)

    def __setattr__(self, name: str, value: Any) -> None:
        from src.engine.phases.contract import PhaseAccess
        permission = self._contract.permissions.get(name, PhaseAccess.NONE)
        
        # AOA Stabilization: Strict Enforcement of MUTATE permissions
        if not (permission & PhaseAccess.MUTATE):
            raise RuntimeError(
                f"Phase '{self._contract.name}' attempted to MUTATE unauthorized field '{name}'"
            )
        
        setattr(self._ctx, name, value)

    def __repr__(self) -> str:
        return f"EngineContextProxy(phase={self._contract.name}, target={self._ctx})"

class ActionProposalGuard:
    """Context manager to enforce read-only world state during Action Proposal phase.
    
    Any attempt to mutate the world or its entities within this block will raise 
    a RuntimeError, ensuring that AI logic remains purely functional and proposal-based.
    """
    
    def __init__(self, world: WorldState):
        self.world = world

    def __enter__(self):
        # Lock the world state if supported (Snapshot support)
        if hasattr(self.world, "freeze"):
            self.world.freeze()
        return self.world

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Snapshot stays frozen for downstream verification.
        pass

class PhaseGuard:
    """Enforces EnginePhase contracts at runtime using an EngineContextProxy.
    
    Intercepts access to EngineContext for the duration of a phase without
    modifying the underlying class structure.
    """
    
    def __init__(self, ctx: EngineContext, contract: PhaseContract):
        self._ctx = ctx
        self._contract = contract
        self._proxy = None

    def __enter__(self) -> EngineContext:
        """Return the guarded context proxy."""
        self._proxy = EngineContextProxy(self._ctx, self._contract)
        # We cast to Any to satisfy static type checkers that expect an EngineContext
        return self._proxy # type: ignore

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clearance of proxy references
        self._proxy = None
