"""Tests for subsystem tick rates (design-02).

Covers:
- Subsystems always run even when no entities are ready (empty tick fix)
- Configurable rate divisors control subsystem frequency
- Core/environment/economy groups fire at expected intervals
"""


from unittest.mock import MagicMock, patch, call
from src.config import SimulationConfig
from tests.helpers.legacy_stats import Stats
from src.core.entities.entity import Entity, Vector2
from src.core.gameplay.faction import Faction
from src.core.models.enums import AIState
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.engine.world_loop import WorldLoop
from src.engine.conflict_resolver import ConflictResolver
from src.engine.worker_pool import WorkerPool
from src.systems.world.generator import EntityGenerator


def _make_config(**overrides) -> SimulationConfig:
    defaults = dict(
        max_ticks=100,
        initial_entity_count=0,
        generator_max_entities=0,
        num_camps=0,
        num_workers=1,
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
    from src.platform.rng import DeterministicRNG
    config = config or _make_config()
    world = world or _make_world(config)
    rng = DeterministicRNG(seed=42)
    brain = AIBrain(config, rng)
    pool = WorkerPool(config, brain, rng)
    resolver = ConflictResolver(config, rng)
    gen = EntityGenerator(config, rng)
    loop = WorldLoop(config, world, pool, resolver, gen, rng=rng)
    return loop


class TestSubsystemsAlwaysRun:
    """Subsystems must tick even when no entities are ready (empty tick bug fix)."""

    def test_effects_tick_on_empty_tick(self):
        """Status effects should decay even when no entities act."""
        loop = _make_loop()
        entity = Entity(id=1, kind="hero")
        # Initialize core aspects
        entity.combat.hp = 50
        entity.combat.max_hp = 100
        
        entity.next_act_at = 999  # Won't be ready for a long time
        from src.core.gameplay.effects import StatusEffect, EffectType
        entity.combat.effects.append(StatusEffect(
            effect_type=EffectType.SKILL_BUFF, remaining_ticks=3, source="test",
        ))
        loop.world.add_entity(entity)

        # Run a tick — entity is NOT ready, but CombatSystem should still tick effects
        loop.tick_once()
        ent = loop.world.entities[1]
        assert len(ent.combat.effects) > 0
        assert ent.combat.effects[0].remaining_ticks == 2

    def test_stamina_regens_on_empty_tick(self):
        """Stamina should regen even when no entities are ready to act."""
        loop = _make_loop()
        entity = Entity(id=1, kind="hero")
        entity.progression.stamina = 50
        entity.progression.max_stamina = 100
        entity.mind.decision.ai_state = AIState.WANDER
        entity.next_act_at = 999
        loop.world.add_entity(entity)

        old_stamina = entity.progression.stamina
        loop.tick_once()
        # Stamina is in ProgressionSystem now
        assert loop.world.entities[1].progression.stamina > old_stamina

    def test_skill_cooldowns_tick_on_empty_tick(self):
        """Skill cooldowns should count down even on empty ticks."""
        loop = _make_loop()
        entity = Entity(id=1, kind="hero")
        entity.next_act_at = 999
        from src.core.gameplay.classes import SkillInstance
        skill = SkillInstance(skill_id="power_strike", cooldown_remaining=5)
        entity.progression.skills.append(skill)
        loop.world.add_entity(entity)

        loop.tick_once()
        # Cooldowns are in ProgressionSystem now
        assert loop.world.entities[1].progression.skills[0].cooldown_remaining == 4


class TestSubsystemRateDivisors:
    """Configurable rate divisors control subsystem frequency."""

    def test_core_runs_every_tick(self):
        config = _make_config(subsystem_rate_core=1)
        loop = _make_loop(config=config)

        from src.systems.gameplay.combat_system import CombatSystem
        with patch.object(CombatSystem, 'on_tick', return_value=None) as mock_tick:
            loop._system_manager.tick(loop.world, 0)
            loop._system_manager.tick(loop.world, 1)
            loop._system_manager.tick(loop.world, 2)
            assert mock_tick.call_count == 3

    def test_environment_runs_every_2nd_tick(self):
        config = _make_config(subsystem_rate_environment=2)
        loop = _make_loop(config=config)

        from src.systems.world.environment_system import EnvironmentSystem
        with patch.object(EnvironmentSystem, 'on_tick', return_value=None) as mock_tick:
            for t in range(10):
                loop._system_manager.tick(loop.world, t)
            assert mock_tick.call_count == 5

    def test_economy_runs_at_configured_rates(self):
        """Verify that economy systems (now in SystemManager) run at their configured rates."""
        config = _make_config(subsystem_rate_economy=5)
        loop = _make_loop(config=config)
        
        from src.systems.world.world_object_system import WorldObjectSystem
        with patch.object(WorldObjectSystem, 'on_tick', return_value=None) as mock_tick:
            for t in range(20):
                loop._system_manager.tick(loop.world, t)
            # 20 ticks, rate 5 -> 4 times (0, 5, 10, 15)
            assert mock_tick.call_count == 4

    def test_all_subsystems_run_on_tick_0(self):
        """All groups should fire on tick 0 regardless of rate."""
        config = _make_config(
            subsystem_rate_core=3,
            subsystem_rate_environment=7,
            subsystem_rate_economy=13,
        )
        loop = _make_loop(config=config)

        from src.systems.gameplay.combat_system import CombatSystem
        from src.systems.world.environment_system import EnvironmentSystem
        from src.systems.world.world_object_system import WorldObjectSystem
        
        with patch.object(CombatSystem, 'on_tick', return_value=None) as m1, \
             patch.object(EnvironmentSystem, 'on_tick', return_value=None) as m2, \
             patch.object(WorldObjectSystem, 'on_tick', return_value=None) as m3:
            loop._system_manager.tick(loop.world, 0)
            assert m1.call_count == 1
            assert m2.call_count == 1
            assert m3.call_count == 1

    def test_rate_1_means_every_tick_for_all(self):
        """Setting all rates to 1 means everything runs every tick."""
        config = _make_config(
            subsystem_rate_core=1,
            subsystem_rate_environment=1,
            subsystem_rate_economy=1,
        )
        loop = _make_loop(config=config)

        from src.systems.gameplay.combat_system import CombatSystem
        from src.systems.world.environment_system import EnvironmentSystem
        from src.systems.world.world_object_system import WorldObjectSystem

        with patch.object(CombatSystem, 'on_tick', return_value=None) as m1, \
             patch.object(EnvironmentSystem, 'on_tick', return_value=None) as m2, \
             patch.object(WorldObjectSystem, 'on_tick', return_value=None) as m3:
            for t in range(5):
                loop._system_manager.tick(loop.world, t)
            assert m1.call_count == 5
            assert m2.call_count == 5
            assert m3.call_count == 5


class TestConfigDefaults:
    """Config defaults for subsystem rates are reasonable."""

    def test_default_core_rate_is_1(self):
        cfg = SimulationConfig()
        assert cfg.subsystem_rate_core == 1

    def test_default_environment_rate_is_2(self):
        cfg = SimulationConfig()
        assert cfg.subsystem_rate_environment == 2

    def test_default_economy_rate_is_5(self):
        cfg = SimulationConfig()
        assert cfg.subsystem_rate_economy == 5
