"""Tests for subsystem tick rates (design-02).

Refactored for AOA Stabilization:
- Updated imports to modern AOA paths.
- Used EntityBuilder for entity construction.
- Updated WorkerPool and WorldLoop construction.
- Updated attribute access to use aspects.
- Updated subsystem tests to mock System.on_tick instead of WorldLoop internal methods.
"""

from __future__ import annotations
import unittest
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch, ANY

# Ensure the src directory is in the python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import SimulationConfig
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.models.enums import AIState, Faction
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.systems.spatial_hash import SpatialHash
from src.engine.world_loop import WorldLoop
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.systems.world.generator import EntityGenerator
from src.core.entities.entity_builder import EntityBuilder
from src.platform.rng import DeterministicRNG


def _make_config(**overrides) -> SimulationConfig:
    defaults = dict(
        max_ticks=100,
        initial_entity_count=0,
        generator_max_entities=0,
        num_camps=0,
        subsystem_rate_core=1,
        subsystem_rate_environment=2,
        subsystem_rate_economy=5,
    )
    defaults.update(overrides)
    return SimulationConfig(**defaults)


def _make_world(config: SimulationConfig) -> WorldState:
    grid = Grid(32, 32)
    spatial = SpatialHash(config.spatial_cell_size)
    return WorldState(seed=42, grid=grid, spatial_index=spatial)


def _make_loop(config=None, world=None) -> WorldLoop:
    from src.ai.brain import AIBrain
    config = config or _make_config()
    world = world or _make_world(config)
    rng = DeterministicRNG(seed=42)
    brain = AIBrain(config, rng)
    pool = WorkerPool(config, brain, rng)
    resolver = ConflictResolver(config, rng)
    gen = EntityGenerator(config, rng)
    loop = WorldLoop(config, world, pool, resolver, gen, rng=rng)
    return loop


class TestSubsystemsAlwaysRun(unittest.TestCase):
    """Subsystems must tick even when no entities are ready (empty tick bug fix)."""

    def setUp(self):
        self.rng = DeterministicRNG(42)

    def test_effects_tick_on_empty_tick(self):
        """Status effects should decay even when no entities act."""
        loop = _make_loop()
        entity = (
            EntityBuilder(self.rng, 1)
            .kind("hero")
            .at(Vector2(5, 5))
            .with_base_stats(hp=50)
            .build()
        )
        entity.identity.identity.faction = Faction.HERO_GUILD
        entity.next_act_at = 999.0
        
        from src.core.gameplay.effects import StatusEffect, EffectType
        entity.combat.effects.append(StatusEffect(
            effect_type=EffectType.SKILL_BUFF, remaining_ticks=3, source="test",
        ))
        loop.world.add_entity(entity)

        # Run a tick
        loop.tick_once()
        ent = loop.world.entities[1]
        assert len(ent.combat.effects) > 0
        assert ent.combat.effects[0].remaining_ticks == 2

    def test_stamina_regens_on_empty_tick(self):
        """Stamina should regen even when no entities are ready to act."""
        loop = _make_loop()
        entity = (
            EntityBuilder(self.rng, 1)
            .kind("hero")
            .at(Vector2(5, 5))
            .with_base_stats(hp=100)
            .build()
        )
        entity.identity.identity.faction = Faction.HERO_GUILD
        entity.progression.progression.stamina = 50
        entity.progression.max_stamina = 100
        entity.mind.decision.ai_state = AIState.WANDER
        entity.next_act_at = 999.0
        loop.world.add_entity(entity)

        old_stamina = entity.progression.progression.stamina
        loop.tick_once()
        assert loop.world.entities[1].progression.progression.stamina > old_stamina


class TestSubsystemRateDivisors(unittest.TestCase):
    """Configurable rate divisors control subsystem frequency."""

    def test_core_runs_every_tick(self):
        config = _make_config(subsystem_rate_core=1)
        loop = _make_loop(config=config)
        
        from src.systems.gameplay.combat_system import CombatSystem
        with patch.object(CombatSystem, 'on_tick', return_value=None) as mock_combat:
            # We need to re-initialize because the loop already has an instance
            # Or better, just find the instance and mock its on_tick
            for s, rate in loop._system_manager._systems:
                if isinstance(s, CombatSystem):
                    s.on_tick = mock_combat
            
            for t in range(3):
                loop._system_manager.tick(loop.world, t)
            
            assert mock_combat.call_count == 3

    def test_environment_runs_every_2nd_tick(self):
        config = _make_config(subsystem_rate_environment=2)
        loop = _make_loop(config=config)

        from src.systems.world.environment_system import EnvironmentSystem
        with patch.object(EnvironmentSystem, 'on_tick', return_value=None) as mock_env:
            for s, rate in loop._system_manager._systems:
                if isinstance(s, EnvironmentSystem):
                    s.on_tick = mock_env
            
            for t in range(10):
                loop._system_manager.tick(loop.world, t)
            
            assert mock_env.call_count == 5

    def test_economy_runs_every_5th_tick(self):
        config = _make_config(subsystem_rate_economy=5)
        loop = _make_loop(config=config)

        from src.systems.gameplay.economy_system import EconomySystem
        with patch.object(EconomySystem, 'on_tick', return_value=None) as mock_eco:
            for s, rate in loop._system_manager._systems:
                if isinstance(s, EconomySystem):
                    s.on_tick = mock_eco
            
            for t in range(20):
                loop._system_manager.tick(loop.world, t)
            
            assert mock_eco.call_count == 4


if __name__ == "__main__":
    unittest.main()
