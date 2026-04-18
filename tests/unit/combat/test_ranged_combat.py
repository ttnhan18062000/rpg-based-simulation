import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


"""Tests for F4: Ranged Combat Positioning.

Refactored for AOA Stabilization:
- Updated imports to modern module locations.
- Used EntityBuilder for all entity construction.
- Updated all test cases to use aspect paths (combat, spatial, inventory).
- Aligned with authoritative CombatAction validation.
"""

import unittest
from pathlib import Path

# Ensure the src directory is in the python path

from src.actions.combat import CombatAction
from src.actions.base import ActionProposal
from src.core.models.enums import AIState, ActionType, DamageType, EnemyTier, Faction
from src.core.world.grid import Grid, Material
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.entities.entity_builder import EntityBuilder
from src.core.models.world_state import WorldState
from src.platform.rng import DeterministicRNG
from src.platform.spatial_hash import SpatialHash
from src.config import SimulationConfig


def _make_entity(
    eid: int, kind: str = "hero", pos: tuple = (0, 0),
    hp: int = 50, atk: int = 10, def_: int = 5, spd: int = 10,
    faction: Faction = Faction.HERO_GUILD,
    weapon: str | None = None,
) -> Entity:
    """Helper to create a test entity with AOA aspects."""
    rng = DeterministicRNG(42)
    builder = (
        EntityBuilder(rng, eid)
        .kind(kind)
        .at(Vector2(*pos))
        .faction(faction)
        .with_base_stats(hp=hp, atk=atk, def_=def_, spd=spd)
    )
    if weapon:
        builder.with_inventory(weapon=weapon)
    return builder.build()


def _make_grid(width: int = 20, height: int = 20) -> Grid:
    """Create a simple floor grid."""
    g = Grid(width, height)
    for y in range(height):
        for x in range(width):
            g.set(Vector2(x, y), Material.FLOOR)
    return g


class TestWeaponRange(unittest.TestCase):
    def test_melee_weapon_default_range(self):
        sword = ITEM_REGISTRY["iron_sword"]
        assert sword.weapon_range == 1

    def test_shortbow_range(self):
        bow = ITEM_REGISTRY["shortbow"]
        assert bow.weapon_range == 3

    def test_longbow_range(self):
        bow = ITEM_REGISTRY["longbow"]
        assert bow.weapon_range == 4


class TestLineOfSight(unittest.TestCase):
    def test_clear_line_of_sight(self):
        g = _make_grid()
        assert g.has_line_of_sight(0, 0, 5, 0) is True

    def test_clear_diagonal(self):
        g = _make_grid()
        assert g.has_line_of_sight(0, 0, 3, 3) is True

    def test_wall_blocks_line_of_sight(self):
        g = _make_grid()
        g.set(Vector2(3, 0), Material.WALL)
        assert g.has_line_of_sight(0, 0, 5, 0) is False

    def test_wall_on_diagonal_blocks(self):
        g = _make_grid()
        g.set(Vector2(1, 1), Material.WALL)
        assert g.has_line_of_sight(0, 0, 2, 2) is False

    def test_adjacent_always_visible(self):
        g = _make_grid()
        g.set(Vector2(1, 1), Material.WALL)
        # Adjacent tiles should ignore LOS blocking if using certain rules, 
        # but pure LOS usually respects blocks. 
        # Standard AOA: adjacent is always visible.
        assert g.has_line_of_sight(0, 0, 1, 1) is True

    def test_wall_at_endpoint_doesnt_block(self):
        g = _make_grid()
        g.set(Vector2(5, 0), Material.WALL)
        assert g.has_line_of_sight(0, 0, 5, 0) is True

    def test_wall_at_start_doesnt_block(self):
        g = _make_grid()
        g.set(Vector2(0, 0), Material.WALL)
        assert g.has_line_of_sight(0, 0, 5, 0) is True


class TestCoverSystem(unittest.TestCase):
    def test_no_cover_on_open_ground(self):
        g = _make_grid()
        assert g.has_adjacent_wall(5, 5) is False

    def test_cover_from_wall_north(self):
        g = _make_grid()
        g.set(Vector2(5, 4), Material.WALL)
        assert g.has_adjacent_wall(5, 5) is True


class TestCombatActionRanged(unittest.TestCase):
    def setUp(self):
        self.config = SimulationConfig()
        self.rng = DeterministicRNG(42)
        self.ca = CombatAction(self.config, self.rng)

    def _make_world(self, grid, entities):
        spatial = SpatialHash(cell_size=16)
        w = WorldState(seed=42, grid=grid, spatial_index=spatial)
        for e in entities:
            w.add_entity(e)
        return w

    def test_melee_attack_adjacent_valid(self):
        g = _make_grid()
        atk = _make_entity(1, pos=(5, 5), weapon="iron_sword")
        dfn = _make_entity(2, pos=(5, 6), faction=Faction.GOBLIN_HORDE)
        world = self._make_world(g, [atk, dfn])
        proposal = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2)
        assert self.ca.validate(proposal, world) is True

    def test_melee_attack_out_of_range_invalid(self):
        g = _make_grid()
        atk = _make_entity(1, pos=(5, 5), weapon="iron_sword")
        dfn = _make_entity(2, pos=(5, 8), faction=Faction.GOBLIN_HORDE)
        world = self._make_world(g, [atk, dfn])
        proposal = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2)
        print(f"DEBUG_TEST: AtkPos={atk.spatial.pos}, DfnPos={dfn.spatial.pos}, Dist={atk.spatial.pos.manhattan(dfn.spatial.pos)}")
        print(f"DEBUG_TEST: Weapon={atk.inventory.weapon if atk.inventory else 'NONE'}")
        val = self.ca.validate(proposal, world)
        print(f"DEBUG_TEST: Validation result={val}")
        assert val is False

    def test_ranged_attack_at_distance_valid(self):
        g = _make_grid()
        atk = _make_entity(1, pos=(5, 5), weapon="shortbow")  # range 3
        dfn = _make_entity(2, pos=(5, 8), faction=Faction.GOBLIN_HORDE)
        world = self._make_world(g, [atk, dfn])
        proposal = ActionProposal(actor_id=1, verb=ActionType.ATTACK, target=2)
        assert self.ca.validate(proposal, world) is True

    def test_unarmed_entity_range_is_1(self):
        atk = _make_entity(1, pos=(5, 5))  # no weapon
        assert self.ca._get_weapon_range(atk) == 1

    def test_bow_entity_range_is_3(self):
        atk = _make_entity(1, pos=(5, 5), weapon="shortbow")
        assert self.ca._get_weapon_range(atk) == 3


class TestRangeAwareSkillSelection(unittest.TestCase):
    def test_ranged_skill_selected_at_distance(self):
        from src.core.gameplay.classes import SkillInstance
        from src.ai.states import best_ready_skill; from tests.helpers.ai_test_utils import make_test_ai_context
        e = _make_entity(1)
        e.progression.stamina = 50
        e.progression.skills = [SkillInstance(skill_id="quick_shot")]  # range=3
        result = enemy = _make_entity(2, pos=(3, 0)); ctx = make_test_ai_context(e, enemies=[enemy]); result = best_ready_skill(ctx, enemy)
        assert result == "quick_shot"

    def test_melee_skill_not_selected_at_distance(self):
        from src.core.gameplay.classes import SkillInstance
        from src.ai.states import best_ready_skill; from tests.helpers.ai_test_utils import make_test_ai_context
        e = _make_entity(1)
        e.progression.stamina = 50
        e.progression.skills = [SkillInstance(skill_id="power_strike")]  # range=1
        result = enemy = _make_entity(2, pos=(3, 0)); ctx = make_test_ai_context(e, enemies=[enemy]); result = best_ready_skill(ctx, enemy)
        assert result is None


class TestHeroStartingGear(unittest.TestCase):
    def test_warrior_gets_iron_sword(self):
        from src.core.gameplay.classes import HeroClass, HERO_STARTING_GEAR
        gear = HERO_STARTING_GEAR[HeroClass.WARRIOR]
        assert gear["weapon"] == "iron_sword"

    def test_ranger_gets_shortbow(self):
        from src.core.gameplay.classes import HeroClass, HERO_STARTING_GEAR
        gear = HERO_STARTING_GEAR[HeroClass.RANGER]
        assert gear["weapon"] == "shortbow"
