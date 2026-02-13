"""AI state handlers — class-based, faction-aware, extensible.

Architecture:
  - AIContext bundles all data a handler needs (actor, snapshot, config, rng,
    faction_reg).  Adding new context (e.g. weather) only requires extending
    AIContext, not every handler signature.
  - Each handler is a class implementing the ``handle`` method.
  - Handlers are registered in STATE_HANDLERS by AIState key; new states are
    added by creating a class and inserting one dict entry.
  - Enemy/ally detection delegates to the FactionRegistry — adding a new
    faction or changing alliances requires zero handler changes.
  - Territory tiles are passable for everyone but hostile territory applies
    debuffs and triggers alerts (see WorldLoop).

State machine:
  IDLE → WANDER
  WANDER → HUNT | RETURN_HOME (low HP) | LOOTING (loot nearby)
  HUNT → COMBAT (adjacent) | FLEE (low HP) | WANDER (lost target)
  COMBAT → FLEE/RETURN_HOME (low HP) | HUNT (enemy retreated) |
           WANDER (enemy dead) | USE_ITEM (potion)
  FLEE → RETURN_HOME | WANDER (safe) | HUNT (HP recovered)
  RETURN_TO_TOWN → RESTING_IN_TOWN (arrived) | RETURN_TO_TOWN (moving)
  RESTING_IN_TOWN → WANDER (fully healed)
  RETURN_TO_CAMP → GUARD_CAMP (arrived) | RETURN_TO_CAMP (moving)
  GUARD_CAMP → HUNT (enemy visible) | GUARD_CAMP (patrol)
  LOOTING → WANDER (done) | LOOTING (moving)
  ALERT → HUNT (enemy found) | GUARD_CAMP/RETURN_HOME (no enemy)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.ai.perception import Perception
from src.core.buildings import (
    Building, RECIPES, RECIPE_MAP, SHOP_INVENTORY,
    can_craft, item_sell_price, shop_buy_price,
)
from src.core.enums import AIState, ActionType, Domain, EntityRole
from src.core.faction import Faction, FactionRegistry
from src.core.items import ITEM_REGISTRY, ItemType
from src.core.models import DIRECTION_OFFSETS, Entity, Vector2

if TYPE_CHECKING:
    from src.config import SimulationConfig
    from src.core.snapshot import Snapshot
    from src.systems.rng import DeterministicRNG


# =====================================================================
# AI Context — single object passed to every handler
# =====================================================================

@dataclass(slots=True)
class AIContext:
    """All data a state handler might need.  Extend this to add weather,
    quests, etc. without changing handler signatures."""

    actor: Entity
    snapshot: Snapshot
    config: SimulationConfig
    rng: DeterministicRNG
    faction_reg: FactionRegistry

    # -- cached helpers (lazily populated) --

    _visible: list[Entity] | None = None

    @property
    def visible(self) -> list[Entity]:
        if self._visible is None:
            self._visible = Perception.visible_entities(
                self.actor, self.snapshot, self.actor.stats.vision_range)
        return self._visible

    def nearest_enemy(self) -> Entity | None:
        return Perception.nearest_enemy(self.actor, self.visible, self.faction_reg)

    def nearest_ally(self) -> Entity | None:
        return Perception.nearest_ally(self.actor, self.visible, self.faction_reg)


# =====================================================================
# Shared helpers
# =====================================================================

def is_tile_passable(actor: Entity, pos: Vector2, snapshot: Snapshot) -> bool:
    """Check if *pos* is walkable terrain.

    Territory tiles (TOWN, CAMP) are passable for everyone.
    The consequence of entering enemy territory is handled by the WorldLoop
    (debuff + alert), not by blocking movement.
    """
    return snapshot.grid.is_walkable(pos)


def propose_move_toward(actor: Entity, target_pos: Vector2, snapshot: Snapshot, reason: str) -> ActionProposal:
    """Propose a MOVE one step toward *target_pos*, with perpendicular fallback."""
    direction = Perception.direction_toward(actor.pos, target_pos)
    dest = actor.pos + direction
    if is_tile_passable(actor, dest, snapshot):
        return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=dest, reason=reason)
    dx = target_pos.x - actor.pos.x
    dy = target_pos.y - actor.pos.y
    alternates = [Vector2(0, 1), Vector2(0, -1)] if abs(dx) >= abs(dy) else [Vector2(1, 0), Vector2(-1, 0)]
    for alt in alternates:
        alt_dest = actor.pos + alt
        if is_tile_passable(actor, alt_dest, snapshot):
            return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=alt_dest, reason=f"{reason} (detour)")
    return ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason=f"{reason} (path blocked)")


def propose_move_away(actor: Entity, threat_pos: Vector2, snapshot: Snapshot, reason: str) -> ActionProposal:
    """Propose a MOVE one step away from *threat_pos*."""
    direction = Perception.direction_away_from(actor.pos, threat_pos)
    dest = actor.pos + direction
    if is_tile_passable(actor, dest, snapshot):
        return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=dest, reason=reason)
    perps = [Vector2(-direction.y, direction.x), Vector2(direction.y, -direction.x)]
    for p in perps:
        alt = actor.pos + p
        if is_tile_passable(actor, alt, snapshot):
            return ActionProposal(actor_id=actor.id, verb=ActionType.MOVE, target=alt, reason=f"{reason} (side step)")
    return ActionProposal(actor_id=actor.id, verb=ActionType.REST, reason=f"{reason} (flee blocked)")


def should_flee(actor: Entity, config: SimulationConfig) -> bool:
    """Check if entity HP is below flee threshold."""
    return actor.stats.hp_ratio <= config.flee_hp_threshold


def clear_dead_from_memory(actor: Entity, snapshot: Snapshot) -> None:
    """Remove dead or missing entities from memory."""
    dead_ids = [eid for eid in actor.memory if eid not in snapshot.entities or not snapshot.entities[eid].alive]
    for eid in dead_ids:
        del actor.memory[eid]


def can_use_buildings(actor: Entity) -> bool:
    """Return True if the entity's role permits using town buildings.

    Only HERO (and future NPC) roles can use shops, guilds, etc.
    MOBs are always rejected — this is the single guard for all building handlers.
    """
    return actor.role in (EntityRole.HERO, EntityRole.NPC)


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


def beyond_leash(actor: Entity, multiplier: float = 1.0) -> bool:
    """True if a mob with a leash is beyond its allowed range from home."""
    if actor.leash_radius <= 0 or actor.home_pos is None:
        return False
    return actor.pos.manhattan(actor.home_pos) > int(actor.leash_radius * multiplier)


def propose_retreat_home(ctx: AIContext, reason: str) -> tuple[AIState, ActionProposal]:
    """Generic retreat: faction-aware.  Heroes → TOWN, goblins → CAMP."""
    actor = ctx.actor
    if actor.faction == Faction.HERO_GUILD and actor.home_pos:
        return AIState.RETURN_TO_TOWN, propose_move_toward(
            actor, actor.home_pos, ctx.snapshot, reason)
    camp = Perception.nearest_camp(actor, ctx.snapshot)
    if camp:
        return AIState.RETURN_TO_CAMP, propose_move_toward(
            actor, camp, ctx.snapshot, reason)
    # No home — just flee direction
    enemy = ctx.nearest_enemy()
    if enemy:
        return AIState.FLEE, propose_move_away(actor, enemy.pos, ctx.snapshot, reason)
    return AIState.WANDER, ActionProposal(
        actor_id=actor.id, verb=ActionType.REST, reason=f"{reason} (nowhere to go)")


def is_on_enemy_territory(ctx: AIContext) -> bool:
    """Check if actor is on hostile faction's territory tile."""
    return Perception.is_on_enemy_territory(ctx.actor, ctx.snapshot, ctx.faction_reg)


def is_on_home_territory(ctx: AIContext) -> bool:
    """Check if actor is on own faction's territory tile."""
    return Perception.is_on_home_territory(ctx.actor, ctx.snapshot, ctx.faction_reg)


def is_in_hostile_town(ctx: AIContext) -> bool:
    """Non-hero entity standing on a TOWN tile (takes aura damage)."""
    return (
        ctx.actor.faction != Faction.HERO_GUILD
        and ctx.snapshot.grid.is_town(ctx.actor.pos)
    )


def find_nearby_resource(actor: Entity, snapshot, radius: int = 6):
    """Find the nearest available resource node within radius."""
    best = None
    best_dist = radius + 1
    for node in snapshot.resource_nodes:
        if not node.is_available:
            continue
        dist = actor.pos.manhattan(node.pos)
        if dist < best_dist:
            best_dist = dist
            best = node
    return best


def find_building(snapshot, building_type: str) -> Building | None:
    """Find a building of the given type in the snapshot."""
    for b in snapshot.buildings:
        if b.building_type == building_type:
            return b
    return None


def hero_has_sellable_items(actor: Entity) -> bool:
    """Check if hero has items worth selling (non-equipped, non-consumable dupes)."""
    if not actor.inventory:
        return False
    for iid in actor.inventory.items:
        t = ITEM_REGISTRY.get(iid)
        if t is None:
            continue
        # Sell materials, gold pouches, and unneeded equipment
        if t.item_type == ItemType.MATERIAL:
            # Keep materials if hero has a craft target that needs them
            if actor.craft_target:
                recipe = RECIPE_MAP.get(actor.craft_target)
                if recipe and iid in recipe.materials:
                    continue
            return True
        if t.gold_value > 0:
            return True
        # Sell equipment that's worse than what's equipped
        if t.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
            equipped = _get_equipped_for_type(actor, t.item_type)
            if equipped:
                eq_t = ITEM_REGISTRY.get(equipped)
                if eq_t and _item_power(t) < _item_power(eq_t):
                    return True
    return False


def _get_equipped_for_type(actor: Entity, item_type: int) -> str | None:
    """Get the equipped item_id for a given ItemType."""
    if not actor.inventory:
        return None
    if item_type == ItemType.WEAPON:
        return actor.inventory.weapon
    elif item_type == ItemType.ARMOR:
        return actor.inventory.armor
    elif item_type == ItemType.ACCESSORY:
        return actor.inventory.accessory
    return None


def _item_power(t) -> int:
    """Simple heuristic for item power (used for comparison)."""
    return (t.atk_bonus + t.def_bonus + t.spd_bonus + t.max_hp_bonus
            + t.matk_bonus + t.mdef_bonus
            + int(t.crit_rate_bonus * 50) + int(t.evasion_bonus * 50))


def hero_wants_to_buy(actor: Entity) -> str | None:
    """Check if hero wants to buy something from the shop.

    Priority order:
    1. Healing potions if low (< 2)
    2. Equipment upgrades (best power gain per gold)
    3. Buff potions if none owned
    4. Crafting materials for active craft target

    Returns item_id or None.
    """
    if not actor.inventory:
        return None
    gold = actor.stats.gold
    inv = actor.inventory

    # --- Priority 1: Healing potions when low ---
    heal_potions = [
        ("large_hp_potion", 80), ("medium_hp_potion", 40), ("small_hp_potion", 15),
    ]
    total_heals = sum(inv.count_item(pid) for pid, _ in heal_potions)
    if total_heals < 2:
        for pid, price in heal_potions:
            if gold >= price and inv.can_add(pid):
                return pid

    # --- Priority 2: Equipment upgrades (best upgrade first) ---
    best_upgrade = None
    best_upgrade_gain = 0
    for iid, price in SHOP_INVENTORY:
        if gold < price:
            continue
        t = ITEM_REGISTRY.get(iid)
        if t is None:
            continue
        if t.item_type not in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
            continue
        equipped = _get_equipped_for_type(actor, t.item_type)
        new_power = _item_power(t)
        cur_power = 0
        if equipped:
            eq_t = ITEM_REGISTRY.get(equipped)
            if eq_t:
                cur_power = _item_power(eq_t)
        gain = new_power - cur_power
        if gain > best_upgrade_gain:
            best_upgrade_gain = gain
            best_upgrade = iid
    if best_upgrade:
        return best_upgrade

    # --- Priority 3: Buff potions if none owned ---
    buff_ids = ["atk_potion", "def_potion", "spd_potion"]
    for bid in buff_ids:
        if inv.count_item(bid) == 0:
            price = shop_buy_price(bid)
            if price and gold >= price and inv.can_add(bid):
                return bid

    # --- Priority 4: Materials for active craft target ---
    if actor.craft_target:
        recipe = RECIPE_MAP.get(actor.craft_target)
        if recipe:
            for mat_id, needed in recipe.materials.items():
                have = inv.items.count(mat_id)
                if have < needed:
                    price = shop_buy_price(mat_id)
                    if price and gold >= price and inv.can_add(mat_id):
                        return mat_id

    return None


def hero_should_visit_blacksmith(actor: Entity) -> bool:
    """Check if hero should visit blacksmith (to learn recipes or craft)."""
    if not actor.inventory:
        return False
    # If hero has no known recipes yet, visit to learn
    if not actor.known_recipes:
        return True
    # If hero has a craft target and can craft it, visit
    if actor.craft_target:
        recipe = RECIPE_MAP.get(actor.craft_target)
        if recipe and can_craft(recipe, actor.stats.gold, actor.inventory.items):
            return True
    return False


def hero_should_visit_guild(actor: Entity) -> bool:
    """Check if hero lacks enemy intel — guild can help with camps and terrain regions."""
    if not actor.entity_memory:
        return True
    # Visit guild if hero has no knowledge of any enemy race
    known_prefixes = {"goblin", "wolf", "bandit", "skeleton", "zombie", "lich", "orc"}
    known_kinds = {em.get("kind", "") for em in actor.entity_memory}
    has_any_enemy_knowledge = any(
        any(k.startswith(prefix) for prefix in known_prefixes)
        for k in known_kinds
    )
    return not has_any_enemy_knowledge


def get_weapon_range(actor: Entity) -> int:
    """Return the weapon range of the entity's equipped weapon (default 1 = melee)."""
    if actor.inventory and actor.inventory.weapon:
        weapon_tmpl = ITEM_REGISTRY.get(actor.inventory.weapon)
        if weapon_tmpl:
            return weapon_tmpl.weapon_range
    return 1


def best_ready_skill(actor: Entity, dist_to_enemy: int = 1) -> str | None:
    """Return the skill_id of the best ready active combat skill, or None.

    When *dist_to_enemy* > 1 (ranged), only considers skills whose range
    can reach the enemy.  Self/ally buffs are always considered.
    """
    from src.core.classes import SKILL_DEFS, SkillTarget, SkillType
    best_id = None
    best_power = 0.0
    for si in actor.skills:
        if not si.is_ready():
            continue
        sdef = SKILL_DEFS.get(si.skill_id)
        if sdef is None or sdef.skill_type != SkillType.ACTIVE:
            continue
        if sdef.target not in (SkillTarget.SINGLE_ENEMY, SkillTarget.AREA_ENEMIES,
                               SkillTarget.SELF, SkillTarget.AREA_ALLIES):
            continue
        # Range check: offensive skills must reach the enemy
        if sdef.target in (SkillTarget.SINGLE_ENEMY, SkillTarget.AREA_ENEMIES):
            skill_range = getattr(sdef, 'range', 1) or 1
            if skill_range < dist_to_enemy:
                continue
        cost = si.effective_stamina_cost(sdef.stamina_cost)
        if actor.stats.stamina < cost:
            continue
        power = si.effective_power(sdef.power)
        if power > best_power:
            best_power = power
            best_id = si.skill_id
    return best_id


def hero_should_visit_class_hall(actor: Entity) -> bool:
    """Check if hero should visit class hall to learn new skills or attempt breakthrough."""
    from src.core.classes import (
        HeroClass, available_class_skills, can_breakthrough, SKILL_DEFS,
    )
    try:
        hero_class = HeroClass(actor.hero_class)
    except (ValueError, KeyError):
        return False
    if hero_class == HeroClass.NONE:
        return False
    # Check if there are learnable skills the hero doesn't have yet
    known_ids = {s.skill_id for s in actor.skills}
    available = available_class_skills(hero_class, actor.stats.level)
    for sid in available:
        if sid not in known_ids:
            sdef = SKILL_DEFS.get(sid)
            if sdef and actor.stats.gold >= sdef.gold_cost:
                return True
    # Check if hero can attempt a breakthrough
    if actor.attributes and can_breakthrough(hero_class, actor.stats.level, actor.attributes):
        return True
    return False


def hero_should_visit_inn(actor: Entity) -> bool:
    """Check if hero has low stamina and would benefit from inn rest."""
    if actor.stats.max_stamina <= 0:
        return False
    return actor.stats.stamina < actor.stats.max_stamina * 0.4


# =====================================================================
# Base handler
# =====================================================================

class StateHandler(ABC):
    """Abstract base for AI state handlers.

    Subclass and implement ``handle`` to define behaviour for an AIState.
    """

    @abstractmethod
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        ...


# =====================================================================
# Handler implementations
# =====================================================================

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

        # Leash enforcement (enhance-04): mobs return home when too far
        if beyond_leash(actor):
            actor.chase_ticks = 0
            return propose_retreat_home(ctx, "Beyond leash range → returning home")

        # Town aura: hostiles in town take damage — retreat unless they can finish a kill
        if is_in_hostile_town(ctx):
            if actor.stats.hp_ratio < 0.6 or enemy is None:
                return propose_retreat_home(ctx, "Town aura burning → retreating")

        # On enemy territory → consider retreating (non-aggressive types)
        if is_on_enemy_territory(ctx) and actor.stats.hp_ratio < 0.8:
            return propose_retreat_home(ctx, "On enemy territory while weakened → retreating")

        # Wounded → return home to heal
        if actor.home_pos and actor.stats.hp_ratio < 0.7:
            return propose_retreat_home(ctx, "Wounded → retreating home to heal")

        # Heroes pick up nearby loot while wandering
        if actor.faction == Faction.HERO_GUILD:
            loot_pos = Perception.ground_loot_nearby(actor, snapshot, radius=4)
            if loot_pos is not None:
                if actor.pos.manhattan(loot_pos) == 0:
                    return AIState.LOOTING, ActionProposal(
                        actor_id=actor.id, verb=ActionType.LOOT, target=loot_pos,
                        reason="Standing on loot → picking up")
                return AIState.LOOTING, propose_move_toward(
                    actor, loot_pos, snapshot, "Loot nearby → moving to pick up")

            # Heroes harvest nearby resources when they have inventory space
            if actor.inventory and actor.inventory.used_slots < actor.inventory.max_slots - 1:
                res = find_nearby_resource(actor, snapshot, radius=5)
                if res is not None:
                    if actor.pos == res.pos:
                        actor.loot_progress = 0
                        return AIState.HARVESTING, ActionProposal(
                            actor_id=actor.id, verb=ActionType.HARVEST,
                            target=res.pos,
                            reason=f"Harvesting {res.name}")
                    return AIState.HARVESTING, propose_move_toward(
                        actor, res.pos, snapshot,
                        f"Resource nearby → moving to {res.name}")

        if enemy is not None:
            if should_flee(actor, config):
                return propose_retreat_home(ctx, "Low HP → retreating")
            # Check remembered strength — avoid if enemy was much stronger
            mem = Perception.remembered_enemy_strength(actor, enemy.id)
            if mem and mem.get("atk", 0) > actor.effective_atk() * 1.5 and actor.stats.hp_ratio < 0.7:
                return propose_retreat_home(ctx, "Enemy too strong from memory → retreating")
            return AIState.HUNT, propose_move_toward(
                actor, enemy.pos, snapshot, "Spotted enemy → hunting")

        # Hero: check memory for known camp locations to raid when strong enough
        if actor.faction == Faction.HERO_GUILD and actor.stats.level >= 3:
            for em in actor.entity_memory:
                if not em.get("visible", False) and em.get("kind", "").startswith("goblin"):
                    remembered_pos = Vector2(em["x"], em["y"])
                    if actor.pos.manhattan(remembered_pos) > 3:
                        em_atk = em.get("atk", 0)
                        if em_atk > 0 and actor.effective_atk() > em_atk * 1.2:
                            return AIState.HUNT, propose_move_toward(
                                actor, remembered_pos, snapshot,
                                f"Returning to fight remembered enemy #{em['id']}")

        # Frontier-based exploration instead of random movement
        rng_val = rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 999)
        frontier = Perception.find_frontier_target(actor, snapshot, rng_val)
        if frontier is not None:
            return AIState.WANDER, propose_move_toward(
                actor, frontier, snapshot, "Exploring unknown territory")

        # Fallback: random movement if no frontier
        direction_idx = rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 3)
        offset = DIRECTION_OFFSETS[direction_idx]
        target = actor.pos + offset
        if is_tile_passable(actor, target, snapshot):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.MOVE, target=target,
                reason="Wandering randomly")
        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Wander blocked → resting")


class HuntHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        clear_dead_from_memory(actor, snapshot)

        # Leash enforcement (enhance-04): abandon chase if too far from home
        if beyond_leash(actor, config.mob_leash_chase_multiplier):
            actor.chase_ticks = 0
            return propose_retreat_home(ctx, "Chase leash exceeded → returning home")

        # Chase give-up timer (enhance-04): abandon after too many ticks
        if actor.leash_radius > 0 and actor.chase_ticks >= config.mob_chase_give_up_ticks:
            actor.chase_ticks = 0
            return propose_retreat_home(ctx, "Chase timed out → returning home")

        # Town aura pressure: retreat at higher HP threshold
        if is_in_hostile_town(ctx) and actor.stats.hp_ratio < 0.6:
            return propose_retreat_home(ctx, "Town aura burning → aborting hunt")

        # Flee check
        if should_flee(actor, config):
            return propose_retreat_home(ctx, "Low HP → retreating from hunt")

        enemy = ctx.nearest_enemy()

        if enemy is None:
            actor.chase_ticks = 0
            # Check memory for last known positions
            if actor.memory:
                last_seen_id = min(actor.memory.keys())
                target_pos = actor.memory[last_seen_id]
                if actor.pos.manhattan(target_pos) <= 1:
                    del actor.memory[last_seen_id]
                    return AIState.WANDER, ActionProposal(
                        actor_id=actor.id, verb=ActionType.REST,
                        reason="Reached last known position, target gone → wander")
                return AIState.HUNT, propose_move_toward(
                    actor, target_pos, snapshot, "Hunting from memory")
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Lost target → back to wander")

        # Within weapon range → switch to combat (reset chase counter)
        weapon_rng = get_weapon_range(actor)
        dist = actor.pos.manhattan(enemy.pos)
        if dist <= weapon_rng:
            actor.chase_ticks = 0
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                reason=f"In range of enemy {enemy.id} (dist={dist}, range={weapon_rng}) → attacking")

        # Diagonal deadlock prevention (bug-01): when two mutually aggressive
        # entities are at Manhattan distance 2, both moving toward each other
        # can swap to the same distance. The higher-ID entity yields (rests)
        # so the lower-ID entity closes the gap unimpeded.
        if (actor.pos.manhattan(enemy.pos) == 2
                and enemy.ai_state in (AIState.HUNT, AIState.COMBAT)
                and actor.id > enemy.id):
            return AIState.HUNT, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Yielding to let enemy {enemy.id} close gap (anti-deadlock)")

        actor.chase_ticks += 1
        return AIState.HUNT, propose_move_toward(
            actor, enemy.pos, snapshot, f"Hunting enemy {enemy.id}")


class CombatHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        clear_dead_from_memory(actor, snapshot)

        # Town aura pressure: hostiles in town disengage sooner
        if is_in_hostile_town(ctx) and actor.stats.hp_ratio < 0.5:
            return propose_retreat_home(ctx, "Town aura burning → disengaging from combat")

        # Potion use
        if actor.stats.hp_ratio < 0.5:
            potion_id = can_use_potion(actor)
            if potion_id:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.USE_ITEM, target=potion_id,
                    reason=f"Low HP → using {potion_id}")

        # Flee check
        if should_flee(actor, config):
            return propose_retreat_home(ctx, "Low HP → retreating from combat")

        enemy = ctx.nearest_enemy()
        if enemy is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Enemy vanished → returning to wander")

        dist = actor.pos.manhattan(enemy.pos)
        weapon_rng = get_weapon_range(actor)

        # Can we attack from here? (within weapon range)
        if dist <= weapon_rng:
            # Try to use a skill first (pass distance for range-aware selection)
            skill_id = best_ready_skill(actor, dist)
            if skill_id:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.USE_SKILL, target=skill_id,
                    reason=f"Using skill {skill_id} on enemy {enemy.id} (dist={dist})")

            # Ranged kiting: if we're a ranged attacker and enemy is adjacent,
            # try to back away to maintain distance (only if HP is okay)
            if weapon_rng >= 3 and dist <= 1 and actor.stats.hp_ratio > 0.6:
                return AIState.COMBAT, propose_move_away(
                    actor, enemy.pos, snapshot, f"Kiting enemy {enemy.id} → maintaining range")

            # Basic attack (melee or ranged)
            return AIState.COMBAT, ActionProposal(
                actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                reason=f"Attacking enemy {enemy.id} (dist={dist}, range={weapon_rng})")

        # Out of weapon range — close the gap
        return AIState.HUNT, propose_move_toward(
            actor, enemy.pos, snapshot, f"Enemy {enemy.id} out of range → closing distance")


class FleeHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        clear_dead_from_memory(actor, snapshot)
        enemy = ctx.nearest_enemy()

        # Always prefer retreating home
        if actor.home_pos:
            if is_on_home_territory(ctx):
                if actor.faction == Faction.HERO_GUILD:
                    return AIState.RESTING_IN_TOWN, ActionProposal(
                        actor_id=actor.id, verb=ActionType.REST,
                        reason="Reached home → resting in safety")
                return AIState.GUARD_CAMP, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason="Reached camp → guarding")
            return propose_retreat_home(ctx, "Fleeing → heading home")

        if enemy is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="No threats visible → recovering")

        if actor.stats.hp_ratio > config.flee_hp_threshold * 1.5:
            return AIState.HUNT, propose_move_toward(
                actor, enemy.pos, snapshot, "HP recovered → re-engaging")

        return AIState.FLEE, propose_move_away(
            actor, enemy.pos, snapshot, f"Fleeing from enemy {enemy.id}")


class ReturnToTownHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        clear_dead_from_memory(actor, snapshot)

        if Perception.is_in_town(actor, snapshot):
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Arrived at town → resting to heal")

        if actor.home_pos:
            return AIState.RETURN_TO_TOWN, propose_move_toward(
                actor, actor.home_pos, snapshot, "Heading to town")

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="No town to return to → wander")


class RestingInTownHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor = ctx.actor
        clear_dead_from_memory(actor, ctx.snapshot)

        if actor.stats.hp < actor.stats.max_hp:
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Resting in town ({actor.stats.hp}/{actor.stats.max_hp})")

        # Only entities with building access (HERO, NPC) use town activities
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Recovered → resuming patrol")

        # Fully healed → consider town activities before leaving
        snapshot = ctx.snapshot

        # 1. Sell items if bag has sellable stuff
        if hero_has_sellable_items(actor):
            store = find_building(snapshot, "store")
            if store:
                return AIState.VISIT_SHOP, propose_move_toward(
                    actor, store.pos, snapshot, "Heading to store to sell items")

        # 2. Buy upgrades if enough gold
        want_buy = hero_wants_to_buy(actor)
        if want_buy:
            store = find_building(snapshot, "store")
            if store:
                return AIState.VISIT_SHOP, propose_move_toward(
                    actor, store.pos, snapshot, f"Heading to store to buy {want_buy}")

        # 3. Visit blacksmith to learn recipes or craft
        if hero_should_visit_blacksmith(actor):
            bs = find_building(snapshot, "blacksmith")
            if bs:
                return AIState.VISIT_BLACKSMITH, propose_move_toward(
                    actor, bs.pos, snapshot, "Heading to blacksmith")

        # 4. Visit guild for intel
        if hero_should_visit_guild(actor):
            guild = find_building(snapshot, "guild")
            if guild:
                return AIState.VISIT_GUILD, propose_move_toward(
                    actor, guild.pos, snapshot, "Heading to guild for intel")

        # 5. Visit class hall to learn skills or attempt breakthrough
        if hero_should_visit_class_hall(actor):
            ch = find_building(snapshot, "class_hall")
            if ch:
                return AIState.VISIT_CLASS_HALL, propose_move_toward(
                    actor, ch.pos, snapshot, "Heading to class hall")

        # 6. Visit home to store items or upgrade storage
        if hero_should_visit_home(actor):
            if actor.home_pos:
                return AIState.VISIT_HOME, propose_move_toward(
                    actor, actor.home_pos, snapshot, "Heading home to manage storage")

        # 7. Visit inn for stamina recovery
        if hero_should_visit_inn(actor):
            inn = find_building(snapshot, "inn")
            if inn:
                return AIState.VISIT_INN, propose_move_toward(
                    actor, inn.pos, snapshot, "Heading to inn to recover stamina")

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Fully healed → leaving town to explore")


class ReturnToCampHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        clear_dead_from_memory(actor, snapshot)

        # Heal while returning home (enhance-04)
        if actor.stats.hp < actor.stats.max_hp and config.mob_return_heal_rate > 0:
            heal = max(1, int(actor.stats.max_hp * config.mob_return_heal_rate))
            actor.stats.hp = min(actor.stats.max_hp, actor.stats.hp + heal)

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
            if actor.pos.manhattan(enemy.pos) <= 1:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                    reason=f"Camp guard attacking intruder {enemy.id}")
            # Use entity's vision range for chase distance; guards chase aggressively
            chase_range = max(4, actor.stats.vision_range)
            if actor.pos.manhattan(enemy.pos) <= chase_range:
                return AIState.HUNT, propose_move_toward(
                    actor, enemy.pos, snapshot, f"Camp guard chasing intruder {enemy.id}")

        # Patrol near camp
        camp = Perception.nearest_camp(actor, snapshot)
        if camp:
            dist_to_camp = actor.pos.manhattan(camp)
            if dist_to_camp > config.camp_radius + 1:
                return AIState.GUARD_CAMP, propose_move_toward(
                    actor, camp, snapshot, "Patrol → returning closer to camp")

        direction_idx = rng.next_int(Domain.AI_DECISION, actor.id, snapshot.tick, 0, 3)
        offset = DIRECTION_OFFSETS[direction_idx]
        target = actor.pos + offset
        if is_tile_passable(actor, target, snapshot):
            return AIState.GUARD_CAMP, ActionProposal(
                actor_id=actor.id, verb=ActionType.MOVE, target=target,
                reason="Patrolling camp")
        return AIState.GUARD_CAMP, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Camp patrol blocked → resting")


class LootingHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot, config = ctx.actor, ctx.snapshot, ctx.config
        clear_dead_from_memory(actor, snapshot)

        # Abort looting if inventory is full — slots or weight (bug-02)
        if actor.inventory and actor.inventory.is_effectively_full:
            actor.loot_progress = 0
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Bag full → abandoning loot")

        key = (actor.pos.x, actor.pos.y)
        if key in snapshot.ground_items and snapshot.ground_items[key]:
            # Channel: increment loot_progress until loot_duration, then pick up
            if actor.loot_progress < config.loot_duration:
                actor.loot_progress += 1
                return AIState.LOOTING, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Looting... ({actor.loot_progress}/{config.loot_duration})")
            # Done channeling → actually pick up
            actor.loot_progress = 0
            return AIState.LOOTING, ActionProposal(
                actor_id=actor.id, verb=ActionType.LOOT, target=actor.pos,
                reason="Picking up loot")

        # Reset progress when not on a loot tile
        actor.loot_progress = 0

        loot_pos = Perception.ground_loot_nearby(actor, snapshot, radius=4)
        if loot_pos is not None:
            return AIState.LOOTING, propose_move_toward(
                actor, loot_pos, snapshot, "Moving to loot")

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="No more loot → wander")


class AlertHandler(StateHandler):
    """Responds to territory intrusion — seek and engage the intruder."""

    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        clear_dead_from_memory(actor, snapshot)
        enemy = ctx.nearest_enemy()

        if enemy is not None:
            if actor.pos.manhattan(enemy.pos) <= 1:
                return AIState.COMBAT, ActionProposal(
                    actor_id=actor.id, verb=ActionType.ATTACK, target=enemy.id,
                    reason=f"Alert! Attacking intruder {enemy.id}")
            return AIState.HUNT, propose_move_toward(
                actor, enemy.pos, snapshot, f"Alert! Chasing intruder {enemy.id}")

        # No enemy visible — return to normal duty
        if is_on_home_territory(ctx):
            return AIState.GUARD_CAMP, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Alert over → resuming guard duty")
        return propose_retreat_home(ctx, "Alert over → heading home")


class VisitShopHandler(StateHandler):
    """Hero visits the General Store to sell/buy items."""

    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        store = find_building(snapshot, "store")
        if store is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No store found")

        # Move to store if not there
        if actor.pos.manhattan(store.pos) > 0:
            return AIState.VISIT_SHOP, propose_move_toward(
                actor, store.pos, snapshot, "Walking to store")

        # At the store — perform transactions
        inv = actor.inventory
        if inv is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No inventory")

        # Phase 1: Sell items
        sold_any = False
        items_to_sell = []
        for iid in list(inv.items):
            t = ITEM_REGISTRY.get(iid)
            if t is None:
                continue
            should_sell = False
            if t.gold_value > 0:
                should_sell = True
            elif t.item_type == ItemType.MATERIAL:
                # Keep materials needed for craft target
                if actor.craft_target:
                    recipe = RECIPE_MAP.get(actor.craft_target)
                    if recipe and iid in recipe.materials:
                        needed = recipe.materials[iid]
                        have = inv.items.count(iid) - len([x for x in items_to_sell if x == iid])
                        if have <= needed:
                            continue
                should_sell = True
            elif t.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
                equipped = _get_equipped_for_type(actor, t.item_type)
                if equipped:
                    eq_t = ITEM_REGISTRY.get(equipped)
                    if eq_t and _item_power(t) < _item_power(eq_t):
                        should_sell = True
            if should_sell:
                items_to_sell.append(iid)

        total_gold = 0
        for iid in items_to_sell:
            if inv.remove_item(iid):
                price = item_sell_price(iid)
                actor.stats.gold += price
                total_gold += price
                sold_any = True

        if sold_any:
            return AIState.VISIT_SHOP, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Sold items for {total_gold}g (total gold: {actor.stats.gold})")

        # Phase 2: Buy items
        want = hero_wants_to_buy(actor)
        if want:
            price = shop_buy_price(want)
            if price and actor.stats.gold >= price and inv.can_add(want):
                actor.stats.gold -= price
                inv.add_item(want)
                # Auto-equip only if better than current gear
                inv.auto_equip_best(want)
                return AIState.VISIT_SHOP, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Bought {want} for {price}g")

        # Done shopping
        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Done shopping → checking other activities")


class VisitBlacksmithHandler(StateHandler):
    """Hero visits the Blacksmith to learn recipes or craft items."""

    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        bs = find_building(snapshot, "blacksmith")
        if bs is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No blacksmith found")

        # Move to blacksmith if not there
        if actor.pos.manhattan(bs.pos) > 0:
            return AIState.VISIT_BLACKSMITH, propose_move_toward(
                actor, bs.pos, snapshot, "Walking to blacksmith")

        inv = actor.inventory
        if inv is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No inventory")

        # Phase 1: Learn recipes if unknown
        if not actor.known_recipes:
            actor.known_recipes = [r.recipe_id for r in RECIPES]
            # Pick a craft target — the best item the hero doesn't have
            best_recipe = None
            best_power = -1
            for r in RECIPES:
                t = ITEM_REGISTRY.get(r.output_item)
                if t is None:
                    continue
                power = _item_power(t)
                equipped = _get_equipped_for_type(actor, t.item_type)
                if equipped:
                    eq_t = ITEM_REGISTRY.get(equipped)
                    if eq_t and power <= _item_power(eq_t):
                        continue
                if power > best_power:
                    best_power = power
                    best_recipe = r.recipe_id
            if best_recipe:
                actor.craft_target = best_recipe
            return AIState.VISIT_BLACKSMITH, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Learned {len(RECIPES)} recipes from blacksmith! Target: {actor.craft_target}")

        # Phase 2: Craft if possible
        if actor.craft_target:
            recipe = RECIPE_MAP.get(actor.craft_target)
            if recipe and can_craft(recipe, actor.stats.gold, inv.items):
                # Consume materials
                for mat_id, qty in recipe.materials.items():
                    for _ in range(qty):
                        inv.remove_item(mat_id)
                actor.stats.gold -= recipe.gold_cost
                # Add crafted item
                if inv.can_add(recipe.output_item):
                    inv.add_item(recipe.output_item)
                    t = ITEM_REGISTRY.get(recipe.output_item)
                    if t and t.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
                        inv.equip(recipe.output_item)
                actor.craft_target = None
                return AIState.VISIT_BLACKSMITH, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Crafted {recipe.output_item}!")

        # Not ready to craft — go gather materials
        if actor.craft_target:
            recipe = RECIPE_MAP.get(actor.craft_target)
            if recipe:
                missing = []
                for mat_id, qty in recipe.materials.items():
                    have = inv.items.count(mat_id)
                    if have < qty:
                        missing.append(f"{mat_id} ({have}/{qty})")
                gold_needed = max(0, recipe.gold_cost - actor.stats.gold)
                reason = f"Need: {', '.join(missing)}"
                if gold_needed > 0:
                    reason += f" + {gold_needed}g"
                return AIState.WANDER, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Left blacksmith to gather materials — {reason}")

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Nothing to craft → checking other activities")


class VisitGuildHandler(StateHandler):
    """Hero visits the Adventurer's Guild for intel."""

    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        guild = find_building(snapshot, "guild")
        if guild is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No guild found")

        # Move to guild if not there
        if actor.pos.manhattan(guild.pos) > 0:
            return AIState.VISIT_GUILD, propose_move_toward(
                actor, guild.pos, snapshot, "Walking to guild hall")

        # At the guild — provide intel about camps and terrain regions
        intel_added = False

        # Reveal all enemy camp locations
        for cx, cy in snapshot.camps:
            camp_key = (cx, cy)
            if camp_key not in actor.terrain_memory:
                actor.terrain_memory[camp_key] = 4  # CAMP tile type
                intel_added = True
            # Add nearby tiles to memory
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    k = (cx + dx, cy + dy)
                    if k not in actor.terrain_memory:
                        actor.terrain_memory[k] = 0  # rough knowledge

        # Reveal terrain region centers (resource-rich areas)
        regions_revealed = 0
        for node in snapshot.resource_nodes:
            nk = (node.pos.x, node.pos.y)
            if nk not in actor.terrain_memory:
                actor.terrain_memory[nk] = node.terrain.value if hasattr(node.terrain, 'value') else int(node.terrain)
                intel_added = True
                regions_revealed += 1

        if intel_added:
            parts = []
            if snapshot.camps:
                parts.append(f"{len(snapshot.camps)} camp locations")
            if regions_revealed:
                parts.append(f"{regions_revealed} resource nodes")
            return AIState.VISIT_GUILD, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Guild revealed {', '.join(parts)}!")

        # Generate a quest if the hero has room
        from src.core.quests import generate_quest, MAX_ACTIVE_QUESTS
        active_quests = [q for q in actor.quests if not q.completed]
        if len(active_quests) < MAX_ACTIVE_QUESTS:
            existing_ids = {q.quest_id for q in actor.quests}
            new_quest = generate_quest(
                hero_level=actor.stats.level,
                existing_quest_ids=existing_ids,
                rng=ctx.rng,
                entity_id=actor.id,
                tick=snapshot.tick,
                grid_width=snapshot.grid.width if hasattr(snapshot, 'grid') else 100,
                grid_height=snapshot.grid.height if hasattr(snapshot, 'grid') else 100,
            )
            if new_quest:
                actor.quests.append(new_quest)
                return AIState.VISIT_GUILD, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Accepted quest: {new_quest.title}")

        # Already know camps — provide material hints and terrain tips as goals
        from src.core.buildings import MATERIAL_HINTS
        if actor.craft_target:
            recipe = RECIPE_MAP.get(actor.craft_target)
            if recipe:
                for mat_id in recipe.materials:
                    hint = MATERIAL_HINTS.get(mat_id)
                    if hint and hint not in actor.goals:
                        actor.goals.append(f"Guild tip: {mat_id} — {hint}")

        # Add general terrain tips
        terrain_tips = [
            "Forests (green) host wolves — wolf pelts and fangs drop there.",
            "Deserts (tan) host bandits — fiber and raw gems found there.",
            "Swamps (purple) host undead — bone shards and ectoplasm drop there.",
            "Mountains (grey) host orcs — stone blocks and iron ore found there.",
        ]
        for tip in terrain_tips:
            if tip not in actor.goals:
                actor.goals.append(f"Guild tip: {tip}")

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Got intel from guild → planning next move")


class HarvestingHandler(StateHandler):
    """Hero channeling a resource harvest or moving toward a resource node."""

    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot

        # Interrupt: flee if low HP
        if should_flee(actor, ctx.config):
            actor.loot_progress = 0
            return propose_retreat_home(ctx, "Low HP → abandoning harvest")

        # Interrupt: enemy spotted while harvesting
        enemy = ctx.nearest_enemy()
        if enemy and actor.pos.manhattan(enemy.pos) <= 3:
            actor.loot_progress = 0
            return AIState.HUNT, propose_move_toward(
                actor, enemy.pos, snapshot, "Enemy nearby → abandoning harvest")

        # Find the resource node at our position
        res = None
        for node in snapshot.resource_nodes:
            if node.pos == actor.pos and node.is_available:
                res = node
                break

        if res is None:
            # Not on a resource — find nearest and move toward it
            res = find_nearby_resource(actor, snapshot, radius=8)
            if res is None:
                actor.loot_progress = 0
                return AIState.WANDER, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason="No resources available → wander")
            return AIState.HARVESTING, propose_move_toward(
                actor, res.pos, snapshot, f"Moving to {res.name}")

        # We're on a resource node — channel harvest
        actor.loot_progress += 1
        if actor.loot_progress >= res.harvest_ticks:
            actor.loot_progress = 0
            # Actually harvest in the world loop — for now propose HARVEST
            return AIState.HARVESTING, ActionProposal(
                actor_id=actor.id, verb=ActionType.HARVEST, target=res.pos,
                reason=f"Harvested {res.name} → got {res.yields_item}")
        return AIState.HARVESTING, ActionProposal(
            actor_id=actor.id, verb=ActionType.HARVEST, target=res.pos,
            reason=f"Harvesting {res.name} ({actor.loot_progress}/{res.harvest_ticks})")


class VisitClassHallHandler(StateHandler):
    """Hero visits the Class Hall to learn skills or attempt class breakthrough."""

    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        ch = find_building(snapshot, "class_hall")
        if ch is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No class hall found")

        # Move to class hall if not there
        if actor.pos.manhattan(ch.pos) > 0:
            return AIState.VISIT_CLASS_HALL, propose_move_toward(
                actor, ch.pos, snapshot, "Walking to class hall")

        from src.core.classes import (
            HeroClass, available_class_skills, can_breakthrough, can_learn_skill,
            SKILL_DEFS, BREAKTHROUGHS, CLASS_DEFS, SkillInstance,
        )
        try:
            hero_class = HeroClass(actor.hero_class)
        except (ValueError, KeyError):
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No class → leaving")

        # Phase 1: Learn new class skills (with mastery requirements)
        known_ids = {s.skill_id for s in actor.skills}
        available = available_class_skills(hero_class, actor.stats.level)
        for sid in available:
            if sid not in known_ids:
                sdef = SKILL_DEFS.get(sid)
                if sdef and actor.stats.gold >= sdef.gold_cost:
                    can_learn, reason = can_learn_skill(
                        sdef, actor.stats.level, actor.skills, actor.class_mastery)
                    if not can_learn:
                        continue
                    actor.stats.gold -= sdef.gold_cost
                    actor.skills.append(SkillInstance(skill_id=sid))
                    return AIState.VISIT_CLASS_HALL, ActionProposal(
                        actor_id=actor.id, verb=ActionType.REST,
                        reason=f"Learned skill: {sdef.name} (cost {sdef.gold_cost}g)")

        # Phase 2: Attempt breakthrough
        if actor.attributes and can_breakthrough(hero_class, actor.stats.level, actor.attributes):
            bt = BREAKTHROUGHS.get(hero_class)
            if bt:
                actor.hero_class = int(bt.to_class)
                new_cdef = CLASS_DEFS.get(bt.to_class)
                if new_cdef and actor.attribute_caps:
                    actor.attribute_caps.str_cap += new_cdef.str_cap_bonus
                    actor.attribute_caps.agi_cap += new_cdef.agi_cap_bonus
                    actor.attribute_caps.vit_cap += new_cdef.vit_cap_bonus
                    actor.attribute_caps.int_cap += new_cdef.int_cap_bonus
                    actor.attribute_caps.spi_cap += new_cdef.spi_cap_bonus
                    actor.attribute_caps.wis_cap += new_cdef.wis_cap_bonus
                    actor.attribute_caps.end_cap += new_cdef.end_cap_bonus
                    actor.attribute_caps.per_cap += new_cdef.per_cap_bonus
                    actor.attribute_caps.cha_cap += new_cdef.cha_cap_bonus
                return AIState.VISIT_CLASS_HALL, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"CLASS BREAKTHROUGH! → {bt.to_class.name} (Talent: {bt.talent})")

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Done at class hall → checking other activities")


class VisitInnHandler(StateHandler):
    """Hero rests at the Inn for rapid HP and stamina recovery."""

    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        inn = find_building(snapshot, "inn")
        if inn is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No inn found")

        # Move to inn if not there
        if actor.pos.manhattan(inn.pos) > 0:
            return AIState.VISIT_INN, propose_move_toward(
                actor, inn.pos, snapshot, "Walking to inn")

        # At the inn — rapid recovery
        healed = False
        # HP recovery: +10 per tick at inn
        if actor.stats.hp < actor.stats.max_hp:
            actor.stats.hp = min(actor.stats.hp + 10, actor.stats.max_hp)
            healed = True
        # Stamina recovery: +10 per tick at inn (on top of normal regen)
        if actor.stats.stamina < actor.stats.max_stamina:
            actor.stats.stamina = min(actor.stats.stamina + 10, actor.stats.max_stamina)
            healed = True
        # Attribute training from resting
        if actor.attributes and actor.attribute_caps:
            from src.core.attributes import train_attributes
            train_attributes(actor.attributes, actor.attribute_caps, "rest", stats=actor.stats)

        if healed:
            return AIState.VISIT_INN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Resting at inn (HP: {actor.stats.hp}/{actor.stats.max_hp}, "
                       f"STA: {actor.stats.stamina}/{actor.stats.max_stamina})")

        # Fully recovered
        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Fully recovered at inn → checking other activities")


# =====================================================================
# State: VISIT_HOME — hero visits home to store/retrieve items or upgrade
# =====================================================================

def hero_should_visit_home(actor: Entity) -> bool:
    """Check if hero has items worth storing at home or wants to upgrade."""
    if not actor.home_storage or not actor.inventory:
        return False
    # Visit home if inventory is nearly full and storage has space
    if actor.inventory.used_slots >= actor.inventory.max_slots - 2:
        if not actor.home_storage.is_full:
            return True
    # Visit home if hero can afford an upgrade
    cost = actor.home_storage.upgrade_cost()
    if cost is not None and actor.stats.gold >= cost:
        return True
    return False


class VisitHomeHandler(StateHandler):
    """Hero visits home to store items or upgrade storage."""

    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        if actor.home_pos is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No home set")

        # Move to home if not there
        if actor.pos.manhattan(actor.home_pos) > 0:
            return AIState.VISIT_HOME, propose_move_toward(
                actor, actor.home_pos, snapshot, "Walking home")

        inv = actor.inventory
        storage = actor.home_storage
        if inv is None or storage is None:
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No inventory/storage")

        # Phase 1: Upgrade storage if affordable
        cost = storage.upgrade_cost()
        if cost is not None and actor.stats.gold >= cost:
            actor.stats.gold -= cost
            old_max = storage.max_slots
            storage.upgrade()
            return AIState.VISIT_HOME, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Upgraded home storage {old_max}→{storage.max_slots} slots (-{cost}g)")

        # Phase 2: Store low-priority items (materials, weaker equipment, excess consumables)
        stored = []
        for iid in list(inv.items):
            if storage.is_full:
                break
            t = ITEM_REGISTRY.get(iid)
            if t is None:
                continue
            should_store = False
            # Store materials not needed for current craft
            if t.item_type == ItemType.MATERIAL:
                if actor.craft_target:
                    recipe = RECIPE_MAP.get(actor.craft_target)
                    if recipe and iid in recipe.materials:
                        needed = recipe.materials[iid]
                        have = inv.items.count(iid) - len([x for x in stored if x == iid])
                        if have <= needed:
                            continue
                should_store = True
            # Store equipment weaker than what's equipped
            elif t.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
                equipped = _get_equipped_for_type(actor, t.item_type)
                if equipped:
                    eq_t = ITEM_REGISTRY.get(equipped)
                    if eq_t and _item_power(t) < _item_power(eq_t):
                        should_store = True
            # Store excess consumables (keep 2 of each)
            elif t.item_type == ItemType.CONSUMABLE and t.heal_amount > 0:
                count_in_inv = inv.items.count(iid) - len([x for x in stored if x == iid])
                if count_in_inv > 2:
                    should_store = True

            if should_store:
                if inv.remove_item(iid) and storage.add_item(iid):
                    stored.append(iid)

        if stored:
            return AIState.VISIT_HOME, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Stored {len(stored)} items at home ({storage.used_slots}/{storage.max_slots})")

        # Done at home
        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Done at home → checking other activities")


# =====================================================================
# Handler registry — extend by adding entries
# =====================================================================

STATE_HANDLERS: dict[AIState, StateHandler] = {
    AIState.IDLE: IdleHandler(),
    AIState.WANDER: WanderHandler(),
    AIState.HUNT: HuntHandler(),
    AIState.COMBAT: CombatHandler(),
    AIState.FLEE: FleeHandler(),
    AIState.RETURN_TO_TOWN: ReturnToTownHandler(),
    AIState.RESTING_IN_TOWN: RestingInTownHandler(),
    AIState.RETURN_TO_CAMP: ReturnToCampHandler(),
    AIState.GUARD_CAMP: GuardCampHandler(),
    AIState.LOOTING: LootingHandler(),
    AIState.ALERT: AlertHandler(),
    AIState.VISIT_SHOP: VisitShopHandler(),
    AIState.VISIT_BLACKSMITH: VisitBlacksmithHandler(),
    AIState.VISIT_GUILD: VisitGuildHandler(),
    AIState.HARVESTING: HarvestingHandler(),
    AIState.VISIT_CLASS_HALL: VisitClassHallHandler(),
    AIState.VISIT_INN: VisitInnHandler(),
    AIState.VISIT_HOME: VisitHomeHandler(),
}
