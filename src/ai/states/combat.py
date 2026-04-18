from __future__ import annotations

from src.actions.base import ActionType, ActionProposal
from src.ai.perception import Perception
from src.core.models.enums import AIState, MovementIntention
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.entities.entity import Entity, Vector2
from src.ai.states.base import (
    AIContext, StateHandler, get_dead_memory_ids, get_perception_cleanup_update,
    propose_move_toward, propose_move_away, propose_retreat_home,
    is_in_hostile_town, should_flee
)
from src.actions.base import (
    ActionType, ActionProposal, IntentUpdate, 
    NavigationUpdate, PerceptionUpdate, ProgressionUpdate
)
from src.ai.tactical.contract import TacticalMode, TacticalRole, TacticalEvaluation


def get_weapon_range(actor: Entity) -> int:
    """Return the weapon range of the entity's equipped weapon (default 1 = melee)."""
    if actor.inventory and actor.inventory.weapon:
        weapon_tmpl = ITEM_REGISTRY.get(actor.inventory.weapon)
        if weapon_tmpl:
            return weapon_tmpl.weapon_range
    return 1


def best_ready_skill(ctx: AIContext, target_enemy: Entity | None = None) -> str | None:
    """Return the skill_id of the best ready active combat skill, or None."""
    from src.core.gameplay.classes import SKILL_DEFS, SkillTarget, SkillType
    import logging
    logger = logging.getLogger(__name__)
    
    actor = ctx.actor
    dist_to_enemy = 1
    if target_enemy:
        dist_to_enemy = actor.spatial.pos.manhattan(target_enemy.spatial.pos)

    best_id = None
    best_score = 0.0
    for si in actor.progression.skills:
        sdef = SKILL_DEFS.get(si.skill_id)
        if sdef is None:
            continue
        if not sdef: continue
        
        if not si.is_ready(): continue
        if sdef.skill_type != SkillType.ACTIVE:
            continue
        
        # Range check
        skill_range = sdef.range or 1
        if skill_range < dist_to_enemy: continue
        
        # Resource check
        cost = si.effective_stamina_cost(sdef.stamina_cost)
        if actor.progression.stamina < cost:
            continue
        
        # Scoring
        power = si.effective_power(sdef.power)
        radius = getattr(sdef, "radius", 0)
        
        # Scoring: power * multiplier (if AoE and multiple targets hit)
        hits = 1
        if radius > 0:
            # Determine AoE center
            center = actor.spatial.pos if sdef.target == SkillTarget.SELF else (target_enemy.spatial.pos if target_enemy else actor.spatial.pos)
            hits = 0
            for v in ctx.visible:
                 if ctx.faction_reg.is_hostile(actor.identity.faction, v.identity.faction):
                     belief = ctx.get_belief(v.id)
                     if not belief or (belief.visible_injury < 1.0 or belief.visible_injury == -1.0):
                         if center.manhattan(v.spatial.pos) <= radius:
                             hits += 1
        
        score = power * (hits if radius > 0 and hits > 1 else 1)
            
        if score > best_score:
            best_score = score
            best_id = si.skill_id
            
    return best_id


def can_use_potion(actor: Entity) -> str | None:
    """Return the best potion item_id the actor can use, or None."""
    if actor.inventory is None:
        return None
    for pid in ("large_hp_potion", "medium_hp_potion", "small_hp_potion"):
        if actor.inventory.has_consumable(pid):
            t = ITEM_REGISTRY.get(pid)
            if t and t.heal_amount > 0:
                return pid
    return None


class HuntHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        cleanup = get_perception_cleanup_update(actor, snapshot)
        final_updates = [cleanup] if cleanup else []

        # Leash enforcement
        from src.ai.states.base import beyond_leash
        if beyond_leash(actor, config.mob_leash_chase_multiplier):
            return propose_retreat_home(ctx, "Chase leash exceeded → returning home")

        if actor.spatial.leash_radius > 0 and actor.mind.navigation.chase_ticks >= config.mob_chase_give_up_ticks:
            return propose_retreat_home(ctx, "Chase timed out → returning home")

        enemy = ctx.nearest_enemy()
        if enemy is None:
            # Memory-based hunt
            memory = ctx.entity_memory
            if memory:
                # Target oldest memory for now
                eid = next(iter(memory))
                target_pos = memory[eid].pos
                if actor.spatial.pos.manhattan(target_pos) <= 1:
                    return AIState.WANDER, ActionProposal(
                        actor_id=actor.id, verb=ActionType.REST,
                        reason="Reached last known position, target gone → wander",
                        updates=[NavigationUpdate(chase_ticks=0), PerceptionUpdate(memory_remove=[eid])])
                return AIState.HUNT, propose_move_toward(
                    ctx, target_pos, "Hunting from memory", MovementIntention.PURSUIT,
                    updates=[NavigationUpdate(chase_ticks=actor.mind.navigation.chase_ticks + 1)])
            
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Lost target → back to wander",
                updates=[NavigationUpdate(chase_ticks=0)])

        # 1. Tactical Evaluation
        eval: TacticalEvaluation = ctx.tactical_hints.get("evaluation")
        if not eval or not eval.target_id:
            return AIState.WANDER, ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason="No tactical target")

        # 2. Targeted Enemy Retrieval
        enemy = snapshot.entities.get(eval.target_id)
        if not enemy:
             return AIState.WANDER, ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason="Tactical target missing")

        dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
        weapon_rng = get_weapon_range(actor)

        # 3. Deliberate Retreat
        if eval.mode == TacticalMode.RETREAT:
            return propose_retreat_home(ctx, eval.reason)

        # 4. Use Skills/Attacks if "Safe" (Milestone 4: Safe Shot)
        skill_id = best_ready_skill(ctx, enemy)
        if skill_id and (dist <= weapon_rng or eval.is_safe_shot):
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.USE_SKILL, target=(skill_id, enemy.id),
                reason=f"{eval.reason} + Skill {skill_id} ready",
                updates=[NavigationUpdate(chase_ticks=0)])

        if dist <= weapon_rng and eval.mode != TacticalMode.WIDEN:
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                reason=f"{eval.reason} + Attacking {enemy.id}",
                updates=[NavigationUpdate(chase_ticks=0)])

        # 5. Handle yielding/deadlocks
        if (dist == 2
                and enemy.mind.decision.ai_state in (AIState.HUNT, AIState.COMBAT)
                and actor.id > enemy.id):
            return AIState.HUNT, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Yielding to let enemy {enemy.id} close gap (anti-deadlock)")

        # 6. Tactical Movement
        if eval.mode in (TacticalMode.COVER, TacticalMode.CHOKEPOINT):
             if eval.target_pos:
                 target_vec = Vector2(eval.target_pos[0], eval.target_pos[1])
                 if actor.spatial.pos != target_vec:
                     return AIState.HUNT, propose_move_toward(ctx, target_vec, eval.reason, MovementIntention.REPOSITION, updates=[NavigationUpdate(chase_ticks=actor.mind.navigation.chase_ticks + 1)])
        
        if eval.mode == TacticalMode.WIDEN:
             return AIState.HUNT, propose_move_away(ctx, enemy.spatial.pos, eval.reason, MovementIntention.REPOSITION, updates=[NavigationUpdate(chase_ticks=actor.mind.navigation.chase_ticks + 1)])
        
        if eval.mode == TacticalMode.MAINTAIN and dist == eval.preferred_dist:
             return AIState.HUNT, ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason="Maintaining distance (Waiting)")

        # Default Pursuit
        return AIState.HUNT, propose_move_toward(
            ctx, enemy.spatial.pos, eval.reason, MovementIntention.PURSUIT,
            updates=[NavigationUpdate(chase_ticks=actor.mind.navigation.chase_ticks + 1)])


class CombatHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        cleanup = get_perception_cleanup_update(actor, snapshot)
        final_updates = [cleanup] if cleanup else []

        # 1. Tactical Evaluation
        eval: TacticalEvaluation = ctx.tactical_hints.get("evaluation")
        if not eval or not eval.target_id:
            return AIState.WANDER, ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason="No tactical target")

        enemy = snapshot.entities.get(eval.target_id)
        if not enemy:
            return AIState.WANDER, ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason="Combat target lost")

        # 2. Deliberate Retreat
        if eval.mode == TacticalMode.RETREAT:
            potion_id = can_use_potion(actor)
            if potion_id:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.USE_ITEM, target=potion_id,
                    reason=f"Retreating + Using {potion_id}",
                    updates=[NavigationUpdate(chase_ticks=0)])
            return propose_retreat_home(ctx, eval.reason)

        dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
        weapon_rng = get_weapon_range(actor)

        # 3. Action Selection
        skill_id = best_ready_skill(ctx, enemy)
        if skill_id and (dist <= weapon_rng or eval.is_safe_shot):
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.USE_SKILL, target=(skill_id, enemy.id),
                reason=f"{eval.reason} + Using skill {skill_id}",
                updates=final_updates)

        # 4. Tactical Intent: Support / Coordination
        support_id = ctx.tactical_hints.get("support_target_id")
        if support_id:
            target = snapshot.entities.get(support_id)
            if target:
                ally_belief = ctx.get_belief(target.id)
                if ally_belief and ally_belief.visible_injury < 1.0:
                    support_skill = best_ready_skill(ctx, target)
                    if support_skill:
                        return AIState.COMBAT, ActionProposal(
                            actor_id=actor.id, verb=ActionType.USE_SKILL, target=(support_skill, target.id),
                            reason=f"Supporting ally {target.id}")
                    return AIState.COMBAT, propose_move_toward(ctx, target.spatial.pos, f"Moving to support {target.id}", MovementIntention.REGROUP, updates=[NavigationUpdate(chase_ticks=0)])

        # 5. Tactical Movement vs Attack
        if eval.mode in (TacticalMode.COVER, TacticalMode.CHOKEPOINT):
             if eval.target_pos:
                 target_vec = Vector2(eval.target_pos[0], eval.target_pos[1])
                 if actor.spatial.pos != target_vec:
                     return AIState.COMBAT, propose_move_toward(ctx, target_vec, eval.reason, MovementIntention.REPOSITION)

        if dist <= weapon_rng:
            if eval.mode == TacticalMode.WIDEN:
                return AIState.COMBAT, propose_move_away(ctx, enemy.spatial.pos, eval.reason, MovementIntention.REPOSITION)
                
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                reason=f"{eval.reason} + Attacking {enemy.id}",
                updates=[NavigationUpdate(chase_ticks=0)])

        # Pursuit
        return AIState.HUNT, propose_move_toward(
            ctx, enemy.spatial.pos, eval.reason, MovementIntention.PURSUIT)


class FleeHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        cleanup = get_perception_cleanup_update(actor, snapshot)
        final_updates = [cleanup] if cleanup else []
        enemy = ctx.nearest_enemy()

        if enemy is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Safe or recovered → stop fleeing",
                updates=[NavigationUpdate(chase_ticks=0)])

        return AIState.FLEE, propose_move_away(
            ctx, enemy.spatial.pos, f"Fleeing from enemy {enemy.id}", MovementIntention.RETREAT,
            updates=final_updates + [NavigationUpdate(chase_ticks=0)])


class AlertHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        cleanup = get_perception_cleanup_update(actor, snapshot)
        final_updates = [cleanup] if cleanup else []
        enemy = ctx.nearest_enemy()

        if enemy is not None:
            if actor.spatial.pos.manhattan(enemy.spatial.pos) <= 1:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                    reason=f"Alert! Attacking intruder {enemy.id}",
                updates=[NavigationUpdate(chase_ticks=0)])
            return AIState.HUNT, propose_move_toward(
                ctx, enemy.spatial.pos, f"Alert! Chasing intruder {enemy.id}", MovementIntention.PURSUIT)

        from src.ai.states.base import is_on_home_territory
        if is_on_home_territory(ctx):
            return AIState.GUARD_CAMP, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Alert over → resuming guard duty")
        return propose_retreat_home(ctx, "Alert over → heading home")
