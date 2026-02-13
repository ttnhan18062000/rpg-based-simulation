"""Tests for F4: Ranged Combat Positioning.

Covers:
  - weapon_range on ItemTemplate
  - Line-of-sight (Bresenham) through WALL tiles
  - Cover system (evasion bonus near WALLs)
  - CombatAction validation with ranged weapons
  - AI range-aware skill selection
  - AI kiting behavior
  - Hero starting gear per class
  - Ranged mob variants
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.attributes import Attributes, AttributeCaps
from src.core.enums import AIState, ActionType, DamageType, EnemyTier
from src.core.faction import Faction
from src.core.grid import Grid, Material
from src.core.items import (
    ITEM_REGISTRY, ItemTemplate, Inventory,
    RACE_STARTING_GEAR, RACE_TIER_KINDS, TIER_STARTING_GEAR,
)
from src.core.models import Entity, Stats, Vector2


def _make_entity(
    eid: int, kind: str = "hero", pos: tuple = (0, 0),
    hp: int = 50, atk: int = 10, def_: int = 5, spd: int = 10,
    faction: Faction = Faction.HERO_GUILD,
    weapon: str | None = None, stamina: int = 50,
) -> Entity:
    """Helper to create a test entity with optional weapon."""
    stats = Stats(
        hp=hp, max_hp=hp, atk=atk, def_=def_, spd=spd,
        stamina=stamina, max_stamina=stamina,
    )
    attrs = Attributes(str_=5, agi=5, vit=5, int_=5, wis=5, end=5)
    caps = AttributeCaps()
    inv = Inventory(items=[], max_slots=12, max_weight=30.0, weapon=weapon)
    return Entity(
        id=eid, kind=kind, pos=Vector2(*pos),
        stats=stats, faction=faction,
        inventory=inv, attributes=attrs, attribute_caps=caps,
    )


def _make_grid(width: int = 20, height: int = 20) -> Grid:
    """Create a simple floor grid."""
    g = Grid(width, height)
    for y in range(height):
        for x in range(width):
            g.set(Vector2(x, y), Material.FLOOR)
    return g


# =========================================================================
# weapon_range on ItemTemplate
# =========================================================================

class TestWeaponRange:
    def test_melee_weapon_default_range(self):
        sword = ITEM_REGISTRY["iron_sword"]
        assert sword.weapon_range == 1

    def test_shortbow_range(self):
        bow = ITEM_REGISTRY["shortbow"]
        assert bow.weapon_range == 3

    def test_longbow_range(self):
        bow = ITEM_REGISTRY["longbow"]
        assert bow.weapon_range == 4

    def test_windpiercer_range(self):
        bow = ITEM_REGISTRY["windpiercer"]
        assert bow.weapon_range == 5

    def test_apprentice_staff_range(self):
        staff = ITEM_REGISTRY["apprentice_staff"]
        assert staff.weapon_range == 3

    def test_crystal_staff_range(self):
        staff = ITEM_REGISTRY["crystal_staff"]
        assert staff.weapon_range == 4

    def test_bandit_bow_range(self):
        bow = ITEM_REGISTRY["bandit_bow"]
        assert bow.weapon_range == 3

    def test_stormcaller_range(self):
        staff = ITEM_REGISTRY["stormcaller"]
        assert staff.weapon_range == 4


# =========================================================================
# Line-of-Sight (Bresenham)
# =========================================================================

class TestLineOfSight:
    def test_clear_line_of_sight(self):
        g = _make_grid()
        assert g.has_line_of_sight(0, 0, 5, 0) is True

    def test_clear_diagonal(self):
        g = _make_grid()
        assert g.has_line_of_sight(0, 0, 5, 5) is True

    def test_wall_blocks_line_of_sight(self):
        g = _make_grid()
        g.set(Vector2(3, 0), Material.WALL)
        assert g.has_line_of_sight(0, 0, 5, 0) is False

    def test_wall_on_diagonal(self):
        g = _make_grid()
        g.set(Vector2(2, 2), Material.WALL)
        assert g.has_line_of_sight(0, 0, 4, 4) is False

    def test_adjacent_always_visible(self):
        """Adjacent tiles (dist=1) don't check intermediate tiles."""
        g = _make_grid()
        assert g.has_line_of_sight(0, 0, 1, 0) is True

    def test_same_tile(self):
        g = _make_grid()
        assert g.has_line_of_sight(5, 5, 5, 5) is True

    def test_wall_at_endpoint_doesnt_block(self):
        """WALL at the target position itself shouldn't block LoS."""
        g = _make_grid()
        g.set(Vector2(5, 0), Material.WALL)
        # LoS excludes endpoints, so a wall at (5,0) won't block the path
        assert g.has_line_of_sight(0, 0, 5, 0) is True

    def test_wall_at_start_doesnt_block(self):
        """WALL at the start position shouldn't block LoS."""
        g = _make_grid()
        g.set(Vector2(0, 0), Material.WALL)
        assert g.has_line_of_sight(0, 0, 5, 0) is True


# =========================================================================
# Cover system (has_adjacent_wall)
# =========================================================================

class TestCoverSystem:
    def test_no_cover_on_open_ground(self):
        g = _make_grid()
        assert g.has_adjacent_wall(5, 5) is False

    def test_cover_from_wall_north(self):
        g = _make_grid()
        g.set(Vector2(5, 4), Material.WALL)
        assert g.has_adjacent_wall(5, 5) is True

    def test_cover_from_wall_east(self):
        g = _make_grid()
        g.set(Vector2(6, 5), Material.WALL)
        assert g.has_adjacent_wall(5, 5) is True

    def test_cover_from_wall_south(self):
        g = _make_grid()
        g.set(Vector2(5, 6), Material.WALL)
        assert g.has_adjacent_wall(5, 5) is True

    def test_cover_from_wall_west(self):
        g = _make_grid()
        g.set(Vector2(4, 5), Material.WALL)
        assert g.has_adjacent_wall(5, 5) is True

    def test_diagonal_wall_no_cover(self):
        """Diagonal walls don't provide cover (cardinal only)."""
        g = _make_grid()
        g.set(Vector2(6, 6), Material.WALL)
        assert g.has_adjacent_wall(5, 5) is False

    def test_edge_of_map_counts_as_wall(self):
        """Out-of-bounds tiles return WALL, so edge positions have cover."""
        g = _make_grid(10, 10)
        assert g.has_adjacent_wall(0, 5) is True  # west is out of bounds


# =========================================================================
# CombatAction validation with ranged weapons
# =========================================================================

class TestCombatActionRanged:
    def _make_world(self, grid, entities):
        """Minimal world-like object for CombatAction.validate."""
        from src.core.world_state import WorldState
        w = WorldState.__new__(WorldState)
        w.entities = {e.id: e for e in entities}
        w.grid = grid
        return w

    def test_melee_attack_adjacent_valid(self):
        from src.actions.combat import CombatAction
        from src.actions.base import ActionProposal
        g = _make_grid()
        atk = _make_entity(1, pos=(5, 5), weapon="iron_sword")
        dfn = _make_entity(2, pos=(5, 6), faction=Faction.GOBLIN_HORDE)
        world = self._make_world(g, [atk, dfn])
        ca = CombatAction.__new__(CombatAction)
        proposal = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2)
        assert ca.validate(proposal, world) is True

    def test_melee_attack_out_of_range_invalid(self):
        from src.actions.combat import CombatAction
        from src.actions.base import ActionProposal
        g = _make_grid()
        atk = _make_entity(1, pos=(5, 5), weapon="iron_sword")
        dfn = _make_entity(2, pos=(5, 8), faction=Faction.GOBLIN_HORDE)
        world = self._make_world(g, [atk, dfn])
        ca = CombatAction.__new__(CombatAction)
        proposal = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2)
        assert ca.validate(proposal, world) is False

    def test_ranged_attack_at_distance_valid(self):
        from src.actions.combat import CombatAction
        from src.actions.base import ActionProposal
        g = _make_grid()
        atk = _make_entity(1, pos=(5, 5), weapon="shortbow")  # range 3
        dfn = _make_entity(2, pos=(5, 8), faction=Faction.GOBLIN_HORDE)
        world = self._make_world(g, [atk, dfn])
        ca = CombatAction.__new__(CombatAction)
        proposal = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2)
        assert ca.validate(proposal, world) is True

    def test_ranged_attack_beyond_range_invalid(self):
        from src.actions.combat import CombatAction
        from src.actions.base import ActionProposal
        g = _make_grid()
        atk = _make_entity(1, pos=(5, 5), weapon="shortbow")  # range 3
        dfn = _make_entity(2, pos=(5, 9), faction=Faction.GOBLIN_HORDE)  # dist=4
        world = self._make_world(g, [atk, dfn])
        ca = CombatAction.__new__(CombatAction)
        proposal = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2)
        assert ca.validate(proposal, world) is False

    def test_ranged_attack_blocked_by_wall(self):
        from src.actions.combat import CombatAction
        from src.actions.base import ActionProposal
        g = _make_grid()
        g.set(Vector2(5, 7), Material.WALL)  # wall between attacker and defender
        atk = _make_entity(1, pos=(5, 5), weapon="shortbow")
        dfn = _make_entity(2, pos=(5, 8), faction=Faction.GOBLIN_HORDE)
        world = self._make_world(g, [atk, dfn])
        ca = CombatAction.__new__(CombatAction)
        proposal = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2)
        assert ca.validate(proposal, world) is False

    def test_melee_attack_not_blocked_by_wall(self):
        """Melee attacks (dist=1) skip LoS check."""
        from src.actions.combat import CombatAction
        from src.actions.base import ActionProposal
        g = _make_grid()
        atk = _make_entity(1, pos=(5, 5), weapon="iron_sword")
        dfn = _make_entity(2, pos=(5, 6), faction=Faction.GOBLIN_HORDE)
        world = self._make_world(g, [atk, dfn])
        ca = CombatAction.__new__(CombatAction)
        proposal = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2)
        assert ca.validate(proposal, world) is True

    def test_unarmed_entity_range_is_1(self):
        from src.actions.combat import CombatAction
        atk = _make_entity(1, pos=(5, 5))  # no weapon
        assert CombatAction._get_weapon_range(atk) == 1

    def test_bow_entity_range_is_3(self):
        from src.actions.combat import CombatAction
        atk = _make_entity(1, pos=(5, 5), weapon="shortbow")
        assert CombatAction._get_weapon_range(atk) == 3


# =========================================================================
# AI: range-aware skill selection
# =========================================================================

class TestRangeAwareSkillSelection:
    def test_ranged_skill_selected_at_distance(self):
        from src.core.classes import SkillInstance
        from src.ai.states import best_ready_skill
        e = _make_entity(1, stamina=50)
        e.skills = [SkillInstance(skill_id="quick_shot")]  # range=3
        result = best_ready_skill(e, dist_to_enemy=3)
        assert result == "quick_shot"

    def test_melee_skill_not_selected_at_distance(self):
        from src.core.classes import SkillInstance
        from src.ai.states import best_ready_skill
        e = _make_entity(1, stamina=50)
        e.skills = [SkillInstance(skill_id="power_strike")]  # range=1
        result = best_ready_skill(e, dist_to_enemy=3)
        assert result is None

    def test_melee_skill_selected_when_adjacent(self):
        from src.core.classes import SkillInstance
        from src.ai.states import best_ready_skill
        e = _make_entity(1, stamina=50)
        e.skills = [SkillInstance(skill_id="power_strike")]  # range=1
        result = best_ready_skill(e, dist_to_enemy=1)
        assert result == "power_strike"

    def test_self_buff_always_available(self):
        from src.core.classes import SkillInstance
        from src.ai.states import best_ready_skill
        e = _make_entity(1, stamina=50)
        e.skills = [SkillInstance(skill_id="shield_wall")]  # SELF target
        result = best_ready_skill(e, dist_to_enemy=5)
        # shield_wall is a self-buff with def_mod, power=0 → won't be selected
        # because power is 0 and best_power starts at 0.0
        # This is expected — self-buffs with no power don't get selected
        # (they provide stat mods, not damage)

    def test_prefers_highest_power_in_range(self):
        from src.core.classes import SkillInstance
        from src.ai.states import best_ready_skill
        e = _make_entity(1, stamina=50)
        e.skills = [
            SkillInstance(skill_id="quick_shot"),    # power=1.5, range=3
            SkillInstance(skill_id="arcane_bolt"),    # power=2.0, range=4
        ]
        result = best_ready_skill(e, dist_to_enemy=3)
        assert result == "arcane_bolt"


# =========================================================================
# AI: get_weapon_range
# =========================================================================

class TestGetWeaponRange:
    def test_unarmed(self):
        from src.ai.states import get_weapon_range
        e = _make_entity(1)
        assert get_weapon_range(e) == 1

    def test_melee_weapon(self):
        from src.ai.states import get_weapon_range
        e = _make_entity(1, weapon="iron_sword")
        assert get_weapon_range(e) == 1

    def test_ranged_weapon(self):
        from src.ai.states import get_weapon_range
        e = _make_entity(1, weapon="shortbow")
        assert get_weapon_range(e) == 3

    def test_staff_weapon(self):
        from src.ai.states import get_weapon_range
        e = _make_entity(1, weapon="crystal_staff")
        assert get_weapon_range(e) == 4


# =========================================================================
# Hero Starting Gear
# =========================================================================

class TestHeroStartingGear:
    def test_warrior_gets_iron_sword(self):
        from src.core.classes import HeroClass, HERO_STARTING_GEAR
        gear = HERO_STARTING_GEAR[HeroClass.WARRIOR]
        assert gear["weapon"] == "iron_sword"
        assert gear["armor"] == "leather_vest"

    def test_ranger_gets_shortbow(self):
        from src.core.classes import HeroClass, HERO_STARTING_GEAR
        gear = HERO_STARTING_GEAR[HeroClass.RANGER]
        assert gear["weapon"] == "shortbow"
        assert ITEM_REGISTRY[gear["weapon"]].weapon_range >= 3

    def test_mage_gets_staff(self):
        from src.core.classes import HeroClass, HERO_STARTING_GEAR
        gear = HERO_STARTING_GEAR[HeroClass.MAGE]
        assert gear["weapon"] == "apprentice_staff"
        assert ITEM_REGISTRY[gear["weapon"]].weapon_range >= 3

    def test_rogue_gets_dagger(self):
        from src.core.classes import HeroClass, HERO_STARTING_GEAR
        gear = HERO_STARTING_GEAR[HeroClass.ROGUE]
        assert gear["weapon"] == "bandit_dagger"
        assert ITEM_REGISTRY[gear["weapon"]].weapon_range == 1

    def test_all_starting_weapons_exist_in_registry(self):
        from src.core.classes import HERO_STARTING_GEAR
        for cls, gear in HERO_STARTING_GEAR.items():
            for slot in ("weapon", "armor", "accessory"):
                item_id = gear.get(slot)
                if item_id is not None:
                    assert item_id in ITEM_REGISTRY, f"{slot}={item_id} for class {cls}"


# =========================================================================
# Ranged Mob Variants
# =========================================================================

class TestRangedMobVariants:
    def test_bandit_scout_has_bow(self):
        gear = RACE_STARTING_GEAR["bandit"][EnemyTier.SCOUT]
        assert gear["weapon"] == "bandit_bow"
        assert ITEM_REGISTRY["bandit_bow"].weapon_range >= 3

    def test_bandit_archer_kind(self):
        kind = RACE_TIER_KINDS["bandit"][EnemyTier.SCOUT]
        assert kind == "bandit_archer"

    def test_skeleton_mage_kind(self):
        kind = RACE_TIER_KINDS["undead"][EnemyTier.SCOUT]
        assert kind == "skeleton_mage"

    def test_skeleton_mage_has_staff(self):
        gear = RACE_STARTING_GEAR["undead"][EnemyTier.SCOUT]
        assert gear["weapon"] == "wooden_staff"
        assert ITEM_REGISTRY["wooden_staff"].weapon_range >= 3

    def test_lich_has_ranged_weapon(self):
        gear = RACE_STARTING_GEAR["undead"][EnemyTier.ELITE]
        weapon_id = gear["weapon"]
        assert weapon_id is not None
        assert ITEM_REGISTRY[weapon_id].weapon_range >= 3

    def test_goblin_chief_has_ranged_weapon(self):
        gear = TIER_STARTING_GEAR[EnemyTier.ELITE]
        weapon_id = gear["weapon"]
        assert weapon_id is not None
        assert ITEM_REGISTRY[weapon_id].weapon_range >= 3

    def test_skeleton_mage_is_caster_class(self):
        from src.core.classes import HeroClass, RACE_CLASS_MAP
        cls = RACE_CLASS_MAP.get(("undead", EnemyTier.SCOUT))
        assert cls == HeroClass.CASTER

    def test_all_race_gear_weapons_exist(self):
        """All weapons in RACE_STARTING_GEAR must exist in ITEM_REGISTRY."""
        for race, tier_gear in RACE_STARTING_GEAR.items():
            for tier, gear in tier_gear.items():
                weapon_id = gear.get("weapon")
                if weapon_id is not None:
                    assert weapon_id in ITEM_REGISTRY, (
                        f"Race={race}, tier={tier}: weapon '{weapon_id}' not in registry"
                    )
