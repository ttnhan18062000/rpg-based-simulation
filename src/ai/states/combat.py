from __future__ import annotations

from src.actions.base import ActionType, ActionProposal
from src.ai.perception import Perception
from src.core.models.enums import AIState
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.entities.entity import Entity
from src.ai.states.base import (
    AIContext, StateHandler, get_dead_memory_ids, get_perception_cleanup_update,
    propose_move_toward, propose_move_away, propose_retreat_home,
    is_in_hostile_town, should_flee
)
from src.actions.base import (
    ActionType, ActionProposal, IntentUpdate, 
    NavigationUpdate, PerceptionUpdate, ProgressionUpdate
)


def get_weapon_range(actor: Entity) -> int:
    """Return the weapon range of the entity's equipped weapon (default 1 = melee)."""
    if actor.inventory and actor.inventory.weapon:
        weapon_tmpl = ITEM_REGISTRY.get(actor.inventory.weapon)
        if weapon_tmpl:
            return weapon_tmpl.weapon_range
    return 1


def best_ready_skill(actor: Entity, dist_to_enemy: int = 1, nearby_enemies: int = 1) -> str | None:
    """Return the skill_id of the best ready active combat skill, or None."""
    from src.core.gameplay.classes import SKILL_DEFS, SkillTarget, SkillType
    import logging
    logger = logging.getLogger(__name__)
    
    best_id = None
    best_score = 0.0
    # print(f"DEBUG_SKILL: Entity {actor.id} checking {len(actor.progression.skills)} skills. Dist={dist_to_enemy}, Nearby={nearby_enemies}")
    for si in actor.progression.skills:
        sdef = SKILL_DEFS.get(si.skill_id)
        if sdef is None:
            # print(f"  Skill {si.skill_id} NOT FOUND in SKILL_DEFS")
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
        aoe_radius = getattr(sdef, 'radius', 0) or 0
        score = power * (nearby_enemies if aoe_radius > 0 and nearby_enemies > 1 else 1)
        # print(f"  Skill {si.skill_id} SCORE={score} (power={power}, aoe={aoe_radius})")
            
        if score > best_score:
            best_score = score
            best_id = si.skill_id
            
    if best_id:
        print(f"DEBUG_SKILL_PICK: Entity {actor.id} picked {best_id} (score={best_score})")
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
            return propose_retreat_home(ctx, "Chase leash exceeded → returning home") # Note: propose_retreat_home adds its own updates

        if actor.spatial.leash_radius > 0 and actor.mind.navigation.chase_ticks >= config.mob_chase_give_up_ticks:
            return propose_retreat_home(ctx, "Chase timed out → returning home")

        if is_in_hostile_town(ctx) and actor.combat.hp_ratio < 0.6:
            return propose_retreat_home(ctx, "Town aura burning → aborting hunt")

        # Note: High-level brain (GoalEvaluator) already handles state transitions
        # We only keep critical overrides like Leash here.

        enemy = ctx.nearest_enemy()

        if enemy is None:
            memory = actor.mind.perception.entity_memory
            if memory:
                last_seen_id = min(memory.keys())
                target_pos = memory[last_seen_id]
                if actor.spatial.pos.manhattan(target_pos) <= 1:
                    return AIState.WANDER, ActionProposal(
                        actor_id=actor.id, verb=ActionType.REST,
                        reason="Reached last known position, target gone → wander",
                        updates=[NavigationUpdate(chase_ticks=0), PerceptionUpdate(memory_remove=[last_seen_id])])
                return AIState.HUNT, propose_move_toward(
                    actor, target_pos, snapshot, "Hunting from memory",
                    updates=[NavigationUpdate(chase_ticks=actor.mind.navigation.chase_ticks + 1)])
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Lost target → back to wander",
                updates=[NavigationUpdate(chase_ticks=0)])

        weapon_rng = get_weapon_range(actor)
        dist = actor.spatial.pos.manhattan(enemy.spatial.pos)

        # 1. Action Preference: Skill > Attack
        nearby_count = sum(
            1 for v in ctx.visible if ctx.faction_reg.is_hostile(actor.identity.faction, v.identity.faction)
            and v.combat.alive and actor.spatial.pos.manhattan(v.spatial.pos) <= 4
        )
        skill_id = best_ready_skill(actor, dist, nearby_count)
        if skill_id:
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.USE_SKILL, target=(skill_id, enemy.id),
                reason=f"Using skill {skill_id} on enemy {enemy.id} (dist={dist})",
                updates=[NavigationUpdate(chase_ticks=0)])

        # 2. Basic Attack
        if dist <= weapon_rng:
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                reason=f"In range of enemy {enemy.id} (dist={dist}, range={weapon_rng}) → attacking",
                updates=[NavigationUpdate(chase_ticks=0)])

        # 3. Handle deadlocks (yielding)
        if (dist == 2
                and enemy.mind.decision.ai_state in (AIState.HUNT, AIState.COMBAT)
                and actor.id > enemy.id):
            return AIState.HUNT, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Yielding to let enemy {enemy.id} close gap (anti-deadlock)")

        # 4. Tactical Intent: Skirmish (Kiting)
        if ctx.tactical_hints.get("skirmish") and dist < ctx.tactical_hints.get("min_dist", 3):
            return AIState.HUNT, propose_move_away(actor, enemy.spatial.pos, snapshot, "Skirmishing (kiting) to maintain distance", updates=[NavigationUpdate(chase_ticks=actor.mind.navigation.chase_ticks + 1)])

        # 5. Move closer
        return AIState.HUNT, propose_move_toward(
            actor, enemy.spatial.pos, snapshot, f"Hunting enemy {enemy.id}",
            updates=[NavigationUpdate(chase_ticks=actor.mind.navigation.chase_ticks + 1)])


class CombatHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        cleanup = get_perception_cleanup_update(actor, snapshot)
        final_updates = [cleanup] if cleanup else []

        if is_in_hostile_town(ctx) and actor.combat.hp_ratio < 0.5:
            return propose_retreat_home(ctx, "Town aura burning → disengaging from combat")

        if actor.combat.hp_ratio < 0.5:
            potion_id = can_use_potion(actor)
            if potion_id:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.USE_ITEM, target=potion_id,
                    reason=f"Low HP → using {potion_id}",
                    updates=[NavigationUpdate(chase_ticks=0)])

        # Note: Brain handles state transitions

        enemy = ctx.nearest_enemy()
        if enemy is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Enemy vanished → returning to wander")

        dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
        weapon_rng = get_weapon_range(actor)

        # 1. Action Preference: Skill > Attack
        nearby_count = sum(
            1 for v in ctx.visible if ctx.faction_reg.is_hostile(actor.identity.faction, v.identity.faction)
            and v.combat.alive and actor.spatial.pos.manhattan(v.spatial.pos) <= 4
        )
        skill_id = best_ready_skill(actor, dist, nearby_count)
        if skill_id:
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.USE_SKILL, target=(skill_id, enemy.id),
                reason=f"Using skill {skill_id} on enemy {enemy.id} (dist={dist})",
                updates=final_updates)

        # 2. Tactical Intent: Support / Healing
        support_id = ctx.tactical_hints.get("support_target_id")
        if support_id:
            target = snapshot.entities.get(support_id)
            if target and target.combat.alive:
                # Prioritize support skill or move toward ally
                support_skill = best_ready_skill(actor, actor.spatial.pos.manhattan(target.spatial.pos), 0)
                if support_skill:
                    return AIState.COMBAT, ActionProposal(
                        actor_id=actor.id, verb=ActionType.USE_SKILL, target=(support_skill, target.id),
                        reason=f"Supporting ally {target.id}")
                return AIState.COMBAT, propose_move_toward(actor, target.spatial.pos, snapshot, f"Moving to support {target.id}", updates=[NavigationUpdate(chase_ticks=0)])

        # 3. Distance-based decision
        if dist <= weapon_rng:
            # Skirmish check: if too close, reposition
            if ctx.tactical_hints.get("skirmish") and dist < ctx.tactical_hints.get("min_dist", 1):
                return AIState.COMBAT, propose_move_away(actor, enemy.spatial.pos, snapshot, "Skirmishing (kiting) for breathing room")
                
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                reason=f"Attacking enemy {enemy.id} (dist={dist}, range={weapon_rng})",
                updates=[NavigationUpdate(chase_ticks=0)])

        return AIState.HUNT, propose_move_toward(
            actor, enemy.spatial.pos, snapshot, f"Enemy {enemy.id} out of range ({dist} > {weapon_rng}) → closing distance")


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
            actor, enemy.spatial.pos, snapshot, f"Fleeing from enemy {enemy.id}",
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
                actor, enemy.spatial.pos, snapshot, f"Alert! Chasing intruder {enemy.id}")

        from src.ai.states.base import is_on_home_territory
        if is_on_home_territory(ctx):
            return AIState.GUARD_CAMP, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Alert over → resuming guard duty")
        return propose_retreat_home(ctx, "Alert over → heading home")
