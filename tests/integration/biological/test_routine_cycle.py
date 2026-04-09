import pytest
from unittest.mock import MagicMock
from src.core.entities.entity import Entity
from src.core.models.world_state import WorldState
from src.config import SimulationConfig
from src.systems.gameplay.action_system import ActionSystem
from src.actions.base import ActionProposal
from src.core.models.enums import ActionType, AIState
from src.core.aspects.inventory import InventoryAspect

@pytest.mark.integration
class TestRoutineCycleIntegration:
    """Verifies the Phase 2 Stage 3 biological needs cycle."""

    def test_biological_decay_and_forced_sleep(self):
        # 1. Setup minimal world
        mock_grid = MagicMock()
        mock_spatial = MagicMock()
        world = WorldState(seed=42, grid=mock_grid, spatial_index=mock_spatial)
        
        # SimulationConfig is frozen, so we must pass values to constructor
        config = SimulationConfig(
            sleep_decay_rate=0.1, 
            hunger_decay_rate=0.1,
            sleep_recovery_rate=0.2
        )
        
        hero = Entity(id=1, kind="hero")
        hero.mind.routine.sleep_debt = 0.8
        hero.mind.routine.hunger_level = 0.8
        world.entities[1] = hero
        
        # 2. Apply decay
        ActionSystem._apply_biological_decay(world, config)
        
        # 3. Verification: Needs increased
        assert hero.mind.routine.sleep_debt >= 0.9
        assert hero.mind.routine.hunger_level >= 0.9
        
        # 4. Another tick should force sleep
        ActionSystem._apply_biological_decay(world, config)
        # It reached 1.0, triggered sleep, and immediately recovered by recovery_rate (0.2)
        assert hero.mind.routine.is_sleeping is True
        assert hero.mind.routine.sleep_debt <= 0.8

    def test_eat_action_flow(self):
        # 1. Setup
        mock_grid = MagicMock()
        mock_spatial = MagicMock()
        world = WorldState(seed=42, grid=mock_grid, spatial_index=mock_spatial)
        config = SimulationConfig()
        
        hero = Entity(id=1, kind="hero")
        hero.mind.routine.hunger_level = 0.8
        # Explicitly initialize inventory
        hero.inventory = InventoryAspect(items=["wild_berries"])
        world.entities[1] = hero
        
        # 2. Create EAT proposal
        proposal = ActionProposal(
            actor_id=1,
            verb=ActionType.EAT,
            metadata={"item_id": "wild_berries"}
        )
        
        # 3. Apply via ActionSystem
        rng = MagicMock()
        ActionSystem.apply_action_state_transitions(world, config, [proposal], rng)
        
        # 4. Verification
        # Hunger should be reduced (wild_berries = -0.3)
        assert hero.mind.routine.hunger_level < 0.6
        # Item should be removed from inventory
        assert "wild_berries" not in hero.inventory.items

    def test_sleep_action_flow(self):
         # 1. Setup
        mock_grid = MagicMock()
        mock_spatial = MagicMock()
        world = WorldState(seed=42, grid=mock_grid, spatial_index=mock_spatial)
        config = SimulationConfig()
        
        hero = Entity(id=1, kind="hero")
        hero.mind.routine.sleep_debt = 0.8
        hero.mind.routine.is_sleeping = False
        world.entities[1] = hero
        
        # 2. Propose SLEEP
        proposal = ActionProposal(
            actor_id=1,
            verb=ActionType.SLEEP
        )
        
        # 3. Apply
        rng = MagicMock()
        ActionSystem.apply_action_state_transitions(world, config, [proposal], rng)
        
        # 4. Verification
        assert hero.mind.routine.is_sleeping is True
        # Note: apply_action_state_transitions ALSO updates AIState if new_ai_state is set in proposal
        # SleepAction.apply sets proposal.new_ai_state = AIState.SLEEPING
        assert hero.mind.decision.ai_state == AIState.SLEEPING
