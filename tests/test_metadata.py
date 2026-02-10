"""Tests for the metadata API and shared pydantic dataclass models.

Verifies that:
1. Core pydantic dataclasses still work for game logic (IntEnum comparisons)
2. Core models serialize correctly via TypeAdapter (enums → strings)
3. All metadata endpoints return expected data shapes
"""

import pytest
from pydantic import TypeAdapter

from src.core.enums import DamageType, Element, ItemType, Rarity
from src.core.items import ITEM_REGISTRY, ItemTemplate
from src.core.classes import (
    CLASS_DEFS, SKILL_DEFS, BREAKTHROUGHS, RACE_SKILLS,
    HeroClass, SkillType, SkillTarget,
    SkillDef, ClassDef, BreakthroughDef,
)
from src.core.traits import TRAIT_DEFS, TraitDef


# ---------------------------------------------------------------------------
# Core model — game logic still works with pydantic dataclasses
# ---------------------------------------------------------------------------

class TestCoreGameLogic:
    """Ensure pydantic dataclass conversion didn't break IntEnum game logic."""

    def test_item_enum_comparison(self):
        t = ITEM_REGISTRY["iron_sword"]
        assert t.item_type == ItemType.WEAPON
        assert t.rarity == Rarity.COMMON
        assert t.damage_type == DamageType.PHYSICAL
        assert t.element == Element.NONE

    def test_skill_enum_comparison(self):
        sd = SKILL_DEFS["power_strike"]
        assert sd.skill_type == SkillType.ACTIVE
        assert sd.target == SkillTarget.SINGLE_ENEMY
        assert sd.class_req == HeroClass.WARRIOR

    def test_class_enum_comparison(self):
        cd = CLASS_DEFS[HeroClass.WARRIOR]
        assert cd.class_id == HeroClass.WARRIOR
        assert cd.breakthrough_class == HeroClass.CHAMPION

    def test_breakthrough_enum_comparison(self):
        bt = BREAKTHROUGHS[HeroClass.WARRIOR]
        assert bt.from_class == HeroClass.WARRIOR
        assert bt.to_class == HeroClass.CHAMPION

    def test_item_frozen(self):
        t = ITEM_REGISTRY["iron_sword"]
        with pytest.raises(Exception):
            t.name = "Hacked Sword"  # type: ignore

    def test_skill_frozen(self):
        sd = SKILL_DEFS["power_strike"]
        with pytest.raises(Exception):
            sd.name = "Hacked"  # type: ignore


# ---------------------------------------------------------------------------
# Core model — pydantic serialization (enum → string)
# ---------------------------------------------------------------------------

class TestCoreSerialization:
    """Ensure pydantic dataclasses serialize enums as lowercase strings."""

    _item_ta = TypeAdapter(ItemTemplate)
    _skill_ta = TypeAdapter(SkillDef)
    _class_ta = TypeAdapter(ClassDef)
    _bt_ta = TypeAdapter(BreakthroughDef)
    _trait_ta = TypeAdapter(TraitDef)

    def test_item_serialization(self):
        d = self._item_ta.dump_python(ITEM_REGISTRY["iron_sword"], mode="json")
        assert d["item_type"] == "weapon"
        assert d["rarity"] == "common"
        assert d["damage_type"] == "physical"
        assert d["element"] == "none"
        assert d["name"] == "Iron Sword"
        assert d["atk_bonus"] == 4

    def test_enchanted_blade_serialization(self):
        d = self._item_ta.dump_python(ITEM_REGISTRY["enchanted_blade"], mode="json")
        assert d["rarity"] == "rare"
        assert d["crit_rate_bonus"] == 0.05

    def test_skill_serialization(self):
        d = self._skill_ta.dump_python(SKILL_DEFS["power_strike"], mode="json")
        assert d["skill_type"] == "active"
        assert d["target"] == "single_enemy"
        assert d["class_req"] == "warrior"
        assert d["power"] == 1.8

    def test_passive_skill_serialization(self):
        d = self._skill_ta.dump_python(SKILL_DEFS["pack_hunt"], mode="json")
        assert d["skill_type"] == "passive"
        assert d["target"] == "self"
        assert d["class_req"] == "none"

    def test_class_serialization(self):
        d = self._class_ta.dump_python(CLASS_DEFS[HeroClass.WARRIOR], mode="json")
        assert d["class_id"] == "warrior"
        assert d["breakthrough_class"] == "champion"
        assert d["str_scaling"] == "S"

    def test_breakthrough_serialization(self):
        d = self._bt_ta.dump_python(BREAKTHROUGHS[HeroClass.WARRIOR], mode="json")
        assert d["from_class"] == "warrior"
        assert d["to_class"] == "champion"
        assert d["talent"] == "Unyielding"

    def test_trait_serialization(self):
        td = list(TRAIT_DEFS.values())[0]
        d = self._trait_ta.dump_python(td, mode="json")
        assert "trait_type" in d
        assert "name" in d
        assert "description" in d


# ---------------------------------------------------------------------------
# Metadata endpoints — return correct data
# ---------------------------------------------------------------------------

class TestMetadataEndpoints:
    """Test all metadata endpoint functions directly."""

    def test_get_enums(self):
        from src.api.routes.metadata import get_enums
        e = get_enums()
        assert len(e.materials) > 0
        assert len(e.ai_states) > 0
        assert len(e.factions) > 0
        assert len(e.entity_kinds) > 0

    def test_get_items(self):
        from src.api.routes.metadata import get_items
        result = get_items()
        items = result["items"]
        assert len(items) == len(ITEM_REGISTRY)
        # Check first item has expected keys
        first = items[0]
        assert "item_id" in first
        assert "item_type" in first
        assert isinstance(first["item_type"], str)  # enum serialized as string

    def test_get_classes(self):
        from src.api.routes.metadata import get_classes
        c = get_classes()
        assert len(c.classes) == len(CLASS_DEFS)
        assert len(c.skills) == len(SKILL_DEFS)
        # Check class view structure
        warrior = next(cv for cv in c.classes if cv.id == "warrior")
        assert warrior.name == "Warrior"
        assert warrior.attr_bonuses is not None
        assert warrior.scaling is not None
        assert warrior.breakthrough is not None
        assert warrior.breakthrough.to_class == "champion"

    def test_get_traits(self):
        from src.api.routes.metadata import get_traits
        result = get_traits()
        traits = result["traits"]
        assert len(traits) == len(TRAIT_DEFS)
        assert "trait_type" in traits[0]
        assert "name" in traits[0]

    def test_get_attributes(self):
        from src.api.routes.metadata import get_attributes
        a = get_attributes()
        assert len(a.attributes) == 9
        keys = [attr.key for attr in a.attributes]
        assert "str" in keys
        assert "cha" in keys

    def test_get_buildings(self):
        from src.api.routes.metadata import get_buildings
        b = get_buildings()
        assert len(b.building_types) >= 5
        types = [bt.building_type for bt in b.building_types]
        assert "store" in types
        assert "blacksmith" in types

    def test_get_resources(self):
        from src.api.routes.metadata import get_resources
        r = get_resources()
        assert len(r.resource_types) > 0

    def test_get_recipes(self):
        from src.api.routes.metadata import get_recipes
        r = get_recipes()
        assert len(r.recipes) > 0
        first = r.recipes[0]
        assert first.output_item != ""
        assert first.gold_cost > 0


# ---------------------------------------------------------------------------
# Registry completeness
# ---------------------------------------------------------------------------

class TestRegistryCompleteness:
    """Ensure registries are populated."""

    def test_item_registry_not_empty(self):
        assert len(ITEM_REGISTRY) > 50

    def test_skill_defs_not_empty(self):
        assert len(SKILL_DEFS) > 10

    def test_class_defs_has_base_classes(self):
        for hc in [HeroClass.WARRIOR, HeroClass.RANGER, HeroClass.MAGE, HeroClass.ROGUE]:
            assert hc in CLASS_DEFS

    def test_breakthroughs_exist(self):
        assert len(BREAKTHROUGHS) == 4

    def test_trait_defs_not_empty(self):
        assert len(TRAIT_DEFS) > 10

    def test_race_skills_has_hero(self):
        assert "hero" in RACE_SKILLS
        assert len(RACE_SKILLS["hero"]) > 0
