"""Tests for equipment_enhance features:
- Derived stats (recalc_derived_stats)
- Item pickup / auto_equip_best
- Home storage
- Expanded shop
- Skill learning requirements
- Treasure chests
"""

import pytest

from src.core.attributes import (
    Attributes, AttributeCaps, recalc_derived_stats,
    derive_atk, derive_max_hp, derive_vision,
    train_attributes,
)
from src.core.classes import (
    HeroClass, SkillDef, SkillInstance, SkillType, SkillTarget,
    SKILL_DEFS, can_learn_skill, available_class_skills,
)
from src.core.enums import ItemType, Rarity
from src.core.items import (
    ITEM_REGISTRY, HomeStorage, Inventory, TreasureChest,
    HOUSE_UPGRADE_COSTS, CHEST_LOOT_TABLES,
    item_power, _item_power,
)
from src.core.models import Entity, Stats, Vector2


# =====================================================================
# T1: Derived Stats — recalc_derived_stats
# =====================================================================

class TestRecalcDerivedStats:
    def _make_stats(self, **kw) -> Stats:
        return Stats(**kw)

    def _make_attrs(self, **kw) -> Attributes:
        defaults = dict(str_=5, agi=5, vit=5, int_=5, spi=5, wis=5, end=5, per=5, cha=5)
        defaults.update(kw)
        return Attributes(**defaults)

    def test_creation_mode_adds_bonuses(self):
        stats = self._make_stats(max_hp=50, hp=50, atk=10, def_=3, spd=10)
        attrs = self._make_attrs(str_=10, vit=8, agi=6)
        recalc_derived_stats(stats, attrs)
        # ATK should be base + derive_atk(0, str_)
        assert stats.atk == 10 + derive_atk(0, 10)
        assert stats.max_hp > 50  # VIT and END contribute
        assert stats.vision_range >= 6  # PER contributes

    def test_creation_mode_noncombat(self):
        stats = self._make_stats()
        attrs = self._make_attrs(per=10, wis=8, cha=7, end=6)
        recalc_derived_stats(stats, attrs)
        assert stats.vision_range == derive_vision(6, 10)
        assert stats.hp_regen > 1.0
        assert stats.trade_bonus > 1.0
        assert stats.loot_bonus > 1.0

    def test_delta_mode_strips_old_adds_new(self):
        stats = self._make_stats(max_hp=50, hp=50, atk=10)
        old_attrs = self._make_attrs(str_=5)
        new_attrs = self._make_attrs(str_=10)
        # First apply old
        recalc_derived_stats(stats, old_attrs)
        atk_after_old = stats.atk
        # Now delta: strip old, apply new
        recalc_derived_stats(stats, new_attrs, old_attrs=old_attrs)
        # ATK should increase by the diff in attribute contribution
        expected_delta = derive_atk(0, 10) - derive_atk(0, 5)
        assert stats.atk == atk_after_old + expected_delta

    def test_hp_clamped_after_recalc(self):
        stats = self._make_stats(max_hp=100, hp=100)
        attrs = self._make_attrs(vit=1, end=1)
        recalc_derived_stats(stats, attrs)
        assert stats.hp <= stats.max_hp

    def test_default_attrs_add_bonuses(self):
        stats = self._make_stats(max_hp=20, hp=20, atk=5)
        attrs = Attributes()  # defaults are 5 each
        recalc_derived_stats(stats, attrs)
        # Stats should have base + attribute contribution from str_=5
        assert stats.atk == 5 + derive_atk(0, 5)
        assert stats.vision_range == derive_vision(6, 5)


# =====================================================================
# T2: Item Pickup — auto_equip_best
# =====================================================================

class TestAutoEquipBest:
    def test_equip_empty_slot(self):
        inv = Inventory(items=["iron_sword"], max_slots=10, max_weight=50.0)
        result = inv.auto_equip_best("iron_sword")
        assert result is True
        assert inv.weapon == "iron_sword"
        assert "iron_sword" not in inv.items

    def test_equip_better_item(self):
        inv = Inventory(
            items=["steel_greatsword"], max_slots=10, max_weight=50.0,
            weapon="wooden_club",
        )
        result = inv.auto_equip_best("steel_greatsword")
        assert result is True
        assert inv.weapon == "steel_greatsword"
        assert "wooden_club" in inv.items

    def test_skip_worse_item(self):
        inv = Inventory(
            items=["wooden_club"], max_slots=10, max_weight=50.0,
            weapon="iron_sword",
        )
        result = inv.auto_equip_best("wooden_club")
        assert result is False
        assert inv.weapon == "iron_sword"
        assert "wooden_club" in inv.items

    def test_non_equipment_ignored(self):
        inv = Inventory(items=["small_hp_potion"], max_slots=10, max_weight=50.0)
        result = inv.auto_equip_best("small_hp_potion")
        assert result is False

    def test_item_not_in_inventory(self):
        inv = Inventory(items=[], max_slots=10, max_weight=50.0)
        result = inv.auto_equip_best("iron_sword")
        assert result is False


class TestItemPower:
    def test_known_item_power(self):
        t = ITEM_REGISTRY["iron_sword"]
        assert _item_power(t) > 0

    def test_public_wrapper(self):
        assert item_power("iron_sword") > 0
        assert item_power("nonexistent") == 0

    def test_stronger_item_higher_power(self):
        assert item_power("steel_greatsword") > item_power("iron_sword")
        assert item_power("iron_sword") > item_power("wooden_club")


# =====================================================================
# T3: Home Storage
# =====================================================================

class TestHomeStorage:
    def test_add_item(self):
        hs = HomeStorage(max_slots=5)
        assert hs.add_item("iron_ore")
        assert hs.used_slots == 1

    def test_full_storage(self):
        hs = HomeStorage(max_slots=2)
        hs.add_item("iron_ore")
        hs.add_item("wood")
        assert hs.is_full
        assert not hs.add_item("leather")

    def test_remove_item(self):
        hs = HomeStorage(items=["iron_ore", "wood"])
        assert hs.remove_item("iron_ore")
        assert hs.used_slots == 1
        assert not hs.remove_item("nonexistent")

    def test_upgrade(self):
        hs = HomeStorage(max_slots=30, level=0)
        assert hs.upgrade_cost() == 200
        assert hs.upgrade()
        assert hs.level == 1
        assert hs.max_slots == 50
        assert hs.upgrade_cost() == 500
        assert hs.upgrade()
        assert hs.level == 2
        assert hs.max_slots == 80
        # No more upgrades
        assert hs.upgrade_cost() is None
        assert not hs.upgrade()

    def test_copy(self):
        hs = HomeStorage(items=["iron_ore"], max_slots=50, level=1)
        hs2 = hs.copy()
        assert hs2.items == ["iron_ore"]
        assert hs2.max_slots == 50
        assert hs2.level == 1
        hs2.add_item("wood")
        assert hs.used_slots == 1  # original unchanged


# =====================================================================
# T4: Expanded Shop
# =====================================================================

class TestExpandedShop:
    def test_new_items_in_registry(self):
        for iid in ["atk_potion", "def_potion", "spd_potion", "crit_potion",
                     "antidote", "mana_shard", "silver_ingot", "phoenix_feather",
                     "steel_greatsword", "plate_armor", "apprentice_staff", "fire_staff"]:
            assert iid in ITEM_REGISTRY, f"{iid} missing from ITEM_REGISTRY"

    def test_new_items_in_shop(self):
        from src.core.buildings import shop_buy_price
        for iid in ["atk_potion", "def_potion", "spd_potion", "crit_potion",
                     "steel_greatsword", "plate_armor", "mana_shard"]:
            assert shop_buy_price(iid) is not None, f"{iid} not in shop"

    def test_buff_potion_types(self):
        for iid in ["atk_potion", "def_potion", "spd_potion", "crit_potion"]:
            t = ITEM_REGISTRY[iid]
            assert t.item_type == ItemType.CONSUMABLE


# =====================================================================
# T5: Skill Learning Requirements
# =====================================================================

class TestSkillLearningRequirements:
    def test_tier1_skill_no_prereq(self):
        sdef = SKILL_DEFS["power_strike"]
        can, reason = can_learn_skill(sdef, level=1, known_skills=[])
        assert can is True

    def test_tier2_skill_needs_mastery(self):
        sdef = SKILL_DEFS["shield_wall"]
        # No prerequisite skill known
        can, reason = can_learn_skill(sdef, level=3, known_skills=[])
        assert can is False
        assert "Power Strike" in reason

    def test_tier2_skill_low_mastery(self):
        sdef = SKILL_DEFS["shield_wall"]
        prereq = SkillInstance(skill_id="power_strike", mastery=10.0)
        can, reason = can_learn_skill(sdef, level=3, known_skills=[prereq])
        assert can is False
        assert "mastery" in reason.lower()

    def test_tier2_skill_sufficient_mastery(self):
        sdef = SKILL_DEFS["shield_wall"]
        prereq = SkillInstance(skill_id="power_strike", mastery=25.0)
        can, reason = can_learn_skill(sdef, level=3, known_skills=[prereq])
        assert can is True

    def test_level_too_low(self):
        sdef = SKILL_DEFS["shield_wall"]
        prereq = SkillInstance(skill_id="power_strike", mastery=50.0)
        can, reason = can_learn_skill(sdef, level=1, known_skills=[prereq])
        assert can is False
        assert "level" in reason.lower()

    def test_tier3_chain(self):
        sdef = SKILL_DEFS["battle_cry"]
        # Need shield_wall mastery >= 25
        s1 = SkillInstance(skill_id="power_strike", mastery=50.0)
        s2 = SkillInstance(skill_id="shield_wall", mastery=30.0)
        can, reason = can_learn_skill(sdef, level=5, known_skills=[s1, s2])
        assert can is True

    def test_all_classes_have_chains(self):
        """Verify all 4 base classes have proper skill chains."""
        for hc in [HeroClass.WARRIOR, HeroClass.RANGER, HeroClass.MAGE, HeroClass.ROGUE]:
            skills = available_class_skills(hc, level=10)
            assert len(skills) == 3, f"{hc.name} should have 3 skills at level 10"
            # The 2nd and 3rd skills should have mastery_req
            for sid in skills[1:]:
                sdef = SKILL_DEFS[sid]
                assert sdef.mastery_req != "", f"{sid} should have mastery_req"


# =====================================================================
# T7: Treasure Chests
# =====================================================================

class TestTreasureChest:
    def test_initial_state(self):
        chest = TreasureChest(chest_id=1, pos=Vector2(10, 20), tier=2)
        assert chest.is_available
        assert not chest.looted

    def test_loot_and_respawn(self):
        chest = TreasureChest(chest_id=1, pos=Vector2(10, 20), tier=1)
        chest.loot(current_tick=100, respawn_ticks=50)
        assert chest.looted
        assert not chest.is_available
        assert chest.respawn_at == 150
        # Not yet time to respawn
        assert not chest.try_respawn(120)
        assert chest.looted
        # Time to respawn
        assert chest.try_respawn(150)
        assert not chest.looted
        assert chest.is_available

    def test_copy(self):
        chest = TreasureChest(chest_id=1, pos=Vector2(5, 5), tier=3, looted=True)
        c2 = chest.copy()
        assert c2.chest_id == 1
        assert c2.tier == 3
        assert c2.looted
        c2.looted = False
        assert chest.looted  # original unchanged

    def test_loot_tables_exist(self):
        for tier in [1, 2, 3]:
            assert tier in CHEST_LOOT_TABLES
            assert len(CHEST_LOOT_TABLES[tier]) > 0

    def test_loot_table_items_exist_in_registry(self):
        for tier, table in CHEST_LOOT_TABLES.items():
            for item_id, chance, min_c, max_c in table:
                assert item_id in ITEM_REGISTRY, f"Chest tier {tier}: {item_id} not in registry"
                assert 0.0 < chance <= 1.0
                assert min_c >= 1
                assert max_c >= min_c


# =====================================================================
# T1 + T3: Entity integration — derived stats + home storage on Entity
# =====================================================================

class TestEntityIntegration:
    def test_entity_copy_includes_home_storage(self):
        hs = HomeStorage(items=["wood"], max_slots=30, level=0)
        e = Entity(id=1, kind="hero", pos=Vector2(0, 0), home_storage=hs)
        e2 = e.copy()
        assert e2.home_storage is not None
        assert e2.home_storage.items == ["wood"]
        e2.home_storage.add_item("iron_ore")
        assert len(e.home_storage.items) == 1  # original unchanged

    def test_entity_without_home_storage(self):
        e = Entity(id=1, kind="goblin", pos=Vector2(0, 0))
        assert e.home_storage is None
        e2 = e.copy()
        assert e2.home_storage is None


# =====================================================================
# Training with stats update
# =====================================================================

class TestTrainWithStats:
    def test_training_updates_stats_on_increment(self):
        attrs = Attributes(str_=5, agi=5, vit=5, int_=5, spi=5, wis=5, end=5, per=5, cha=5)
        # Set frac close to 1.0 so it triggers
        attrs._str_frac = 0.99
        caps = AttributeCaps()
        stats = Stats(atk=10)
        recalc_derived_stats(stats, attrs)  # initial derivation
        old_atk = stats.atk
        # Train attack — str rate is 0.015, frac was 0.99 → 1.005 → increment
        train_attributes(attrs, caps, "attack", stats=stats)
        assert attrs.str_ == 6  # incremented
        assert stats.atk > old_atk  # derived stats updated


# =====================================================================
# Speed Delay System (Option D)
# =====================================================================

class TestSpeedDelay:
    def test_import(self):
        from src.core.attributes import speed_delay
        assert callable(speed_delay)

    def test_spd_1_base_delay(self):
        from src.core.attributes import speed_delay
        d = speed_delay(1, "move")
        assert abs(d - 1.0) < 0.01  # ln(1)=0, so 1/(1+0) = 1.0

    def test_logarithmic_diminishing_returns(self):
        from src.core.attributes import speed_delay
        d1 = speed_delay(1, "move")
        d5 = speed_delay(5, "move")
        d10 = speed_delay(10, "move")
        d20 = speed_delay(20, "move")
        d50 = speed_delay(50, "move")
        # Must be strictly decreasing
        assert d1 > d5 > d10 > d20 > d50
        # Diminishing returns: gap between 1→10 much larger than 10→50
        assert (d1 - d10) > (d10 - d50)

    def test_action_type_multipliers(self):
        from src.core.attributes import speed_delay
        spd = 10
        move = speed_delay(spd, "move")
        attack = speed_delay(spd, "attack")
        skill = speed_delay(spd, "skill")
        loot = speed_delay(spd, "loot")
        use_item = speed_delay(spd, "use_item")
        # Attack faster than move, skill slower, loot/use_item fastest
        assert attack < move
        assert skill > move
        assert loot < move
        assert use_item < loot

    def test_min_delay_floor(self):
        from src.core.attributes import speed_delay
        d = speed_delay(999999, "use_item")
        assert d >= 0.15  # _MIN_DELAY

    def test_max_delay_ceiling(self):
        from src.core.attributes import speed_delay
        d = speed_delay(1, "skill")
        assert d <= 2.0  # _MAX_DELAY

    def test_interaction_speed_scales_non_combat(self):
        from src.core.attributes import speed_delay
        base = speed_delay(10, "loot", interaction_speed=1.0)
        fast = speed_delay(10, "loot", interaction_speed=1.5)
        assert fast < base  # higher interaction_speed → lower delay

    def test_interaction_speed_ignored_for_combat(self):
        from src.core.attributes import speed_delay
        base = speed_delay(10, "attack", interaction_speed=1.0)
        fast = speed_delay(10, "attack", interaction_speed=2.0)
        assert abs(base - fast) < 0.001  # should be identical


class TestEngagementLock:
    def test_engaged_ticks_on_entity(self):
        e = Entity(id=1, kind="hero", pos=Vector2(0, 0))
        assert e.engaged_ticks == 0
        e.engaged_ticks = 3
        e2 = e.copy()
        assert e2.engaged_ticks == 3

    def test_last_reason_on_entity(self):
        e = Entity(id=1, kind="hero", pos=Vector2(0, 0))
        assert e.last_reason == ""
        e.last_reason = "Heading to store"
        e2 = e.copy()
        assert e2.last_reason == "Heading to store"
