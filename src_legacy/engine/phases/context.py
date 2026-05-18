from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from src_legacy.config import SimulationConfig
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.engine.action_queue import ActionQueue
    from src_legacy.engine.worker_pool import WorkerPool
    from src_legacy.engine.conflict_resolver import ConflictResolver
    from src_legacy.systems.world.generator import EntityGenerator
    from src_legacy.platform.rng import DeterministicRNG
    from src_legacy.core.gameplay.faction import FactionRegistry
    from src_legacy.systems.infrastructure.manager import SystemManager
    from src_legacy.systems.gameplay.action_system import ActionSystem
    from src_legacy.systems.lifecycle.hero_lifecycle_system import HeroLifecycleSystem
    from src_legacy.actions.base import ActionProposal
    from src_legacy.utils.event_log import SimEvent
    from src_legacy.core.models.social import SocialRegistry

@dataclass
class EngineContext:
    """Shared context passed between execution phases."""
    config: SimulationConfig
    world: WorldState
    action_queue: ActionQueue
    worker_pool: WorkerPool
    conflict_resolver: ConflictResolver
    generator: EntityGenerator
    rng: DeterministicRNG
    faction_reg: FactionRegistry
    system_manager: SystemManager
    action_system: ActionSystem
    hero_lifecycle: HeroLifecycleSystem
    social_registry: SocialRegistry
    emit: Callable[[str, str, tuple[int, ...], dict | None], None]
    
    # State passed between phases during a single tick
    tick_ready_entities: list = field(default_factory=list)
    tick_new_entities: list = field(default_factory=list)
    tick_proposals: list[ActionProposal] = field(default_factory=list)
    tick_applied: list[ActionProposal] = field(default_factory=list)
    tick_rejected: list[ActionProposal] = field(default_factory=list) # Milestone 7
    tick_events: list[SimEvent] = field(default_factory=list)
    tick_start_time: float = 0.0
