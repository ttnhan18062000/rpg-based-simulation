"""Tests for equipment_enhance features.

Refactored for AOA Stabilization:
- Updated imports to modern AOA paths.
- Used EntityBuilder for entity construction.
- Updated recalc_derived_stats tests to use Entity objects.
- Unified Inventory tests with InventoryAspect.
"""

from __future__ import annotations
import unittest
from pathlib import Path
import sys

# Ensure the src directory is in the python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.gameplay.attributes import (
    Attributes, AttributeCaps, recalc_derived_stats,
    derive_atk, derive_max_hp, derive_vision,
    train_attributes,
)
from src.core.gameplay.classes import (
    HeroClass, SkillDef, SkillInstance,
    SKILL_DEFS, can_learn_skill, available_class_skills,
)
from src.core.models.enums import ItemType, Rarity
from src.core.gameplay.items.items import (
    ITEM_REGISTRY, HomeStorage, TreasureChest,
    HOUSE_UPGRADE_COSTS, CHEST_LOOT_TABLES,
    item_power, _item_power,
)
from src.core.aspects.inventory import InventoryAspect as Inventory
from src.core.aspects.spatial import SpatialAspect
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.entities.entity_builder import EntityBuilder
from src.platform.rng import DeterministicRNG


class TestRecalcDerivedStats(unittest.TestCase):
    def setUp(self):
        self.rng = DeterministicRNG(42)

    def _make_entity(self, **stats_kw) -> Entity:
        hp = stats_kw.get("hp", 20.0)
        atk = stats_kw.get("atk", 5)
        def_ = stats_kw.get("def_", 0)
        spd = stats_kw.get("spd", 10)
        return (
            EntityBuilder(self.rng, 1)
            .with_base_stats(hp=hp, atk=atk, def_=def_, spd=spd)
            .build()
        )

    def _make_attrs(self, **kw) -> Attributes:
        return Attributes(**kw)

    def test_creation_mode_adds_bonuses(self):
        entity = (
            EntityBuilder(self.rng, 1)
            .with_base_stats(hp=50, atk=10, def_=3, spd=10)
            .build()
        )
        # Note: EntityBuilder already applied default attributes (all 5)
        # so atk_base is 10 + derive_atk(0, 5) = 12.
        # We'll provide old_attrs=Attributes() (the default ones) to reset them.
        default_attrs = Attributes()
        new_attrs = self._make_attrs(str_=10, vit=8, agi=6)
        
        recalc_derived_stats(entity, new_attrs, old_attrs=default_attrs)
        
        # ATK should be 10 + derive_atk(0, 10)
        assert entity.combat.atk_base == 10 + derive_atk(0, 10)
        assert entity.combat.combat.max_hp > 50
        assert entity.spatial.spatial.vision_range >= 6

    def test_hp_clamped_after_recalc(self):
        entity = (
            EntityBuilder(self.rng, 1)
            .with_base_stats(hp=100)
            .build()
        )
        entity.combat.combat.hp = 100
        attrs = self._make_attrs(vit=1, end=1)
        recalc_derived_stats(entity, attrs)
        assert entity.combat.combat.hp <= entity.combat.combat.max_hp


class TestAutoEquipBest(unittest.TestCase):
    def test_equip_empty_slot(self):
        inv = Inventory(items=["iron_sword"], max_slots=10, max_weight=50.0)
        result = inv.auto_equip_best("iron_sword")
        assert result is True
        assert inv.weapon == "iron_sword"
        assert "iron_sword" not in inv.items


class TestEngagementLock(unittest.TestCase):
    def test_engaged_ticks_on_entity(self):
        e = Entity(id=1, kind="hero")
        e.spatial = SpatialAspect(pos=Vector2(0, 0))
        assert e.mind.navigation.engaged_ticks == 0
        e.mind.navigation.engaged_ticks = 3
        e2 = e.copy()
        assert e2.mind.navigation.engaged_ticks == 3

    def test_last_reason_on_entity(self):
        e = Entity(id=1, kind="hero")
        e.spatial = SpatialAspect(pos=Vector2(0, 0))
        assert e.mind.decision.last_reason == ""
        e.mind.decision.last_reason = "Heading to store"


if __name__ == "__main__":
    unittest.main()
