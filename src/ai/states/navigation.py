from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

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
from src.core.models.enums import HeroClass, LeadKind, MovementIntention


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
                        ctx, target.spatial.pos, f"Following leader {target.id}",
                        MovementIntention.REGROUP, updates=final_updates)

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
                    ctx, loot_pos, "Loot nearby → moving to pick up",
                    MovementIntention.REPOSITION, updates=final_updates)

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
                        ctx, res.spatial.pos, f"Resource nearby → moving to {res.name}",
                        MovementIntention.REPOSITION, updates=final_updates)

        if enemy is not None:
            dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
            # get_weapon_range in combat.py
            from src.ai.states.combat import get_weapon_range
            weapon_rng = get_weapon_range(actor)
            
            if dist <= weapon_rng:
                from src.ai.states.combat import best_ready_skill
                skill_id = best_ready_skill(ctx, enemy)
                
                if skill_id:
                    return AIState.COMBAT, ActionProposal(
                        actor_id=actor.id, verb=ActionType.USE_SKILL, target=(skill_id, enemy.id),
                        reason=f"Enemy adjacent during wander (Unlocked) → using {skill_id}",
                        updates=final_updates)
                else:
                    return AIState.COMBAT, ActionProposal(
                        actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                        reason=f"Enemy in range during wander (Unlocked) → attacking",
                        updates=final_updates)

            return AIState.HUNT, propose_move_toward(
                ctx, enemy.spatial.pos, "Spotted enemy during wander (Unlocked) → hunting",
                MovementIntention.PURSUIT, updates=final_updates)

        if actor.identity.faction == Faction.HERO_GUILD and actor.progression.level >= 3:
            for em_id, em_rec in actor.mind.perception.entity_memory.items():
                # Simplified check for now (needs more robust memory data)
                em_pos = em_rec.pos
                if actor.spatial.pos.manhattan(em_pos) > 3:
                     return AIState.HUNT, propose_move_toward(
                        ctx, em_pos, f"Returning to fight remembered enemy #{em_id}",
                        MovementIntention.PURSUIT, updates=final_updates)

        rng_val = rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 999)
        frontier = Perception.find_frontier_target(actor, snapshot, rng_val)
        if frontier is not None:
            return AIState.WANDER, propose_move_toward(
                ctx, frontier, "Exploring unknown territory",
                MovementIntention.NONE, updates=final_updates)

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
                ctx, actor.spatial.home_pos, "Heading to town",
                MovementIntention.REGROUP, updates=final_updates)

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="No town to return to → wander",
            updates=final_updates)


# Removed redundant propose_retreat_home (moved to base.py)


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
                skill_id = best_ready_skill(ctx, target)
                if skill_id:
                    return AIState.COMBAT, ActionProposal(
                        actor_id=actor.id, verb=ActionType.USE_SKILL, target=(skill_id, target.id),
                        reason=f"Healing/Supporting ally {target.id} during hunt")

        camp = Perception.nearest_camp(actor, snapshot)
        if camp:
            return AIState.RETURN_TO_CAMP, propose_move_toward(
                ctx, camp, "Heading to camp", 
                MovementIntention.REGROUP, updates=final_updates + heal_meta)

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
                    ctx, enemy.spatial.pos, f"Camp guard chasing intruder {enemy.id}",
                    MovementIntention.PURSUIT, updates=final_updates)

        camp = Perception.nearest_camp(actor, snapshot)
        if camp:
            dist_to_camp = actor.spatial.pos.manhattan(camp)
            if dist_to_camp > config.camp_radius + 1:
                return AIState.GUARD_CAMP, propose_move_toward(
                    ctx, camp, "Patrol → returning closer to camp",
                    MovementIntention.GUARD, updates=final_updates)

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
        from src.ai.cognition_capacity import CognitionCapacityBuilder
        from src.ai.strategy.strategic_learning_service import StrategicLearningService
        
        actor, snapshot = ctx.actor, ctx.snapshot
        profile = CognitionCapacityBuilder.build(actor, tick=snapshot.tick)
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

        # 0. Confirmation by Sight [phase_3_task_1]
        if obj.leads:
            for lead in obj.leads:
                is_confirmed = False
                # AOA: Lead subject can be str or int. Snapshot keys are ints. [phase_3_task_1]
                lead_subject = lead.subject
                if isinstance(lead_subject, str) and lead_subject.isdigit():
                    lead_subject = int(lead_subject)
                
                if lead.kind == LeadKind.PERSON and lead_subject is not None:
                    if lead_subject in snapshot.entities:
                        # Seen the person! confirm.
                        is_confirmed = True
                elif lead.kind == LeadKind.LOCATION:
                    # If we can see the target tile and it's what we expected? 
                    # For now, just arrival is enough for location.
                    pass
                
                if is_confirmed:
                    learning_ups = StrategicLearningService.process_lead_outcome(ctx, lead, success=True, profile=profile)
                    # Consolidate: Merge objective clearance into the existing StrategicUpdate if present
                    final_ups = list(learning_ups)
                    strat_up = next((u for u in final_ups if isinstance(u, StrategicUpdate)), None)
                    if strat_up:
                         strat_up.current_objective_id = ""
                    else:
                         final_ups.append(StrategicUpdate(current_objective_id=""))
                    
                    return AIState.WANDER, ActionProposal(
                        actor_id=actor.id, verb=ActionType.REST,
                        reason=f"Intel confirmed by sight: {lead.label}",
                        updates=final_ups)

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
                    ctx, next_tile, f"Target area empty → narrowing search to {next_tile}",
                    updates=final_updates)
            else:
                # No more tiles or no zone → resolve lead as tested
                if obj.leads:
                    # Knowledge Continuity: Mark leads as tested and recalibrate trust [PHASE 3 INTEL CAPACITY]
                    for lead in obj.leads:
                        # If we reached here, the search is exhausted and we found nothing -> Failure
                        learning_ups = StrategicLearningService.process_lead_outcome(ctx, lead, success=False, profile=profile)
                        final_updates.extend(learning_ups)
                        
                    logger.info("InvestigateHandler: Exhausted search for %s leads. Recalibrating trust.", len(obj.leads))
                
                # Consolidate: Merge objective clearance into existing StrategicUpdate
                strat_up = next((u for u in final_updates if isinstance(u, StrategicUpdate)), None)
                if strat_up:
                     strat_up.current_objective_id = ""
                else:
                     final_updates.append(StrategicUpdate(current_objective_id=""))

                return AIState.WANDER, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason="Search space exhausted or lead resolved → clearing objective",
                    updates=final_updates)

        # 3. Tactical Movement
        return AIState.INVESTIGATING, propose_move_toward(
            ctx, target, f"Moving to investigate strategic lead at {target}",
            MovementIntention.INTERCEPT, updates=final_updates)
