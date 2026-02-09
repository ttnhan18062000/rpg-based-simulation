"""Tests for the EntityBuilder fluent API."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.entity_builder import EntityBuilder
from src.core.enums import AIState, Domain
from src.core.faction import Faction
from src.core.items import Inventory
from src.core.models import Entity, Vector2
from src.core.classes import HeroClass


# ---------------------------------------------------------------------------
# Fake RNG for deterministic testing
# ---------------------------------------------------------------------------

class _FakeRNG:
    """Minimal fake RNG that returns predictable values."""
    def __init__(self, int_val: int = 1, float_val: float = 0.5):
        self._int_val = int_val
        self._float_val = float_val

    def next_int(self, domain, eid, tick, lo, hi):
        return max(lo, min(self._int_val, hi))

    def next_float(self, domain, eid, tick):
        return self._float_val

    def next_bool(self, domain, eid, tick, probability):
        return self._float_val < probability


# ---------------------------------------------------------------------------
# Basic construction tests
# ---------------------------------------------------------------------------

class TestEntityBuilderBasic:
    """Test basic EntityBuilder construction."""

    def test_build_returns_entity(self):
        rng = _FakeRNG()
        entity = EntityBuilder(rng, 1).kind("test").build()
        assert isinstance(entity, Entity)
        assert entity.id == 1
        assert entity.kind == "test"

    def test_default_values(self):
        rng = _FakeRNG()
        entity = EntityBuilder(rng, 42).build()
        assert entity.id == 42
        assert entity.kind == "unknown"
        assert entity.ai_state == AIState.WANDER
        assert entity.faction == Faction.HERO_GUILD
        assert entity.alive

    def test_kind_sets_kind(self):
        rng = _FakeRNG()
        entity = EntityBuilder(rng, 1).kind("goblin").build()
        assert entity.kind == "goblin"

    def test_at_sets_position(self):
        rng = _FakeRNG()
        pos = Vector2(10, 20)
        entity = EntityBuilder(rng, 1).at(pos).build()
        assert entity.pos.x == 10
        assert entity.pos.y == 20

    def test_home_sets_home_pos(self):
        rng = _FakeRNG()
        home = Vector2(5, 5)
        entity = EntityBuilder(rng, 1).home(home).build()
        assert entity.home_pos is not None
        assert entity.home_pos.x == 5

    def test_ai_state_sets_state(self):
        rng = _FakeRNG()
        entity = EntityBuilder(rng, 1).ai_state(AIState.GUARD_CAMP).build()
        assert entity.ai_state == AIState.GUARD_CAMP

    def test_faction_sets_faction(self):
        rng = _FakeRNG()
        entity = EntityBuilder(rng, 1).faction(Faction.GOBLIN_HORDE).build()
        assert entity.faction == Faction.GOBLIN_HORDE

    def test_tier_sets_tier(self):
        rng = _FakeRNG()
        entity = EntityBuilder(rng, 1).tier(3).build()
        assert entity.tier == 3


# ---------------------------------------------------------------------------
# Stats tests
# ---------------------------------------------------------------------------

class TestEntityBuilderStats:
    """Test base stat configuration."""

    def test_with_base_stats(self):
        rng = _FakeRNG()
        entity = (
            EntityBuilder(rng, 1)
            .with_base_stats(hp=100, atk=20, def_=10, spd=15, luck=5,
                             crit_rate=0.1, crit_dmg=2.0, evasion=0.05,
                             level=3, xp_to_next=300, gold=200)
            .build()
        )
        assert entity.stats.hp == 100
        assert entity.stats.max_hp == 100
        assert entity.stats.atk == 20
        assert entity.stats.def_ == 10
        assert entity.stats.spd == 15
        assert entity.stats.luck == 5
        assert abs(entity.stats.crit_rate - 0.1) < 0.001
        assert entity.stats.level == 3
        assert entity.stats.xp_to_next == 300
        assert entity.stats.gold == 200

    def test_with_randomized_stats_adds_variance(self):
        rng = _FakeRNG(int_val=5)  # always returns 5 (within bounds)
        entity = (
            EntityBuilder(rng, 1)
            .with_base_stats(hp=50, atk=10, def_=3, spd=10)
            .with_randomized_stats()
            .build()
        )
        # RNG returns min(5, hi) for each stat randomization
        assert entity.stats.hp > 50  # added some variance
        assert entity.stats.atk > 10

    def test_hero_stamina_minimum_50(self):
        rng = _FakeRNG()
        entity = (
            EntityBuilder(rng, 1)
            .kind("hero")
            .with_base_stats(hp=50, atk=10, def_=3, spd=10)
            .build()
        )
        assert entity.stats.stamina >= 50


# ---------------------------------------------------------------------------
# Hero class + attributes tests
# ---------------------------------------------------------------------------

class TestEntityBuilderHeroClass:
    """Test hero class and attribute configuration."""

    def test_with_hero_class_sets_class(self):
        rng = _FakeRNG()
        entity = (
            EntityBuilder(rng, 1)
            .kind("hero")
            .with_hero_class(HeroClass.WARRIOR)
            .build()
        )
        assert entity.hero_class == int(HeroClass.WARRIOR)
        assert entity.attributes is not None
        assert entity.attribute_caps is not None

    def test_with_hero_class_derives_attributes(self):
        rng = _FakeRNG(int_val=1)
        entity = (
            EntityBuilder(rng, 1)
            .kind("hero")
            .with_hero_class(HeroClass.MAGE)
            .build()
        )
        # Mage should have higher INT bonus
        from src.core.classes import CLASS_DEFS
        mage_def = CLASS_DEFS[HeroClass.MAGE]
        assert entity.attributes is not None
        # Base 5 + class bonus + rng(0,2) where rng returns 1
        expected_int = 5 + mage_def.int_bonus + 1
        assert entity.attributes.int_ == expected_int

    def test_with_mob_attributes(self):
        rng = _FakeRNG(int_val=1)
        entity = (
            EntityBuilder(rng, 1)
            .with_mob_attributes(5, tier=2)
            .build()
        )
        assert entity.attributes is not None
        assert entity.attribute_caps is not None
        # attr_base=5, rng returns 1 for each
        assert entity.attributes.str_ == 5 + 1  # attr_base + rng(0,3)->1
        # Caps scale with tier
        assert entity.attribute_caps.str_cap == 15 + 2 * 5  # 25

    def test_with_race_attributes_applies_modifiers(self):
        rng = _FakeRNG(int_val=1)
        entity = (
            EntityBuilder(rng, 1)
            .with_race_attributes(5, tier=1, r_str=3, r_agi=2)
            .build()
        )
        assert entity.attributes is not None
        # STR: max(1, 5 + 3 + rng(0,3)->1) = 9
        assert entity.attributes.str_ == 9
        # AGI: max(1, 5 + 2 + rng(0,3)->1) = 8
        assert entity.attributes.agi == 8


# ---------------------------------------------------------------------------
# Skills tests
# ---------------------------------------------------------------------------

class TestEntityBuilderSkills:
    """Test skill configuration."""

    def test_with_race_skills(self):
        rng = _FakeRNG()
        entity = EntityBuilder(rng, 1).with_race_skills("hero").build()
        assert len(entity.skills) > 0
        skill_ids = [s.skill_id for s in entity.skills]
        assert "rally" in skill_ids or "second_wind" in skill_ids

    def test_with_class_skills(self):
        rng = _FakeRNG()
        entity = (
            EntityBuilder(rng, 1)
            .with_class_skills(HeroClass.WARRIOR, level=1)
            .build()
        )
        skill_ids = [s.skill_id for s in entity.skills]
        assert "power_strike" in skill_ids

    def test_combined_race_and_class_skills(self):
        rng = _FakeRNG()
        entity = (
            EntityBuilder(rng, 1)
            .with_race_skills("hero")
            .with_class_skills(HeroClass.WARRIOR, level=1)
            .build()
        )
        assert len(entity.skills) >= 2  # at least race + class skills

    def test_no_skills_by_default(self):
        rng = _FakeRNG()
        entity = EntityBuilder(rng, 1).build()
        assert entity.skills == []


# ---------------------------------------------------------------------------
# Inventory tests
# ---------------------------------------------------------------------------

class TestEntityBuilderInventory:
    """Test inventory configuration."""

    def test_with_inventory(self):
        rng = _FakeRNG()
        entity = (
            EntityBuilder(rng, 1)
            .with_inventory(max_slots=20, max_weight=100,
                            weapon="iron_sword", armor="leather_vest")
            .build()
        )
        assert entity.inventory is not None
        assert entity.inventory.max_slots == 20
        assert entity.inventory.weapon == "iron_sword"
        assert entity.inventory.armor == "leather_vest"

    def test_with_starting_items(self):
        rng = _FakeRNG()
        entity = (
            EntityBuilder(rng, 1)
            .with_inventory(max_slots=10, max_weight=50)
            .with_starting_items(["small_hp_potion", "small_hp_potion"])
            .build()
        )
        assert entity.inventory is not None
        assert len(entity.inventory.items) == 2

    def test_with_existing_inventory(self):
        rng = _FakeRNG()
        inv = Inventory(items=[], max_slots=5, max_weight=20.0, weapon="club")
        entity = EntityBuilder(rng, 1).with_existing_inventory(inv).build()
        assert entity.inventory is inv
        assert entity.inventory.weapon == "club"

    def test_with_equipment(self):
        rng = _FakeRNG()
        entity = (
            EntityBuilder(rng, 1)
            .with_inventory(max_slots=10, max_weight=50)
            .with_equipment(weapon="iron_sword", armor="chain_mail")
            .build()
        )
        assert entity.inventory.weapon == "iron_sword"
        assert entity.inventory.armor == "chain_mail"

    def test_no_inventory_by_default(self):
        rng = _FakeRNG()
        entity = EntityBuilder(rng, 1).build()
        assert entity.inventory is None


# ---------------------------------------------------------------------------
# Traits tests
# ---------------------------------------------------------------------------

class TestEntityBuilderTraits:
    """Test trait assignment via builder."""

    def test_with_traits_assigns_traits(self):
        rng = _FakeRNG()
        entity = EntityBuilder(rng, 1).with_traits(race_prefix="hero").build()
        assert len(entity.traits) >= 2
        assert len(entity.traits) <= 4

    def test_no_traits_by_default(self):
        rng = _FakeRNG()
        entity = EntityBuilder(rng, 1).build()
        assert entity.traits == []

    def test_traits_with_different_race_prefix(self):
        rng = _FakeRNG()
        hero_entity = EntityBuilder(rng, 1).with_traits(race_prefix="hero").build()
        goblin_entity = EntityBuilder(rng, 2).with_traits(race_prefix="goblin").build()
        assert len(hero_entity.traits) >= 2
        assert len(goblin_entity.traits) >= 2


# ---------------------------------------------------------------------------
# Fluent chaining tests
# ---------------------------------------------------------------------------

class TestEntityBuilderChaining:
    """Test that fluent chaining works correctly."""

    def test_full_hero_chain(self):
        rng = _FakeRNG()
        entity = (
            EntityBuilder(rng, 1, tick=0)
            .kind("hero")
            .at(Vector2(10, 10))
            .home(Vector2(5, 5))
            .faction(Faction.HERO_GUILD)
            .ai_state(AIState.WANDER)
            .with_base_stats(hp=50, atk=10, def_=3, spd=10, luck=3,
                             crit_rate=0.08, crit_dmg=1.8, evasion=0.03, gold=50)
            .with_hero_class(HeroClass.WARRIOR)
            .with_race_skills("hero")
            .with_class_skills(HeroClass.WARRIOR, level=1)
            .with_inventory(max_slots=20, max_weight=100,
                            weapon="iron_sword", armor="leather_vest")
            .with_starting_items(["small_hp_potion"] * 3)
            .with_traits(race_prefix="hero")
            .build()
        )
        assert entity.kind == "hero"
        assert entity.pos.x == 10
        assert entity.home_pos.x == 5
        assert entity.faction == Faction.HERO_GUILD
        assert entity.stats.hp == 50
        assert entity.hero_class == int(HeroClass.WARRIOR)
        assert entity.attributes is not None
        assert len(entity.skills) >= 2
        assert entity.inventory is not None
        assert entity.inventory.weapon == "iron_sword"
        assert len(entity.inventory.items) == 3
        assert len(entity.traits) >= 2
        assert entity.alive

    def test_full_mob_chain(self):
        rng = _FakeRNG()
        inv = Inventory(items=[], max_slots=6, max_weight=20.0, weapon="club")
        entity = (
            EntityBuilder(rng, 5, tick=100)
            .kind("goblin")
            .at(Vector2(30, 40))
            .home(Vector2(30, 40))
            .faction(Faction.GOBLIN_HORDE)
            .ai_state(AIState.GUARD_CAMP)
            .tier(2)
            .with_base_stats(hp=30, atk=8, def_=4, spd=9, level=3,
                             xp_to_next=225)
            .with_existing_inventory(inv)
            .with_mob_attributes(7, tier=2)
            .with_race_skills("goblin")
            .with_traits(race_prefix="goblin")
            .build()
        )
        assert entity.kind == "goblin"
        assert entity.faction == Faction.GOBLIN_HORDE
        assert entity.tier == 2
        assert entity.stats.level == 3
        assert entity.attributes is not None
        assert entity.inventory is inv
        assert len(entity.traits) >= 2

    def test_each_with_method_returns_self(self):
        """Verify all with_* methods return the builder for chaining."""
        rng = _FakeRNG()
        b = EntityBuilder(rng, 1)
        assert b.kind("x") is b
        assert b.at(Vector2(0, 0)) is b
        assert b.home(None) is b
        assert b.ai_state(AIState.IDLE) is b
        assert b.faction(Faction.HERO_GUILD) is b
        assert b.tier(0) is b
        assert b.with_base_stats() is b
        assert b.with_inventory(max_slots=5, max_weight=10) is b
        assert b.with_starting_items([]) is b
        assert b.with_equipment() is b
        assert b.with_traits() is b
        assert b.with_race_skills("hero") is b
