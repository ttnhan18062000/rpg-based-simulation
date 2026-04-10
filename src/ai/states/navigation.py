from __future__ import annotations

from src.actions.base import ActionType, ActionProposal
from src.ai.perception import Perception
from src.core.models.enums import AIState, Domain
from src.core.gameplay.faction import Faction
from src.core.models import DIRECTION_OFFSETS, Vector2
from src.ai.states.base import (
    AIContext, StateHandler, get_dead_memory_ids, get_perception_cleanup_update, 
    propose_move_toward, beyond_leash, propose_retreat_home,
    is_in_hostile_town, is_on_enemy_territory, is_tile_passable,
    should_flee
)
from src.actions.base import (
    ActionType, ActionProposal, IntentUpdate, 
    InteractionUpdate, ProgressionUpdate, NavigationUpdate
)
from src.core.models.enums import HeroClass


class IdleHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        cleanup = get_perception_cleanup_update(actor, snapshot)
        final_updates = [cleanup] if cleanup else []
        return AIState.WANDER, ActionProposal(
            actor_id=ctx.actor.id, verb=ActionType.REST,
            reason="Idle → transitioning to wander",
            updates=final_updates)


class WanderHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config, rng = ctx.actor, ctx.snapshot, ctx.config, ctx.rng
        cleanup = get_perception_cleanup_update(actor, snapshot)
        final_updates = [cleanup] if cleanup else []
        enemy = ctx.nearest_enemy()

        if beyond_leash(actor):
            return propose_retreat_home(ctx, "Beyond leash range → returning home")
            
        # Social/Following Bias [PHASE 4]
        follow_id = ctx.tactical_hints.get("follow_target_id")
        if follow_id:
            target = snapshot.entities.get(follow_id)
            if target and target.combat.alive:
                dist = actor.spatial.pos.manhattan(target.spatial.pos)
                if dist > 3: # Keep distance but stay close
                    return AIState.WANDER, propose_move_toward(
                        actor, target.spatial.pos, snapshot, f"Following leader {target.id}",
                        updates=final_updates)

        if is_in_hostile_town(ctx):
            if actor.combat.hp_ratio < 0.6 or enemy is None:
                return propose_retreat_home(ctx, "Town aura burning → retreating")

        if is_on_enemy_territory(ctx) and actor.combat.hp_ratio < 0.8:
            return propose_retreat_home(ctx, "On enemy territory while weakened → retreating")

        if actor.spatial.home_pos and actor.combat.hp_ratio < 0.7:
            return propose_retreat_home(ctx, "Wounded → retreating home to heal")

        if actor.identity.faction == Faction.HERO_GUILD:
            loot_pos = Perception.ground_loot_nearby(actor, snapshot, radius=4)
            if loot_pos is not None:
                if actor.spatial.pos.manhattan(loot_pos) == 0:
                    return AIState.LOOTING, ActionProposal(
                        actor_id=actor.id, verb=ActionType.LOOT, target=loot_pos,
                        reason="Standing on loot → picking up",
                        updates=final_updates)
                return AIState.LOOTING, propose_move_toward(
                    actor, loot_pos, snapshot, "Loot nearby → moving to pick up",
                    updates=final_updates)

            if actor.inventory and actor.inventory.used_slots < actor.inventory.max_slots - 1:
                # find_nearby_resource is in town.py (or shared)
                # For now, I'll keep it as a local import or move to a common place
                from src.ai.states.interaction import find_nearby_resource
                res = find_nearby_resource(actor, snapshot, radius=5)
                if res is not None:
                    if actor.spatial.pos == res.spatial.pos:
                        return AIState.HARVESTING, ActionProposal(
                            actor_id=actor.id, verb=ActionType.HARVEST,
                            target=res.spatial.pos,
                            reason=f"Harvesting {res.name}",
                            updates=[InteractionUpdate(loot_progress_set=0)])
                    return AIState.HARVESTING, propose_move_toward(
                        actor, res.spatial.pos, snapshot,
                        f"Resource nearby → moving to {res.name}",
                        updates=final_updates)

        if enemy is not None:
            if should_flee(actor, config):
                return propose_retreat_home(ctx, "Low HP → retreating")
            
            dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
            # get_weapon_range in combat.py
            from src.ai.states.combat import get_weapon_range
            weapon_rng = get_weapon_range(actor)
            
            if dist <= weapon_rng:
                # Use spatial index for O(1) cell lookup
                potential_ids = snapshot.nearby_entity_ids(actor.spatial.pos.x, actor.spatial.pos.y, 4)
                nearby_count = 0
                for eid in potential_ids:
                    if eid == actor.id: continue
                    e = snapshot.entities.get(eid)
                    if not e or not e.combat.alive: continue
                    if ctx.faction_reg.is_hostile(actor.identity.faction, e.identity.faction):
                        if e.spatial.pos.manhattan(actor.spatial.pos) <= 4:
                            nearby_count += 1
                
                from src.ai.states.combat import best_ready_skill
                
                skill_id = best_ready_skill(actor, dist, nearby_count)
                if skill_id:
                    return AIState.COMBAT, ActionProposal(
                        actor_id=actor.id, verb=ActionType.USE_SKILL, target=(skill_id, enemy.id),
                        reason=f"Skill {skill_id} ready during wander → using on {enemy.id}",
                        updates=final_updates)
                else:
                    return AIState.COMBAT, ActionProposal(
                        actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                        reason=f"Adjacent to enemy {enemy.id} during wander → basic attack",
                        updates=final_updates)
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                    reason=f"Engaging enemy {enemy.id} in range {dist}",
                    updates=final_updates)

            return AIState.HUNT, propose_move_toward(
                actor, enemy.spatial.pos, snapshot, "Spotted enemy → hunting",
                updates=final_updates)

        if actor.identity.faction == Faction.HERO_GUILD and actor.progression.level >= 3:
            for em_id, em_rec in actor.mind.perception.entity_memory.items():
                # Simplified check for now (needs more robust memory data)
                em_pos = em_rec.pos
                if actor.spatial.pos.manhattan(em_pos) > 3:
                     return AIState.HUNT, propose_move_toward(
                        actor, em_pos, snapshot,
                        f"Returning to fight remembered enemy #{em_id}",
                        updates=final_updates)

        rng_val = rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 999)
        frontier = Perception.find_frontier_target(actor, snapshot, rng_val)
        if frontier is not None:
            return AIState.WANDER, propose_move_toward(
                actor, frontier, snapshot, "Exploring unknown territory",
                updates=final_updates)

        direction_idx = rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 3)
        offset = DIRECTION_OFFSETS[direction_idx]
        target = actor.spatial.pos + offset
        if is_tile_passable(actor, target, snapshot):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.MOVE, target=target,
                reason="Wandering randomly",
                updates=final_updates)
        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Wander blocked → resting",
            updates=final_updates)


class ReturnToTownHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        cleanup = get_perception_cleanup_update(actor, snapshot)
        final_updates = [cleanup] if cleanup else []

        if Perception.is_in_town(actor, snapshot):
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Arrived at town → resting",
                updates=final_updates)

        if actor.spatial.home_pos:
            return AIState.RETURN_TO_TOWN, propose_move_toward(
                actor, actor.spatial.home_pos, snapshot, "Heading to town",
                updates=final_updates)

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="No town to return to → wander",
            updates=final_updates)


def propose_retreat_home(ctx: AIContext, reason: str) -> tuple[AIState, ActionProposal]:
    """Propose moving toward the actor's authoritative home or nearest generic camp."""
    actor = ctx.actor
    # Heroes go to TOWN, others go to CAMP
    state = AIState.RETURN_TO_TOWN if actor.identity.faction == Faction.HERO_GUILD else AIState.RETURN_TO_CAMP
    
    # 1. Authoritative Home Position [AOA AUTHORITATIVE]
    if actor.spatial.home_pos:
        return state, propose_move_toward(
            actor, actor.spatial.home_pos, ctx.snapshot, reason)
    
    # 2. Legacy Fallback: Nearest known camp [SUBJECTIVE RISK]
    camp = Perception.nearest_camp(actor, ctx.snapshot)
    if camp:
        return AIState.RETURN_TO_CAMP, propose_move_toward(
            actor, camp, ctx.snapshot, reason)
            
    enemy = ctx.nearest_enemy()
    if enemy:
        return AIState.FLEE, propose_move_away(actor, enemy.spatial.pos, ctx.snapshot, reason)
        
    return AIState.WANDER, ActionProposal(
        actor_id=actor.id, verb=ActionType.REST, reason=f"{reason} (nowhere to go)")


class ReturnToCampHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        cleanup = get_perception_cleanup_update(actor, snapshot)
        final_updates = [cleanup] if cleanup else []

        heal_rate = config.mob_return_heal_rate
        if actor.combat.hp < actor.combat.max_hp and heal_rate > 0:
            needed = actor.combat.max_hp - actor.combat.hp
            abs_heal = min(needed, max(1.0, actor.combat.max_hp * heal_rate))
            heal_meta = [ProgressionUpdate(hp_delta=int(abs_heal))]
        else:
            heal_meta = []

        if Perception.is_in_camp(actor, snapshot):
            return AIState.GUARD_CAMP, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Arrived at camp → guarding",
                updates=final_updates + heal_meta + [NavigationUpdate(chase_ticks=0)])

        # Support Bias during Hunt
        support_id = ctx.tactical_hints.get("support_target_id")
        if support_id:
            target = snapshot.entities.get(support_id)
            if target and target.combat.alive:
                dist_to_ally = actor.spatial.pos.manhattan(target.spatial.pos)
                from src.ai.states.combat import best_ready_skill
                skill_id = best_ready_skill(actor, dist_to_ally, 0)
                if skill_id:
                    return AIState.COMBAT, ActionProposal(
                        actor_id=actor.id, verb=ActionType.USE_SKILL, target=(skill_id, target.id),
                        reason=f"Healing/Supporting ally {target.id} during hunt")

        camp = Perception.nearest_camp(actor, snapshot)
        if camp:
            return AIState.RETURN_TO_CAMP, propose_move_toward(
                actor, camp, snapshot, "Heading to camp", 
                updates=final_updates + heal_meta)

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="No camp to return to → wander",
            updates=final_updates)


class GuardCampHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config, rng = ctx.actor, ctx.snapshot, ctx.config, ctx.rng
        cleanup = get_perception_cleanup_update(actor, snapshot)
        final_updates = [cleanup] if cleanup else []
        enemy = ctx.nearest_enemy()

        if enemy is not None:
            if actor.spatial.pos.manhattan(enemy.spatial.pos) <= 1:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                    reason=f"Camp guard attacking intruder {enemy.id}",
                    updates=final_updates)
            chase_range = max(4, actor.spatial.vision_range)
            if actor.spatial.pos.manhattan(enemy.spatial.pos) <= chase_range:
                return AIState.HUNT, propose_move_toward(
                    actor, enemy.spatial.pos, snapshot, f"Camp guard chasing intruder {enemy.id}",
                    updates=final_updates)

        camp = Perception.nearest_camp(actor, snapshot)
        if camp:
            dist_to_camp = actor.spatial.pos.manhattan(camp)
            if dist_to_camp > config.camp_radius + 1:
                return AIState.GUARD_CAMP, propose_move_toward(
                    actor, camp, snapshot, "Patrol → returning closer to camp",
                    updates=final_updates)

        direction_idx = rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 3)
        offset = DIRECTION_OFFSETS[direction_idx]
        target = actor.spatial.pos + offset
        if is_tile_passable(actor, target, snapshot):
            return AIState.GUARD_CAMP, ActionProposal(
                actor_id=actor.id, verb=ActionType.MOVE, target=target,
                reason="Patrolling camp",
                updates=final_updates)
        return AIState.GUARD_CAMP, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Camp patrol blocked → resting",
            updates=final_updates)


class ExhaustedHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        return AIState.EXHAUSTED, ActionProposal(
            actor_id=ctx.actor.id,
            verb=ActionType.REST,
            reason="EXHAUSTED: Recovering stamina..."
        )


class InvestigateHandler(StateHandler):
    """Handles movement toward a strategic lead. [PHASE 3]
    
    If the target is reached and the area is empty, it narrows the search 
    via SearchNarrowingService and moves to the next candidate tile.
    """
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        from src.core.models.strategy import ObjectiveKind, ProjectRecord
        from src.actions.base import StrategicUpdate
        from src.core.logic.search_narrowing import SearchNarrowingService
        
        actor, snapshot = ctx.actor, ctx.snapshot
        cleanup = get_perception_cleanup_update(actor, snapshot)
        final_updates = [cleanup] if cleanup else []

        obj = actor.mind.strategic.current_objective
        if not obj or obj.kind != ObjectiveKind.INVESTIGATE or not obj.target_pos:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="No valid investigation objective → wander",
                updates=final_updates)

        # 1. Update Persistent Search History [phase_3_task_8]
        hist_up = SearchNarrowingService.update_search_history(ctx)
        if hist_up:
            final_updates.append(hist_up)

        target = Vector2(x=obj.target_pos.x, y=obj.target_pos.y)
        dist = actor.spatial.pos.manhattan(target)

        # 2. Narrow Search on arrival
        if dist == 0:
            # Check for next search tile within relevant candidate zones
            zone_id = None
            if obj.leads:
                 zone_id = obj.leads[0].candidate_zone_ids[0] if obj.leads[0].candidate_zone_ids else None
            
            next_tile = SearchNarrowingService.select_next_search_tile(ctx, zone_id) if zone_id else None
            
            if next_tile:
                # Update current objective with new target_pos
                updated_obj = obj.model_copy(update={"target_pos": next_tile})
                prj = next((p for p in actor.mind.strategic.projects if p.project_id == obj.project_id), None)
                if prj:
                     updated_prj = prj.model_copy()
                     for i, o in enumerate(updated_prj.objectives):
                          if o.objective_id == obj.objective_id:
                               updated_prj.objectives[i] = updated_obj
                               break
                     final_updates.append(StrategicUpdate(projects_add_or_update=[updated_prj]))
                
                return AIState.INVESTIGATING, propose_move_toward(
                    actor, next_tile, snapshot, f"Target area empty → narrowing search to {next_tile}",
                    updates=final_updates)
            else:
                # No more tiles or no zone → resolve
                final_updates.append(StrategicUpdate(current_objective_id="")) 
                return AIState.WANDER, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason="Search space exhausted or lead resolved → clearing objective",
                    updates=final_updates)

        # 3. Tactical Movement
        return AIState.INVESTIGATING, propose_move_toward(
            actor, target, snapshot, f"Moving to investigate strategic lead at {target}",
            updates=final_updates)
