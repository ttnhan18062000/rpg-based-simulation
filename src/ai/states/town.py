from __future__ import annotations

from src.actions.base import ActionType, ActionProposal
from src.core.gameplay.buildings import (
    Building, RECIPES, RECIPE_MAP, SHOP_INVENTORY,
    can_craft, item_sell_price, shop_buy_price,
)
from src.core.models.enums import AIState, EntityRole
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.entities.entity import Entity
from src.core.gameplay.items.items import ItemType, _item_power
from src.ai.states.base import (
    AIContext, StateHandler, clear_dead_from_memory, 
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
            if actor.craft_target:
                recipe = RECIPE_MAP.get(actor.craft_target)
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
    if not actor.inventory:
        return False
    if not actor.known_recipes:
        return True
    if actor.craft_target:
        recipe = RECIPE_MAP.get(actor.craft_target)
        if recipe and can_craft(recipe, actor.progression.gold, actor.inventory.items):
            return True
    return False


def hero_should_visit_guild(actor: Entity) -> bool:
    if not actor.entity_memory:
        return True
    known_prefixes = {"goblin", "wolf", "bandit", "skeleton", "zombie", "lich", "orc"}
    known_kinds = {em.get("kind", "") for em in actor.entity_memory}
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
    if actor.attributes and can_breakthrough(hero_class, actor.progression.level, actor.attributes):
        return True
    return False


def hero_should_visit_inn(actor: Entity) -> bool:
    if actor.progression.max_stamina <= 0:
        return False
    return actor.progression.stamina < actor.progression.max_stamina * 0.4


def hero_should_visit_home(actor: Entity) -> bool:
    if not actor.home_storage or not actor.inventory:
        return False
    if actor.inventory.used_slots >= actor.inventory.max_slots - 2:
        if not actor.home_storage.is_full:
            return True
    cost = actor.home_storage.upgrade_cost()
    if cost is not None and actor.progression.gold >= cost:
        return True
    return False


class RestingInTownHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        clear_dead_from_memory(actor, snapshot)

        if actor.combat.hp < actor.combat.max_hp:
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason="Resting in town (healing)")

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
            if actor.home_pos:
                return AIState.VISIT_HOME, propose_move_toward(
                    actor, actor.home_pos, snapshot, "Heading home to manage storage")

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
                price = item_sell_price(iid, actor.identity.reputation)
                actor.progression.gold += price
                total_gold += price
                sold_any = True

        if sold_any:
            from src.utils.metrics import SIM_SHOP_TRANSACTIONS_TOTAL
            for iid in items_to_sell:
                SIM_SHOP_TRANSACTIONS_TOTAL.labels(type="sell", item_id=iid).inc()
            return AIState.VISIT_SHOP, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Sold items for {total_gold}g (total gold: {actor.progression.gold})")

        want = hero_wants_to_buy(actor)
        if want:
            price = shop_buy_price(want, actor.identity.reputation)
            if price and actor.progression.gold >= price and inv.can_add(want):
                actor.progression.gold -= price
                tax = int(price * 0.1)
                if hasattr(snapshot, 'town_treasury'):
                    snapshot.town_treasury += tax
                inv.add_item(want)
                from src.utils.metrics import SIM_SHOP_TRANSACTIONS_TOTAL
                SIM_SHOP_TRANSACTIONS_TOTAL.labels(type="buy", item_id=want).inc()
                inv.auto_equip_best(want)
                return AIState.VISIT_SHOP, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Bought {want} for {price}g")

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

        if not actor.known_recipes:
            actor.known_recipes = [r.recipe_id for r in RECIPES]
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

        if actor.craft_target:
            recipe = RECIPE_MAP.get(actor.craft_target)
            if recipe and can_craft(recipe, actor.progression.gold, inv.items):
                for mat_id, qty in recipe.materials.items():
                    for _ in range(qty):
                        inv.remove_item(mat_id)
                actor.progression.gold -= recipe.gold_cost
                if inv.can_add(recipe.output_item):
                    inv.add_item(recipe.output_item)
                    t = ITEM_REGISTRY.get(recipe.output_item)
                    if t and t.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
                        inv.equip(recipe.output_item)
                
                from src.utils.metrics import SIM_ITEMS_CRAFTED_TOTAL
                tier = "T1"
                if "t2" in recipe.output_item.lower(): tier = "T2"
                elif "t3" in recipe.output_item.lower(): tier = "T3"
                SIM_ITEMS_CRAFTED_TOTAL.labels(item_id=recipe.output_item, tier=tier).inc()
                
                actor.craft_target = None
                return AIState.VISIT_BLACKSMITH, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Crafted {recipe.output_item}!")

        if actor.craft_target:
            recipe = RECIPE_MAP.get(actor.craft_target)
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

        intel_added = False
        for cx, cy in snapshot.camps:
            camp_key = (cx, cy)
            if camp_key not in actor.terrain_memory:
                actor.terrain_memory[camp_key] = 4
                intel_added = True
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    k = (cx + dx, cy + dy)
                    if k not in actor.terrain_memory:
                        actor.terrain_memory[k] = 0

        regions_revealed = 0
        for node in snapshot.resource_nodes:
            nk = (node.spatial.pos.x, node.spatial.pos.y)
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

        from src.core.gameplay.quests import generate_quest, MAX_ACTIVE_QUESTS
        active_quests = [q for q in actor.quests if not q.completed]
        if len(active_quests) < MAX_ACTIVE_QUESTS:
            existing_ids = {q.quest_id for q in actor.quests}
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
                actor.quests.append(new_quest)
                return AIState.VISIT_GUILD, ActionProposal(
                    actor_id=actor.id, verb=ActionType.REST,
                    reason=f"Accepted quest: {new_quest.title}")

        from src.core.gameplay.buildings import MATERIAL_HINTS
        if actor.craft_target:
            recipe = RECIPE_MAP.get(actor.craft_target)
            if recipe:
                for mat_id in recipe.materials:
                    hint = MATERIAL_HINTS.get(mat_id)
                    if hint and hint not in actor.mind.goals:
                        actor.mind.goals.append(f"Guild tip: {mat_id} — {hint}")

        terrain_tips = [
            "Forests (green) host wolves — wolf pelts and fangs drop there.",
            "Deserts (tan) host bandits — fiber and raw gems found there.",
            "Swamps (purple) host undead — bone shards and ectoplasm drop there.",
            "Mountains (grey) host orcs — stone blocks and iron ore found there.",
        ]
        for tip in terrain_tips:
            if tip not in actor.mind.goals:
                actor.mind.goals.append(f"Guild tip: {tip}")

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
                if sdef and actor.progression.gold >= sdef.gold_cost:
                    can_learn, _ = can_learn_skill(
                        sdef, actor.progression.level, actor.progression.skills, actor.progression.class_mastery)
                    if not can_learn:
                        continue
                    actor.progression.gold -= sdef.gold_cost
                    actor.progression.skills.append(SkillInstance(skill_id=sid))
                    return AIState.VISIT_CLASS_HALL, ActionProposal(
                        actor_id=actor.id, verb=ActionType.REST, 
                        reason=f"Learned skill: {sdef.name} (cost {sdef.gold_cost}g)")

        if actor.attributes and can_breakthrough(hero_class, actor.progression.level, actor.attributes):
            bt = BREAKTHROUGHS.get(hero_class)
            if bt:
                actor.progression.hero_class = int(bt.to_class)
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

        healed = False
        if actor.combat.hp < actor.combat.max_hp:
            actor.combat.hp = min(actor.combat.hp + 10, actor.combat.max_hp)
            healed = True
        if actor.progression.stamina < actor.progression.max_stamina:
            actor.progression.stamina = min(actor.progression.stamina + 10, actor.progression.max_stamina)
            healed = True
        if actor.attributes and actor.attribute_caps:
            from src.core.gameplay.attributes import train_attributes
            train_attributes(actor.attributes, actor.attribute_caps, "rest", stats=actor.stats)

        if healed:
            return AIState.VISIT_INN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Resting at inn (HP: {actor.combat.hp}/{actor.combat.max_hp}, "
                       f"STA: {actor.progression.stamina}/{actor.progression.max_stamina})")

        from src.core.gameplay.effects import EffectType, well_rested_effect
        actor.remove_effects_by_type(EffectType.RESTED)
        actor.effects.append(well_rested_effect())

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Fully recovered at inn + Well-Rested! → checking other activities")


class VisitHomeHandler(StateHandler):
    def handle(self, ctx: AIContext) -> tuple[AIState, ActionProposal]:
        actor, snapshot = ctx.actor, ctx.snapshot
        if not can_use_buildings(actor):
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="Cannot use buildings → wander")
        if actor.home_pos is None:
            return AIState.WANDER, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No home set")

        if actor.spatial.pos.manhattan(actor.home_pos) > 0:
            return AIState.VISIT_HOME, propose_move_toward(
                actor, actor.home_pos, snapshot, "Walking home")

        inv = actor.inventory
        storage = actor.home_storage
        if inv is None or storage is None:
            return AIState.RESTING_IN_TOWN, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST, reason="No inventory/storage")

        cost = storage.upgrade_cost()
        if cost is not None and actor.stats.progression.gold >= cost:
            actor.stats.progression.gold -= cost
            old_max = storage.max_slots
            storage.upgrade()
            return AIState.VISIT_HOME, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Upgraded home storage {old_max}→{storage.max_slots} slots (-{cost}g)")

        stored = []
        for iid in list(inv.items):
            if storage.is_full:
                break
            t = ITEM_REGISTRY.get(iid)
            if t is None:
                continue
            should_store = False
            if t.item_type == ItemType.MATERIAL:
                if actor.craft_target:
                    recipe = RECIPE_MAP.get(actor.craft_target)
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
                if inv.remove_item(iid) and storage.add_item(iid):
                    stored.append(iid)

        if stored:
            return AIState.VISIT_HOME, ActionProposal(
                actor_id=actor.id, verb=ActionType.REST,
                reason=f"Stored {len(stored)} items at home ({storage.used_slots}/{storage.max_slots})")

        return AIState.RESTING_IN_TOWN, ActionProposal(
            actor_id=actor.id, verb=ActionType.REST,
            reason="Done at home → checking other activities")
