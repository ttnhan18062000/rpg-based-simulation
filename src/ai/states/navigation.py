from __future__ import annotations

from src.actions.base import ActionType, ActionProposal
from src.ai.perception import Perception
from src.core.models.enums import AIState, Domain
from src.core.gameplay.faction import Faction
from src.core.models import DIRECTION_OFFSETS, Vector2
from src.ai.states.base import (
    AIContext, StateHandler, clear_dead_from_memory, 
    propose_move_toward, beyond_leash, propose_retreat_home,
    is_in_hostile_town, is_on_enemy_territory, is_tile_passable,
    should_flee
)


class IdleHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        clear_dead_from_memory(ctx.actor, ctx.snapshot)
        return AIState.WANDER, ActionProposal(
            actor_id=ctx.actor.id, verb=ActionType.REST,
            reason="Idle → transitioning to wander")


class WanderHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config, rng = ctx.actor, ctx.snapshot, ctx.config, ctx.rng
        clear_dead_from_memory(actor, snapshot)
        enemy = ctx.nearest_enemy()

        if beyond_leash(actor):
            actor.chase_ticks = 0
            return propose_retreat_home(ctx, "Beyond leash range → returning home")

        if is_in_hostile_town(ctx):
            if actor.stats.combat.hp_ratio < 0.6 or enemy is None:
                return propose_retreat_home(ctx, "Town aura burning → retreating")

        if is_on_enemy_territory(ctx) and actor.stats.combat.hp_ratio < 0.8:
            return propose_retreat_home(ctx, "On enemy territory while weakened → retreating")

        if actor.home_pos and actor.stats.combat.hp_ratio < 0.7:
            return propose_retreat_home(ctx, "Wounded → retreating home to heal")

        if actor.identity.faction == Faction.HERO_GUILD:
            loot_pos = Perception.ground_loot_nearby(actor, snapshot, radius=4)
            if loot_pos is not None:
                if actor.spatial.pos.manhattan(loot_pos) == 0:
                    return AIState.LOOTING, ActionProposal(
                        actor_id=actor.id, verb=ActionType.LOOT, target=loot_pos,
                        reason="Standing on loot → picking up")
                return AIState.LOOTING, propose_move_toward(
                    actor, loot_pos, snapshot, "Loot nearby → moving to pick up")

            if actor.inventory and actor.inventory.used_slots < actor.inventory.max_slots - 1:
                # find_nearby_resource is in town.py (or shared)
                # For now, I'll keep it as a local import or move to a common place
                from src.ai.states.interaction import find_nearby_resource
                res = find_nearby_resource(actor, snapshot, radius=5)
                if res is not None:
                    if actor.spatial.pos == res.spatial.pos:
                        actor.loot_progress = 0
                        return AIState.HARVESTING, ActionProposal(
                            actor_id=actor.id, verb=ActionType.HARVEST,
                            target=res.spatial.pos,
                            reason=f"Harvesting {res.name}")
                    return AIState.HARVESTING, propose_move_toward(
                        actor, res.spatial.pos, snapshot,
                        f"Resource nearby → moving to {res.name}")

        if enemy is not None:
            if should_flee(actor, config):
                return propose_retreat_home(ctx, "Low HP → retreating")
            
            mem = Perception.remembered_enemy_strength(actor, enemy.id)
            if mem and mem.get("atk", 0) > actor.stats.combat.atk * 1.5 and actor.stats.combat.hp_ratio < 0.7:
                return propose_retreat_home(ctx, "Enemy too strong from memory → retreating")
            
            dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
            # get_weapon_range in combat.py
            from src.ai.states.combat import get_weapon_range
            weapon_rng = get_weapon_range(actor)
            
            if dist <= weapon_rng:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                    reason=f"Engaging enemy {enemy.id} in range {dist}")

            return AIState.HUNT, propose_move_toward(
                actor, enemy.spatial.pos, snapshot, "Spotted enemy → hunting")

        if actor.identity.faction == Faction.HERO_GUILD and actor.stats.progression.level >= 3:
            for em in actor.entity_memory:
                if not em.get("visible", False) and em.get("kind", "").startswith("goblin"):
                    remembered_pos = Vector2(em["x"], em["y"])
                    if actor.spatial.pos.manhattan(remembered_pos) > 3:
                        em_atk = em.get("atk", 0)
                        if em_atk > 0 and actor.stats.combat.atk > em_atk * 1.2:
                            return AIState.HUNT, propose_move_toward(
                                actor, remembered_pos, snapshot,
                                f"Returning to fight remembered enemy #{em['id']}")

        rng_val = rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 999)
        frontier = Perception.find_frontier_target(actor, snapshot, rng_val)
        if frontier is not None:
            return AIState.WANDER, propose_move_toward(
                actor, frontier, snapshot, "Exploring unknown territory")

        direction_idx = rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 3)
        offset = DIRECTION_OFFSETS[direction_idx]
        target = actor.spatial.pos + offset
        if is_tile_passable(actor, target, snapshot):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.MOVE, target=target,
                reason="Wandering randomly")
        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Wander blocked → resting")


class ReturnToTownHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        clear_dead_from_memory(actor, snapshot)

        if Perception.is_in_town(actor, snapshot):
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Arrived at town → resting")

        if actor.home_pos:
            return AIState.RETURN_TO_TOWN, propose_move_toward(
                actor, actor.home_pos, snapshot, "Heading to town")

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="No town to return to → wander")


class ReturnToCampHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        clear_dead_from_memory(actor, snapshot)

        if actor.stats.combat.hp < actor.stats.combat.max_hp and config.mob_return_heal_rate > 0:
            heal = max(1, int(actor.stats.combat.max_hp * config.mob_return_heal_rate))
            actor.stats.combat.hp = min(actor.stats.combat.max_hp, actor.stats.combat.hp + heal)

        if Perception.is_in_camp(actor, snapshot):
            actor.chase_ticks = 0
            return AIState.GUARD_CAMP, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Arrived at camp → guarding")

        camp = Perception.nearest_camp(actor, snapshot)
        if camp:
            return AIState.RETURN_TO_CAMP, propose_move_toward(
                actor, camp, snapshot, "Heading to camp")

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="No camp to return to → wander")


class GuardCampHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config, rng = ctx.actor, ctx.snapshot, ctx.config, ctx.rng
        clear_dead_from_memory(actor, snapshot)
        enemy = ctx.nearest_enemy()

        if enemy is not None:
            if actor.spatial.pos.manhattan(enemy.spatial.pos) <= 1:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                    reason=f"Camp guard attacking intruder {enemy.id}")
            chase_range = max(4, actor.stats.vision_range)
            if actor.spatial.pos.manhattan(enemy.spatial.pos) <= chase_range:
                return AIState.HUNT, propose_move_toward(
                    actor, enemy.spatial.pos, snapshot, f"Camp guard chasing intruder {enemy.id}")

        camp = Perception.nearest_camp(actor, snapshot)
        if camp:
            dist_to_camp = actor.spatial.pos.manhattan(camp)
            if dist_to_camp > config.camp_radius + 1:
                return AIState.GUARD_CAMP, propose_move_toward(
                    actor, camp, snapshot, "Patrol → returning closer to camp")

        direction_idx = rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 3)
        offset = DIRECTION_OFFSETS[direction_idx]
        target = actor.spatial.pos + offset
        if is_tile_passable(actor, target, snapshot):
            return AIState.GUARD_CAMP, ActionProposal(
                actor_id=actor.id, verb=ActionType.MOVE, target=target,
                reason="Patrolling camp")
        return AIState.GUARD_CAMP, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Camp patrol blocked → resting")


class ExhaustedHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        return AIState.EXHAUSTED, ActionProposal(
            actor_id=ctx.actor.id,
            verb=ActionType.REST,
            reason="EXHAUSTED: Recovering stamina..."
        )
