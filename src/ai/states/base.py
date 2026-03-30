from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.ai.perception import Perception
from src.core.models.enums import AIState, ActionType, Domain
from src.core.gameplay.faction import Faction, FactionRegistry
from src.core.entities.entity import Entity, Vector2

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.models.snapshot import Snapshot
    from src.platform.rng import DeterministicRNG


@dataclass(slots=True)
class AIContext:
    """All data a state handler might need.  Extend this to add weather,
    quests, etc. without changing handler signatures."""

    actor: Entity
    snapshot: Snapshot
    config: SimulationConfig
    rng: DeterministicRNG
    faction_reg: FactionRegistry
    
    # Pillar 3: Tactical Intent (Decoupled hints from Brain -> Handler)
    tactical_hints: dict[str, Any] = field(default_factory=dict)

    # -- cached helpers (lazily populated) --

    _visible: list[Entity] | None = None

    @property
    def visible(self) -> list[Entity]:
        if self._visible is None:
            self._visible = Perception.visible_entities(
                self.actor, self.snapshot, self.actor.spatial.vision_range)
        return self._visible

    def nearest_enemy(self) -> Entity | None:
        """Return best combat target."""
        if self.actor.mind.emotion.grudges:
            visible_targets = [v for v in self.visible if self.faction_reg.is_hostile(self.actor.identity.faction, v.identity.faction)]
            nemesis = None
            max_grudge = 0.0
            for v in visible_targets:
                g = self.actor.mind.emotion.grudges.get(v.id, 0.0)
                # Lower threshold for immediate recognition
                if g >= 15.0 and g > max_grudge:
                    max_grudge = g
                    nemesis = v
            if nemesis:
                return nemesis

        nearest = Perception.nearest_enemy(self.actor, self.visible, self.faction_reg)
        if nearest:
            return nearest
            
        # Pillar 3: Memory-Aware Nemesis Focus
        # If no visible enemies, check memory for a known nemesis (grudge >= 15.0)
        grudges = self.actor.mind.emotion.grudges
        if grudges:
            memory = self.actor.mind.perception.entity_memory
            for eid in memory.keys():
                if grudges.get(eid, 0.0) >= 15.0:
                    ent = snapshot.entities.get(eid)
                    if ent and ent.combat.alive:
                        return ent
                    
        return None

    def nearest_ally(self) -> Entity | None:
        return Perception.nearest_ally(self.actor, self.visible, self.faction_reg)


class StateHandler(ABC):
    """Abstract base for AI state handlers."""

    @abstractmethod
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        ...


def is_tile_passable(actor: Entity, pos: Vector2, snapshot: Snapshot) -> bool:
    return snapshot.grid.is_walkable(pos)


def _greedy_move_toward(actor: Entity, target_pos: Vector2, snapshot: Snapshot, reason: str, intent_metadata: dict[str, Any] | None = None) -> ActionProposal:
    # --- Greedy Fallback ---
    # Find all 4 neighbors, pick the one with minimal Manhattan distance to destination
    neighbors = [
        Vector2(x=actor.spatial.pos.x + 1, y=actor.spatial.pos.y),
        Vector2(x=actor.spatial.pos.x - 1, y=actor.spatial.pos.y),
        Vector2(x=actor.spatial.pos.x, y=actor.spatial.pos.y + 1),
        Vector2(x=actor.spatial.pos.x, y=actor.spatial.pos.y - 1),
    ]
    
    best_step = None
    min_dist = actor.spatial.pos.manhattan(target_pos)
    
    for n in neighbors:
        if not snapshot.grid.is_walkable(n): continue
        d = n.manhattan(target_pos)
        if d < min_dist:
            min_dist = d
            best_step = n
            
    if best_step:
        return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=best_step, reason=f"{reason} (Greedy)", intent_metadata=intent_metadata)
    
    return ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason=f"{reason} (path blocked)", intent_metadata=intent_metadata)


def propose_move_toward(actor: Entity, target_pos: Vector2, snapshot: Snapshot, reason: str, intent_metadata: dict[str, Any] | None = None) -> ActionProposal:
    dist = actor.spatial.pos.manhattan(target_pos)
    if dist <= 2:
        return _greedy_move_toward(actor, target_pos, snapshot, reason, intent_metadata)

    if dist > 8:
        is_shared_target = (snapshot.grid.is_town(target_pos) or snapshot.grid.is_camp(target_pos))
        
        # Check for World Boss (Calamity) at target position
        if not is_shared_target:
            from src.core.models.enums import EntityRole
            # Use spatial index to quickly check entities at target_pos
            nearby_ids = snapshot.nearby_entity_ids(target_pos.x, target_pos.y, 1)
            for eid in nearby_ids:
                e = snapshot.entities.get(eid)
                if e and e.spatial.pos == target_pos and e.identity.role == EntityRole.WORLD_BOSS:
                    is_shared_target = True
                    break
        
        if is_shared_target:
            from src.ai.flow_fields import FlowFieldManager
            ff = FlowFieldManager.get_instance().get_flow_field(target_pos, snapshot.grid, snapshot.tick)
            fvec = ff.get_vector(actor.spatial.pos)
            if fvec and (abs(fvec.x) > 0.01 or abs(fvec.y) > 0.01):
                # Optimized step selection: pick the cardinal/diagonal step that aligns best with the flow
                from src.core.models.vectors import DIRECTION_OFFSETS
                best_step = None
                max_dot = -1.0
                for step in DIRECTION_OFFSETS.values():
                    dot = step.x * fvec.x + step.y * fvec.y
                    if dot > max_dot:
                        dest = actor.spatial.pos + step
                        if is_tile_passable(actor, dest, snapshot):
                            max_dot = dot
                            best_step = step
                
                if best_step:
                    return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, 
                                          target=actor.spatial.pos + best_step, 
                                          reason=f"{reason} (Flow Field)")
            
            # Fallback to direct greedy movement if flow field is zero/available (E2E Arenas)
            logger.debug("Navigation: FF fallback to Greedy for %s at %s", actor.id, actor.spatial.pos)

    # Use NavigationState from MindAspect
    nav = actor.mind.navigation
    cached = nav.cached_path
    cached_target = nav.cached_path_target
    
    if (cached and cached_target
            and cached_target == target_pos
            and len(cached) > 0
            and cached[0] == actor.spatial.pos):
        
        # Propose the next step while including the updated (remaining) path in metadata
        next_path = list(cached)
        next_path.pop(0)
        
        if next_path and is_tile_passable(actor, next_path[0], snapshot):
            # Merge caller's intent_metadata with navigation metadata
            final_meta = {**(intent_metadata or {}), "cached_path": next_path, "cached_path_target": target_pos}
            return ActionProposal(
                actor_id=actor.id, 
                verb=ActionType.MOVE,
                target=next_path[0], 
                reason=f"{reason} (A* cached)",
                intent_metadata=final_meta
            )

    from src.ai.pathfinding import Pathfinder
    pf = Pathfinder(snapshot.grid)
    path = pf.find_path(actor.spatial.pos, target_pos)

    if path:
        # Instead of direct mutation: actor.cached_path = path
        step = path[0]
        # Merge caller's intent_metadata with navigation metadata
        final_meta = {**(intent_metadata or {}), "cached_path": path, "cached_path_target": target_pos}
        if is_tile_passable(actor, step, snapshot):
            return ActionProposal(
                actor_id=actor.id, 
                verb=ActionType.MOVE,
                target=step, 
                reason=f"{reason} (A*)",
                intent_metadata=final_meta
            )

    return _greedy_move_toward(actor, target_pos, snapshot, reason)


def propose_move_away(actor: Entity, threat_pos: Vector2, snapshot: Snapshot, reason: str, intent_metadata: dict[str, Any] | None = None) -> ActionProposal:
    direction = Perception.direction_away_from(actor.spatial.pos, threat_pos)
    dest = actor.spatial.pos + direction
    if is_tile_passable(actor, dest, snapshot):
        return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=dest, reason=reason, intent_metadata=intent_metadata)
    perps = [Vector2(-direction.y, direction.x), Vector2(direction.y, -direction.x)]
    for p in perps:
        alt = actor.spatial.pos + p
        if is_tile_passable(actor, alt, snapshot):
            return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=alt, reason=f"{reason} (side step)", intent_metadata=intent_metadata)
    return ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason=f"{reason} (flee blocked)", intent_metadata=intent_metadata)


def propose_retreat_home(ctx: AIContext, reason: str) -> tuple[AIState, ActionProposal]:
    actor = ctx.actor
    if actor.identity.faction == Faction.HERO_GUILD and actor.spatial.home_pos:
        return AIState.RETURN_TO_TOWN, propose_move_toward(
            actor, actor.spatial.home_pos, ctx.snapshot, reason)
    camp = Perception.nearest_camp(actor, ctx.snapshot)
    if camp:
        return AIState.RETURN_TO_CAMP, propose_move_toward(
            actor, camp, ctx.snapshot, reason)
    enemy = ctx.nearest_enemy()
    if enemy:
        return AIState.FLEE, propose_move_away(actor, enemy.spatial.pos, ctx.snapshot, reason)
    return AIState.WANDER, ActionProposal(
        actor_id=actor.id, verb=ActionType.REST, reason=f"{reason} (nowhere to go)")


def get_dead_memory_ids(actor: Entity, snapshot: Snapshot) -> list[int]:
    """Return list of entity IDs in memory that are dead or gone."""
    return [
        eid for eid in actor.mind.perception.entity_memory 
        if eid not in snapshot.entities or not snapshot.entities[eid].combat.alive
    ]


def clear_dead_from_memory(actor: Entity, snapshot: Snapshot) -> None:
    """[Pillar 1: Read-Only] Temporary shim to satisfy imports. 
    Actual clearing must happen via ResolutionPhase and metadata.
    """
    pass


def beyond_leash(actor: Entity, multiplier: float = 1.0) -> bool:
    """Return True if the entity is beyond its leash range from home."""
    spatial = actor.spatial
    if not spatial.home_pos or spatial.leash_radius <= 0:
        return False
    dist = spatial.pos.manhattan(spatial.home_pos)
    return dist > spatial.leash_radius * multiplier


def is_in_hostile_town(ctx: AIContext) -> bool:
    """Return True if the entity is in a town hostile to its faction."""
    if not ctx.snapshot.grid.is_town(ctx.actor.spatial.pos):
        return False
    # Simplified: for now, all towns are assumed hostile to 'mob' factions
    # or we could check a town faction registry if it existed.
    # In WorldLoop, monsters are generally burned by town auras.
    return ctx.actor.identity.faction not in (Faction.HERO_GUILD, Faction.TOWN_GUARD)


def should_flee(actor: Entity, config: SimulationConfig) -> bool:
    """Return True if the entity's HP is below its flee threshold.
    
    Adjusted by mood: Despair (0.0) causes earlier fleeing, 
    Fury (1.0) causes staying longer.
    """
    base_threshold = config.flee_hp_threshold
    
    # Mood modifier derived from EmotionState in MindAspect
    mood = actor.mind.emotion.mood
    threshold_mod = (0.5 - mood) * 0.2
    
    threshold = base_threshold + threshold_mod
    
    # Heroes might have different base thresholds if not provided by config
    if actor.identity.faction == Faction.HERO_GUILD and base_threshold <= 0:
        threshold = 0.2 + threshold_mod
        
    return actor.combat.hp_ratio < threshold


def is_on_home_territory(ctx: AIContext) -> bool:
    """Return True if the entity is within its camp or town area."""
    if ctx.actor.identity.faction == Faction.HERO_GUILD:
        return ctx.snapshot.grid.is_town(ctx.actor.spatial.pos)
    camp = Perception.nearest_camp(ctx.actor, ctx.snapshot)
    if camp:
        return ctx.actor.spatial.pos.manhattan(camp) <= ctx.config.camp_radius + 2
    return False


def is_on_enemy_territory(ctx: AIContext) -> bool:
    """Return True if the entity is in a hostile territory."""
    if ctx.actor.identity.faction == Faction.HERO_GUILD:
        camp = Perception.nearest_camp(ctx.actor, ctx.snapshot)
        if camp:
            return ctx.actor.spatial.pos.manhattan(camp) <= ctx.config.camp_radius + 5
    else:
        return ctx.snapshot.grid.is_town(ctx.actor.spatial.pos)
    return False
