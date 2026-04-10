from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal, IntentUpdate
from src.ai.perception import Perception
from src.core.models.enums import AIState, ActionType, Domain, HeroClass, GoalType
from src.core.gameplay.faction import Faction, FactionRegistry
from src.core.entities.entity import Entity, Vector2

if TYPE_CHECKING:
    from typing import Any
    from src.config import SimulationConfig
    from src.core.models.snapshot import Snapshot
    from src.platform.rng import DeterministicRNG
    from src.core.models.strategy import (
        StrategicState, ProjectRecord, ObjectiveRecord, DirectiveRecord,
        ConcernRecord, LeadRecord, ObligationRecord, SocialContractRecord,
        StrategicStatus
    )
    from src.core.aspects.mind import BeliefRecord, InterpretedEvent


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
    _visible_override: list[Entity] | None = field(default=None, repr=False)
    tactical_hints: dict[str, Any] = field(default_factory=dict)

    # -- subjective helper --
    @property
    def entity_memory(self) -> dict[int, BeliefRecord]:
        return self.actor.mind.perception.entity_memory

    def get_belief(self, entity_id: int) -> BeliefRecord | None:
        return self.entity_memory.get(entity_id)

    # -- strategic helpers (authoritative commitments) --

    @property
    def strategic(self) -> StrategicState:
        """Access the actor's strategic stratum."""
        return self.actor.mind.strategic

    @property
    def current_project(self) -> ProjectRecord | None:
        """The currently active strategic project."""
        return self.strategic.current_project

    @property
    def current_objective(self) -> ObjectiveRecord | None:
        """The specific objective being pursued within the current project."""
        return self.strategic.current_objective

    @property
    def active_directives(self) -> list[DirectiveRecord]:
        """Enduring orientations filtered by priority."""
        return sorted(self.strategic.directives, key=lambda d: d.priority, reverse=True)

    @property
    def active_concerns(self) -> list[ConcernRecord]:
        """Active interrupts (Threats, Opportunities) not yet resolved."""
        return [c for c in self.strategic.concerns if c.resolved_tick is None]

    @property
    def active_leads(self) -> list[LeadRecord]:
        """Available clues for investigation that are not exhausted."""
        return [l for l in self.strategic.leads if not l.is_exhausted]

    @property
    def active_obligations(self) -> list[ObligationRecord]:
        """Unresolved social or professional duties."""
        return [o for o in self.strategic.obligations if o.resolved_tick is None]

    @property
    def active_contracts(self) -> list[SocialContractRecord]:
        """Active social contracts or party commitments."""
        return [c for c in self.strategic.contracts if c.status == StrategicStatus.ACTIVE]

    @property
    def attachment_pressure(self) -> dict[str, float]:
        """Summarized emotional/strategic pressure from place attachments."""
        # Simple heuristic: prioritize based on attachment level
        return {a.location_id: a.attachment_level for a in self.actor.mind.place_attachments}

    @property
    def recent_salient_events(self) -> list[InterpretedEvent]:
        """High-impact narrative events from recent memory."""
        # Return last 5 events with impact > 1.0
        return [e for e in self.actor.mind.narrative.memory_log if abs(e.impact) > 1.0][-5:]

    @property
    def social_support_surface(self) -> list[int]:
        """IDs of visible allies or candidates for social support."""
        # Entities with positive bonds in our social stance
        bonds = self.actor.mind.social.known_bonds
        candidates = []
        for v in self.visible:
            bond = bonds.get(v.id)
            if bond and bond.trust > 0.3:
                candidates.append(v.id)
        return candidates

    # -- cached helpers (lazily populated) --
    _visible_cache: list[Entity] | None = field(init=False, default=None)

    @property
    def visible(self) -> list[Entity]:
        if self._visible_override is not None:
            return self._visible_override
        if self._visible_cache is None:
            self._visible_cache = Perception.visible_entities(
                self.actor, self.snapshot, self.actor.spatial.vision_range)
        return self._visible_cache

    def nearest_enemy(self) -> Entity | None:
        """Return the most 'salient' combat target based on beliefs and presence."""
        visible_enemies = [v for v in self.visible if self.faction_reg.is_hostile(self.actor.identity.faction, v.identity.faction)]
        if not visible_enemies and not self.actor.mind.perception.entity_memory:
            return None

        # 1. Nemesis/Grudge Logic (Subjective Priority)
        grudges = self.actor.mind.emotion.grudges
        if grudges:
            nemesis = None
            max_grudge = -1.0
            for v in visible_enemies:
                g = grudges.get(v.id, 0.0)
                if g >= 15.0 and g > max_grudge:
                    max_grudge = g
                    nemesis = v
            if nemesis:
                return nemesis

        # 2. Saliency-Based Selection [STAGE 1]
        # We value: Distance (proximity), Threat (belief), and Personality (aggression)
        best_target = None
        max_saliency = -1.0
        
        aggression = self.actor.mind.decision.personality.aggression
        memory = self.actor.mind.perception.entity_memory

        for v in visible_enemies:
            dist = self.actor.spatial.pos.manhattan(v.spatial.pos)
            prox_weight = 1.0 / (dist + 1.0)
            
            # Belief weight
            threat_weight = 0.5 # Default for unknown
            belief = memory.get(v.id)
            if belief:
                # If we have a belief, use its threat estimate
                # High aggression makes high-threat targets more salient (challenge)
                # Low aggression (cautious) makes them less salient (avoidance)
                t = belief.threat
                t_overall = t.overall if hasattr(t, 'overall') else t.get('overall', 0.5)
                threat_weight = t_overall * (0.5 + aggression)
            
            saliency = (prox_weight * 0.7) + (threat_weight * 0.3)
            
            if saliency > max_saliency:
                max_saliency = saliency
                best_target = v

        if best_target:
            return best_target
            
        # 3. Off-screen Memory Focus (Nemeses only)
        if grudges:
            for eid, g in grudges.items():
                if g >= 20.0: # Significant grudge
                    belief = memory.get(eid)
                    if belief:
                         ent = self.snapshot.entities.get(eid)
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


def _greedy_move_toward(actor: Entity, target_pos: Vector2, snapshot: Snapshot, reason: str, updates: list[IntentUpdate] | None = None) -> ActionProposal:
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
        return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=best_step, reason=f"{reason} (Greedy)", updates=updates or [])
    
    return ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason=f"{reason} (path blocked)", updates=updates or [])


def propose_move_toward(actor: Entity, target_pos: Vector2, snapshot: Snapshot, reason: str, updates: list[IntentUpdate] | None = None) -> ActionProposal:
    dist = actor.spatial.pos.manhattan(target_pos)
    final_updates = list(updates) if updates else []

    if dist <= 2:
        return _greedy_move_toward(actor, target_pos, snapshot, reason, updates=final_updates)

    if dist > 8:
        # AOA Stabilization: Ensure target_pos is a Vector2 for grid checks [design-03]
        # AOA Stabilization: Ensure target_pos is a Vector2 for grid checks [design-03]
        if not hasattr(target_pos, 'x'):
            from src.core.models.vectors import Vector2
            try:
                target_pos = Vector2.model_validate(target_pos)
            except Exception:
                pass # If coercion fails, grid checks below will likely fail with clear error
            
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
                # Optimized step selection
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
                                          reason=f"{reason} (Flow Field)",
                                          updates=final_updates)
            
            # Fallback to direct greedy movement
            logger.debug("Navigation: FF fallback to Greedy for %s at %s", actor.id, actor.spatial.pos)

    # Use NavigationState from MindAspect
    from src.actions.base import NavigationUpdate
    nav = actor.mind.navigation
    cached = nav.cached_path
    cached_target = nav.cached_path_target
    
    if (cached and cached_target
            and cached_target == target_pos
            and len(cached) > 0
            and cached[0] == actor.spatial.pos):
        
        next_path = list(cached)
        next_path.pop(0)
        
        if next_path and is_tile_passable(actor, next_path[0], snapshot):
            final_updates.append(NavigationUpdate(cached_path=next_path, target_pos=target_pos))
            return ActionProposal(
                actor_id=actor.id, 
                verb=ActionType.MOVE,
                target=next_path[0], 
                reason=f"{reason} (A* cached)",
                updates=final_updates
            )

    from src.ai.pathfinding import Pathfinder
    pf = Pathfinder(snapshot.grid)
    path = pf.find_path(actor.spatial.pos, target_pos)

    if path:
        step = path[0]
        if is_tile_passable(actor, step, snapshot):
            final_updates.append(NavigationUpdate(cached_path=path, target_pos=target_pos))
            return ActionProposal(
                actor_id=actor.id, 
                verb=ActionType.MOVE,
                target=step, 
                reason=f"{reason} (A*)",
                updates=final_updates
            )

    return _greedy_move_toward(actor, target_pos, snapshot, reason, updates=final_updates)


def propose_move_away(actor: Entity, threat_pos: Vector2, snapshot: Snapshot, reason: str, updates: list[IntentUpdate] | None = None) -> ActionProposal:
    direction = Perception.direction_away_from(actor.spatial.pos, threat_pos)
    dest = actor.spatial.pos + direction
    final_updates = updates or []
    if is_tile_passable(actor, dest, snapshot):
        return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=dest, reason=reason, updates=final_updates)
    perps = [Vector2(-direction.y, direction.x), Vector2(direction.y, -direction.x)]
    for p in perps:
        alt = actor.spatial.pos + p
        if is_tile_passable(actor, alt, snapshot):
            return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=alt, reason=f"{reason} (side step)", updates=final_updates)
    return ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason=f"{reason} (flee blocked)", updates=final_updates)


def propose_retreat_home(ctx: AIContext, reason: str) -> tuple[AIState, ActionProposal]:
    """Propose moving toward the actor's authoritative home or nearest generic camp."""
    actor = ctx.actor
    # Heroes go to TOWN, others go to CAMP
    state = AIState.RETURN_TO_TOWN if actor.identity.faction == Faction.HERO_GUILD else AIState.RETURN_TO_CAMP
    
    # [PHASE 2 REMEDIATION] Prioritize authoritative home_pos if it exists
    if actor.spatial.home_pos:
        return state, propose_move_toward(
            actor, actor.spatial.home_pos, ctx.snapshot, reason)
            
    camp = Perception.nearest_camp(actor, ctx.snapshot)
    if camp:
        return state, propose_move_toward(
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


def get_perception_cleanup_update(actor: Entity, snapshot: Snapshot) -> PerceptionUpdate | None:
    """Return a PerceptionUpdate to clear dead entities from memory, if any."""
    dead_ids = get_dead_memory_ids(actor, snapshot)
    if not dead_ids:
        return None
    from src.actions.base import PerceptionUpdate
    return PerceptionUpdate(memory_remove=dead_ids)


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
    return ctx.actor.identity.faction != Faction.HERO_GUILD


def should_flee(actor: Entity, config: SimulationConfig, enemy: Entity | None = None) -> bool:
    """Return True if the entity's HP is below its flee threshold.
    
    Adjusted by:
    - Personality: Caution increases the threshold.
    - Mood: Despair increases it, Fury decreases it.
    - Beliefs: Threat estimates from memory increase it.
    """
    # Layer 3 Hysteresis: Use exit threshold if currently fleeing
    is_fleeing = actor.mind.decision.ai_state == AIState.FLEE or actor.mind.decision.last_goal == GoalType.FLEE
    if is_fleeing:
        base_threshold = getattr(config, "flee_exit_threshold", 0.4)
    else:
        base_threshold = getattr(config, "flee_hp_threshold", 0.2)
    
    # 1. Personality Influence [STAGE 1]
    pers = actor.mind.decision.personality
    caution_bias = (pers.caution - 0.5) * 0.2 # -0.1 to +0.1
    
    # 2. Mood modifier
    emo = actor.mind.emotion
    mood_mod = (0.5 - emo.mood) * 0.2 # -0.1 to +0.1
    
    # [PHASE 1] Panic bias
    panic_bias = emo.panic * 0.3 # High panic makes you much more likely to flee
    
    # 3. Belief/Threat Bias [STAGE 1]
    threat_mod = 0.0
    memory = actor.mind.perception.entity_memory
    
    # Nemesis recognition: If any visible enemy has threat > 0.8 OR high grudge, PANIC FLEE immediately
    # This ensures entities respect powerful enemies before taking damage. [AOA STABILIZATION]
    grudges = actor.mind.emotion.grudges
    for eid, belief in memory.items():
        is_nemesis = False
        if grudges.get(eid, 0.0) >= 10.0:  # If we've taken ~100 damage or explicit 10 grudge
            is_nemesis = True
            
        t = belief.threat
        t_overall = t.overall if hasattr(t, 'overall') else t.get('overall', 0.0)
        t_conf = t.confidence if hasattr(t, 'confidence') else t.get('confidence', 0.0)
        
        if (t_overall > 0.8 and t_conf > 0.4) or is_nemesis:
            # Check believe pos (dist <= 6 for "nearby")
            if actor.spatial.pos.manhattan(belief.pos) <= 6:
                return True
                
    if enemy:
        # Check subjective belief for this specific enemy
        belief = memory.get(enemy.id)
        if belief:
            t = belief.threat
            if t:
                # AOA Architectural Note: Snapshot actors are frozen, converting nested dicts 
                # to MappingProxyType. We use robust accessors here to handle both 
                # mutable models and immutable frozen records without crashing.
                t_conf = t.confidence if hasattr(t, 'confidence') else t.get('confidence', 0.0)
                t_overall = t.overall if hasattr(t, 'overall') else t.get('overall', 0.0)
                
                # Use threat estimate if confidence is high enough
                if t_conf > 0.3:
                    threat_mod += (t_overall * 0.4)
            # Factor in visible injury (subjective)
            if belief.visible_injury >= 0: # -1 = Unknown
                threat_mod *= (1.0 - (belief.visible_injury * 0.5))
        # Scan all known beliefs for high-threat nearby entities
        for eid, belief in memory.items():
            t = belief.threat
            if not t:
                continue
                
            # Robust access for both models and frozen dicts (mappingproxy)
            t_overall = t.overall if hasattr(t, 'overall') else t.get('overall', 0.0)
            t_conf = t.confidence if hasattr(t, 'confidence') else t.get('confidence', 0.0)
            
            if t_overall > 0.6 and t_conf > 0.4:
                # Use belief pos (might be stale!)
                d = actor.spatial.pos.manhattan(belief.pos)
                if d <= 5: # Within immediate danger zone
                    threat_mod += 0.15
                    break

    # 4. Ranged Bias
    # Phase 2 Refinement: Increased ranged_bias from 0.2 to 0.4 (ensuring flee at ~60% HP)
    # to meet E2E regression requirements for Ranger/Mage survivability.
    ranged_bias = 0.4 if _is_ranged(actor) else 0.0
    
    final_threshold = base_threshold + caution_bias + mood_mod + threat_mod + ranged_bias
    return actor.combat.hp_ratio < final_threshold

def _is_ranged(actor: Entity) -> bool:
    """Helper to detect if an entity is a ranged unit."""
    if actor.identity.hero_class in (HeroClass.RANGER, HeroClass.MAGE, HeroClass.ARCHMAGE, HeroClass.SHARPSHOOTER):
        return True
    # Check weapon (AOA: moved to inventory aspect)
    weapon = ""
    if actor.inventory:
        weapon = actor.inventory.weapon or ""
    return "bow" in weapon.lower() or "staff" in weapon.lower() or "wand" in weapon.lower()


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
