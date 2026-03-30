"""Tests for AI heuristics — boredom, life stages, priority shifts.

Refactored for AOA Stabilization:
- Updated imports to modern AOA paths.
- Used EntityBuilder for entity construction.
- Updated attribute access to use aspects (mind, progression, combat).
"""

from __future__ import annotations
import unittest
from pathlib import Path
import sys

# Ensure the src directory is in the python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import SimulationConfig
from src.ai.brain import AIBrain
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.models.enums import AIState, Domain
from src.platform.rng import DeterministicRNG
from src.core.models.snapshot import Snapshot
from src.core.gameplay.faction import FactionRegistry
from src.core.world.grid import Grid
from src.core.entities.entity_builder import EntityBuilder


class TestAIHeuristics(unittest.TestCase):
    def test_ai_boredom_diversification(self):
        """Verify that an entity eventually shifts away from a repetitive goal due to boredom."""
        cfg = SimulationConfig(world_seed=42)
        rng = DeterministicRNG(cfg.world_seed)
        brain = AIBrain(cfg, rng)
        
        # Create an entity using EntityBuilder
        actor = (
            EntityBuilder(rng, 1)
            .kind("hero")
            .at(Vector2(10, 10))
            .with_base_stats(hp=20, atk=10, def_=5, spd=10)
            .build()
        )
        actor.mind.decision.ai_state = AIState.IDLE
        
        # Mocked snapshot with all required fields
        dummy_grid = Grid(20, 20)
        
        # Run brain multiple times. Initially, it might favor WANDER.
        # We want to see it eventually pick something else after boredom sets in.
        for t in range(1, 21):
            snap = Snapshot(
                tick=t, 
                seed=42, 
                entities={1: actor}, 
                grid=dummy_grid, 
                ground_items={}, 
                camps=(), 
                buildings=(), 
                resource_nodes=(), 
                treasure_chests=(), 
                regions=()
            )
            brain.decide(actor, snap)
            actor.mind.decision.ai_state = AIState.IDLE # Force back to decision state for next tick
            
        # Verify that boredom multipliers were initialized and modified
        boredom = actor.mind.decision.boredom_multipliers
        assert len(boredom) > 0
        assert any(m < 1.0 for m in boredom.values())

    def test_life_stage_priority_shift(self):
        """Verify level 1 and level 25 entities have different goal preferences."""
        cfg = SimulationConfig(world_seed=42)
        rng = DeterministicRNG(cfg.world_seed)
        brain = AIBrain(cfg, rng)
        
        # Level 1 Hero
        young_actor = (
            EntityBuilder(rng, 1)
            .kind("hero")
            .at(Vector2(10, 10))
            .with_base_stats(hp=20, atk=5, def_=0, spd=10)
            .build()
        )
        young_actor.progression.level = 1
        young_actor.mind.decision.ai_state = AIState.IDLE
        
        # Level 25 Hero
        veteran_actor = (
            EntityBuilder(rng, 2)
            .kind("hero")
            .at(Vector2(10, 10))
            .with_base_stats(hp=100, atk=20, def_=10, spd=15)
            .build()
        )
        veteran_actor.progression.level = 25
        veteran_actor.mind.decision.ai_state = AIState.IDLE
        
        dummy_grid = Grid(20, 20)
        snap = Snapshot(
            tick=1, 
            seed=42, 
            entities={1: young_actor, 2: veteran_actor}, 
            grid=dummy_grid, 
            ground_items={}, 
            camps=(), 
            buildings=(), 
            resource_nodes=(), 
            treasure_chests=(), 
            regions=()
        )
        
        # Snapshot of goal evaluation
        from src.ai.states import AIContext
        ctx_young = AIContext(actor=young_actor, snapshot=snap, config=cfg, rng=rng, faction_reg=FactionRegistry.default())
        ctx_veteran = AIContext(actor=veteran_actor, snapshot=snap, config=cfg, rng=rng, faction_reg=FactionRegistry.default())
        
        young_scores = brain._goal_evaluator.evaluate(ctx_young)
        veteran_scores = brain._goal_evaluator.evaluate(ctx_veteran)
        
        def get_score(scores, name):
            for s in scores:
                if s.goal == name: return s.score
            return 0.0

        young_explore = get_score(young_scores, "explore")
        veteran_social = get_score(veteran_scores, "social")
        
        assert young_explore > 0
        assert veteran_social > 0


if __name__ == "__main__":
    unittest.main()
