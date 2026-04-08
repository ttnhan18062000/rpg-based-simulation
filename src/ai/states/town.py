from __future__ import annotations

from src.actions.base import (
    ActionType, ActionProposal, IntentUpdate, ProgressionUpdate, 
    IdentityUpdate, InteractionUpdate, PerceptionUpdate, MindUpdate,
    RoutineUpdate
)
from src.core.gameplay.buildings import (
    Building, RECIPES, RECIPE_MAP, SHOP_INVENTORY,
    can_craft, item_sell_price, shop_buy_price,
)
from src.core.models.enums import AIState, EntityRole
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.entities.entity import Entity
from src.core.gameplay.items.items import ItemType, _item_power
from src.ai.states.base import (
    AIContext, StateHandler, get_dead_memory_ids, get_perception_cleanup_update,
    propose_move_toward
)


def find_building(snapshot, building_type: str) -> Building | None:
    """Find a building of the given type in the snapshot."""
    for b in snapshot.buildings:
        if b.building_type == building_type:
            return b
    return None


def can_use_buildings(actor: Entity) -> bool:
    """Return True if the entity's role permits using town buildings."""
    return actor.identity.role in (EntityRole.HERO, EntityRole.NPC)


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




def hero_has_sellable_items(actor: Entity) -> bool:
    """Return True if the hero has items they would want to sell at a shop."""
    inv = actor.inventory
    if not inv or not inv.items:
        return False

    for iid in inv.items:
        t = ITEM_REGISTRY.get(iid)
        if t is None:
            continue
        
        # Direct gold value items
        if t.gold_value > 0:
            return True
            
        # Materials (unless needed for current craft target)
        if t.item_type == ItemType.MATERIAL:
            if actor.identity.craft_target:
                recipe = RECIPE_MAP.get(actor.identity.craft_target)
                if recipe and iid in recipe.materials:
                    needed = recipe.materials[iid]
                    if inv.items.count(iid) <= needed:
                        continue
            return True
            
        # Inferior equipment
        if t.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
            equipped = _get_equipped_for_type(actor, t.item_type)
            if equipped:
                eq_t = ITEM_REGISTRY.get(equipped)
                if eq_t and _item_power(t) < _item_power(eq_t):
                    return True
    return False


def hero_wants_to_buy(actor: Entity) -> str | None:
    """Check if hero wants to buy something from the shop."""
    if not actor.inventory:
        return None
    gold = actor.progression.gold
    inv = actor.inventory

    heal_potions = [
        ("large_hp_potion", 80), ("medium_hp_potion", 40), ("small_hp_potion", 15),
    ]
    total_heals = sum(inv.count_item(pid) for pid, _ in heal_potions)
    if total_heals < 2:
        for pid, price in heal_potions:
            if gold >= price and inv.can_add(pid):
                return pid

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

    buff_ids = ["atk_potion", "def_potion", "spd_potion"]
    for bid in buff_ids:
        if inv.count_item(bid) == 0:
            price = shop_buy_price(bid)
            if price and gold >= price and inv.can_add(bid):
                return bid

    if actor.identity.craft_target:
        recipe = RECIPE_MAP.get(actor.identity.craft_target)
        if recipe:
            for mat_id, needed in recipe.materials.items():
                have = inv.items.count(mat_id)
                if have < needed:
                    price = shop_buy_price(mat_id)
                    if price and gold >= price and inv.can_add(mat_id):
                        return mat_id

    return None


def hero_should_visit_blacksmith(actor: Entity) -> bool:
    if not actor.inventory:
        return False
    if not actor.identity.known_recipes:
        return True
    if actor.identity.craft_target:
        recipe = RECIPE_MAP.get(actor.identity.craft_target)
        if recipe and can_craft(recipe, actor.progression.gold, actor.inventory.items):
            return True
    return False


def hero_should_visit_guild(actor: Entity) -> bool:
    if not actor.mind.perception.entity_memory:
        return False
    known_prefixes = {"goblin", "wolf", "bandit", "skeleton", "zombie", "lich", "orc"}
    known_kinds = {em.get("kind", "") for em in actor.mind.perception.entity_memory.values() if isinstance(em, dict)}
    has_any_enemy_knowledge = any(
        any(k.startswith(prefix) for prefix in known_prefixes)
        for k in known_kinds
    )
    return not has_any_enemy_knowledge


def hero_should_visit_class_hall(actor: Entity) -> bool:
    from src.core.gameplay.classes import (
        HeroClass, available_class_skills, can_breakthrough, SKILL_DEFS,
    )
    try:
        hero_class = HeroClass(actor.progression.hero_class)
    except (ValueError, KeyError):
        return False
    if hero_class == HeroClass.NONE:
        return False
    known_ids = {s.skill_id for s in actor.progression.skills}
    available = available_class_skills(hero_class, actor.progression.level)
    for sid in available:
        if sid not in known_ids:
            sdef = SKILL_DEFS.get(sid)
            if sdef and actor.progression.gold >= sdef.gold_cost:
                return True
    if actor.progression.attributes and can_breakthrough(hero_class, actor.progression.level, actor.progression.attributes):
        return True
    return False


def hero_should_visit_inn(actor: Entity) -> bool:
    if actor.progression.max_stamina <= 0:
        return False
    # Stage 4: Routine Integration
    return actor.progression.stamina < actor.progression.max_stamina * 0.4 or actor.mind.routine.sleep_debt > 0.6


def hero_should_visit_home(actor: Entity) -> bool:
    """True if hero should go home to store items or upgrade."""
    # If we have items to store, we want to go home
    if actor.inventory and actor.inventory.used_slots >= actor.inventory.max_slots - 1:
        return True
        
    if not actor.inventory or not actor.inventory.home_storage:
        return False
        
    storage = actor.inventory.home_storage
    cost = storage.upgrade_cost()
    if cost is not None and actor.progression.gold >= cost:
        return True
        
    return False


class RestingInTownHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        cleanup = get_perception_cleanup_update(actor, snapshot)
        final_updates = [cleanup] if cleanup else []

        if actor.combat.hp < actor.combat.max_hp:
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Resting in town (healing)",
                updates=final_updates)

        want_buy = hero_wants_to_buy(actor)
        if want_buy:
            store = find_building(snapshot, "store")
            if store:
                return AIState.VISIT_SHOP, propose_move_toward(
                    actor, store.spatial.pos, snapshot, f"Heading to store to buy {want_buy}")

        if hero_should_visit_blacksmith(actor):
            bs = find_building(snapshot, "blacksmith")
            if bs:
                return AIState.VISIT_BLACKSMITH, propose_move_toward(
                    actor, bs.spatial.pos, snapshot, "Heading to blacksmith")

        if hero_should_visit_guild(actor):
            guild = find_building(snapshot, "guild")
            if guild:
                return AIState.VISIT_GUILD, propose_move_toward(
                    actor, guild.spatial.pos, snapshot, "Heading to guild for intel")

        if hero_should_visit_class_hall(actor):
            ch = find_building(snapshot, "class_hall")
            if ch:
                return AIState.VISIT_CLASS_HALL, propose_move_toward(
                    actor, ch.spatial.pos, snapshot, "Heading to class hall")

        if hero_should_visit_home(actor):
            if actor.spatial.home_pos:
                return AIState.VISIT_HOME, propose_move_toward(
                    actor, actor.spatial.home_pos, snapshot, "Heading home to manage storage")

        if hero_should_visit_inn(actor):
            inn = find_building(snapshot, "inn")
            if inn:
                return AIState.VISIT_INN, propose_move_toward(
                    actor, inn.spatial.pos, snapshot, "Heading to inn to recover stamina")

        return AIState.WANDER, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Fully healed → leaving town to explore")


class VisitShopHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        store = find_building(snapshot, "store")
        if store is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No store found")

        if actor.spatial.pos.manhattan(store.spatial.pos) > 0:
            return AIState.VISIT_SHOP, propose_move_toward(
                actor, store.spatial.pos, snapshot, "Walking to store")

        inv = actor.inventory
        if inv is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No inventory")

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
                if actor.identity.craft_target:
                    recipe = RECIPE_MAP.get(actor.identity.craft_target)
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
        gold_removals = 0
        removals = []
        for iid in items_to_sell:
            price = item_sell_price(iid, actor.identity.reputation)
            total_gold += price
            removals.append(iid)
            sold_any = True

        if sold_any:
            return AIState.VISIT_SHOP, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Selling {len(removals)} items for {total_gold}g",
                updates=[ProgressionUpdate(inventory_remove=removals, gold_delta=total_gold)])

        want = hero_wants_to_buy(actor)
        if want:
            price = shop_buy_price(want, actor.identity.reputation)
            if price and actor.progression.gold >= price and inv.can_add(want):
                return AIState.VISIT_SHOP, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Buying {want} for {price}g",
                    updates=[ProgressionUpdate(gold_delta=-price, inventory_add=[want])])

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Done shopping → checking other activities")


class VisitBlacksmithHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        bs = find_building(snapshot, "blacksmith")
        if bs is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No blacksmith found")

        if actor.spatial.pos.manhattan(bs.spatial.pos) > 0:
            return AIState.VISIT_BLACKSMITH, propose_move_toward(
                actor, bs.spatial.pos, snapshot, "Walking to blacksmith")

        inv = actor.inventory
        if inv is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No inventory")

        if not actor.identity.known_recipes:
            return AIState.VISIT_BLACKSMITH, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Learning recipes from blacksmith",
                updates=[IdentityUpdate(recipes_learn=[r.recipe_id for r in RECIPES])])

        if actor.identity.craft_target:
            recipe = RECIPE_MAP.get(actor.identity.craft_target)
            if recipe and can_craft(recipe, actor.progression.gold, inv.items):
                mats = []
                for mid, qty in recipe.materials.items():
                    for _ in range(qty): mats.append(mid)
                
                return AIState.VISIT_BLACKSMITH, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Crafting {recipe.output_item}",
                    updates=[
                        ProgressionUpdate(inventory_remove=mats, gold_delta=-recipe.gold_cost, inventory_add=[recipe.output_item]),
                        IdentityUpdate(craft_target=None)
                    ])

        if actor.identity.craft_target:
            recipe = RECIPE_MAP.get(actor.identity.craft_target)
            if recipe:
                missing = []
                for mat_id, qty in recipe.materials.items():
                    have = inv.items.count(mat_id)
                    if have < qty:
                        missing.append(f"{mat_id} ({have}/{qty})")
                gold_needed = max(0, recipe.gold_cost - actor.progression.gold)
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
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        guild = find_building(snapshot, "guild")
        if guild is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No guild found")

        if actor.spatial.pos.manhattan(guild.spatial.pos) > 0:
            return AIState.VISIT_GUILD, propose_move_toward(
                actor, guild.spatial.pos, snapshot, "Walking to guild hall")

        revealed = {}
        for cx, cy in snapshot.camps:
            camp_key = (cx, cy)
            if camp_key not in actor.mind.perception.terrain_memory:
                revealed[camp_key] = 4
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    k = (cx + dx, cy + dy)
                    if k not in actor.mind.perception.terrain_memory:
                        revealed[k] = 0

        for node in snapshot.resource_nodes:
            nk = (node.spatial.pos.x, node.spatial.pos.y)
            if nk not in actor.mind.perception.terrain_memory:
                revealed[nk] = node.terrain.value if hasattr(node.terrain, 'value') else int(node.terrain)

        if revealed:
            return AIState.VISIT_GUILD, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Guild revealed {len(revealed)} locations!",
                updates=[PerceptionUpdate(terrain_memory=revealed)])

        from src.core.gameplay.quests import generate_quest, MAX_ACTIVE_QUESTS
        active_quests = [q for q in actor.progression.quests if not q.completed]
        if len(active_quests) < MAX_ACTIVE_QUESTS:
            existing_ids = {q.quest_id for q in actor.progression.quests}
            new_quest = generate_quest(
                hero_level=actor.progression.level,
                existing_quest_ids=existing_ids,
                rng=ctx.rng,
                entity_id=actor.id,
                tick=snapshot.tick,
                grid_width=snapshot.grid.width if hasattr(snapshot, 'grid') else 100,
                grid_height=snapshot.grid.height if hasattr(snapshot, 'grid') else 100,
                world=snapshot,
            )
            if new_quest:
                return AIState.VISIT_GUILD, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Accepted quest: {new_quest.title}",
                    updates=[ProgressionUpdate(quest_add=[new_quest])])

        from src.core.gameplay.buildings import MATERIAL_HINTS
        new_goals = []
        if actor.identity.craft_target:
            recipe = RECIPE_MAP.get(actor.identity.craft_target)
            if recipe:
                for mat_id in recipe.materials:
                    hint = MATERIAL_HINTS.get(mat_id)
                    if hint and hint not in actor.mind.decision.goals:
                        new_goals.append(f"Guild tip: {mat_id} — {hint}")

        terrain_tips = [
            "Forests (green) host wolves — wolf pelts and fangs drop there.",
            "Deserts (tan) host bandits — fiber and raw gems found there.",
            "Swamps (purple) host undead — bone shards and ectoplasm drop there.",
            "Mountains (grey) host orcs — stone blocks and iron ore found there.",
        ]
        for tip in terrain_tips:
            goal_text = f"Guild tip: {tip}"
            if goal_text not in actor.mind.decision.goals:
                new_goals.append(goal_text)

        if new_goals or revealed:
            final_updates = []
            if revealed: final_updates.append(PerceptionUpdate(terrain_memory=revealed))
            if new_goals: final_updates.append(MindUpdate(goals_add=new_goals))
            
            return AIState.VISIT_GUILD, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Got intel from guild hall",
                updates=final_updates)

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Got intel from guild → planning next move")


class VisitClassHallHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        ch = find_building(snapshot, "class_hall")
        if ch is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No class hall found")

        if actor.spatial.pos.manhattan(ch.spatial.pos) > 0:
            return AIState.VISIT_CLASS_HALL, propose_move_toward(
                actor, ch.spatial.pos, snapshot, "Walking to class hall")

        from src.core.gameplay.classes import (
            HeroClass, available_class_skills, can_breakthrough, can_learn_skill,
            SKILL_DEFS, BREAKTHROUGHS, CLASS_DEFS, SkillInstance,
        )
        try:
            hero_class = HeroClass(actor.progression.hero_class)
        except (ValueError, KeyError, TypeError, AttributeError):
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No class → switching")

        from src.systems.lifecycle.progression_system import available_class_skills, can_learn_skill
        from src.core.gameplay.classes import SkillInstance
        
        known_ids = {s.skill_id for s in actor.progression.skills}
        available = available_class_skills(hero_class, actor.progression.level)
        for sid in available:
            if sid not in known_ids:
                sdef = SKILL_DEFS.get(sid)
                can_learn, _ = can_learn_skill(
                    sdef, actor.progression.level, actor.progression.skills, actor.progression.class_mastery)
                if not can_learn:
                    continue
                        
                return AIState.VISIT_CLASS_HALL, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST, 
                    reason=f"Learning skill: {sdef.name}",
                    updates=[ProgressionUpdate(gold_delta=-sdef.gold_cost, skills_add=[sid])])

        if actor.progression.attributes and can_breakthrough(hero_class, actor.progression.level, actor.progression.attributes):
            bt = BREAKTHROUGHS.get(hero_class)
            if bt:
                return AIState.VISIT_CLASS_HALL, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"CLASS BREAKTHROUGH! → {bt.to_class.name}",
                    updates=[
                        IdentityUpdate(hero_class=int(bt.to_class)),
                        ProgressionUpdate(attribute_cap_delta={"str_cap": 5, "agi_cap": 5, "vit_cap": 5, "int_cap": 5, "spi_cap": 5, "wis_cap": 5, "end_cap": 5, "per_cap": 5, "cha_cap": 5})
                    ])

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Done at class hall → checking other activities")


class VisitInnHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        inn = find_building(snapshot, "inn")
        if inn is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No inn found")

        if actor.spatial.pos.manhattan(inn.spatial.pos) > 0:
            return AIState.VISIT_INN, propose_move_toward(
                actor, inn.spatial.pos, snapshot, "Walking to inn")

        hp_needed = actor.combat.max_hp - actor.combat.hp
        sta_needed = actor.progression.max_stamina - actor.progression.stamina
        
        if hp_needed > 0 or sta_needed > 0 or actor.mind.routine.sleep_debt > 0.1:
            return AIState.SLEEPING, ActionProposal(
                actor_id=actor.id, verb=ActionType.SLEEP,
                reason="Checking into inn to sleep",
                updates=[RoutineUpdate(is_sleeping=True)])

        from src.core.gameplay.effects import well_rested_effect
        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Fully recovered at inn + Well-Rested! → checking other activities",
            updates=[ProgressionUpdate(effects_add=[well_rested_effect()])])


class VisitHomeHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        
        # Resolve home position: 1. spatial.home_pos, 2. PlaceAttachment(HOME)
        target_pos = actor.spatial.home_pos
        if not target_pos:
            from src.core.models.enums import AttachmentKind
            attachment = next((a for a in actor.mind.place_attachments if a.kind == AttachmentKind.HOME), None)
            if attachment:
                target_pos = attachment.location_pos
        
        if not target_pos:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No home or HOME attachment set")

        if actor.spatial.pos.manhattan(target_pos) > 0:
            return AIState.VISIT_HOME, propose_move_toward(
                actor, target_pos, snapshot, "Walking home")

        inv = actor.inventory
        storage = actor.inventory.home_storage if inv else None
        if inv is None or storage is None:
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No inventory/storage")

        cost = storage.upgrade_cost()
        if cost is not None and actor.progression.gold >= cost:
            return AIState.VISIT_HOME, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Upgrading home storage",
                updates=[
                    ProgressionUpdate(gold_delta=-cost),
                    InteractionUpdate(home_storage_upgrade=True)
                ])

        stored = []
        for iid in list(inv.items):
            if storage.is_full:
                break
            t = ITEM_REGISTRY.get(iid)
            if t is None:
                continue
            should_store = False
            if t.item_type == ItemType.MATERIAL:
                if actor.identity.craft_target:
                    recipe = RECIPE_MAP.get(actor.identity.craft_target)
                    if recipe and iid in recipe.materials:
                        needed = recipe.materials[iid]
                        have = inv.items.count(iid) - len([x for x in stored if x == iid])
                        if have <= needed:
                            continue
                should_store = True
            elif t.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
                equipped = _get_equipped_for_type(actor, t.item_type)
                if equipped:
                    eq_t = ITEM_REGISTRY.get(equipped)
                    if eq_t and _item_power(t) < _item_power(eq_t):
                        should_store = True
            elif t.item_type == ItemType.CONSUMABLE and t.heal_amount > 0:
                count_in_inv = inv.items.count(iid) - len([x for x in stored if x == iid])
                if count_in_inv > 2:
                    should_store = True

            if should_store:
                stored.append(iid)

        if stored:
            return AIState.VISIT_HOME, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Storing {len(stored)} items at home",
                updates=[
                    ProgressionUpdate(inventory_remove=stored),
                    InteractionUpdate(home_storage_add=stored)
                ])

        if actor.mind.routine.hunger_level > 0.5:
             return AIState.EATING, ActionProposal(
                actor_id=actor.id, verb=ActionType.EAT,
                reason="Eating at home",
                updates=[RoutineUpdate(hunger_delta=-0.2)])

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Done at home → checking other activities")
