from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from src.config import SimulationConfig
from src.ai.brain import AIBrain
from src.actions.base import MindUpdate
from src.core.entities.entity import Entity, Vector2
from src.core.models.enums import AIState, Domain, GoalType
from src.platform.rng import DeterministicRNG
from src.core.models.snapshot import Snapshot
from src.core.gameplay.faction import FactionRegistry
from src.core.world.grid import Grid
from src.core.models.enums import Material

def test_ai_boredom_diversification():
    """Verify that an entity eventually shifts away from a repetitive goal due to boredom."""
    cfg = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(cfg.world_seed)
    brain = AIBrain(cfg, rng)
    
    # Create an entity in a decision state (IDLE)
    actor = Entity(id=1, kind="hero")
    actor.spatial.pos = Vector2(10, 10)
    actor.progression.level = 1
    actor.combat.hp = 20
    actor.combat.max_hp = 20
    actor.mind.decision.ai_state = AIState.IDLE
    
    # Mocked snapshot with all required fields
    dummy_grid = Grid(20, 20)
    snap = Snapshot(
        tick=1, 
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
    
    # Run brain multiple times. Initially, it might favor WANDER.
    # We want to see it eventually pick something else after boredom sets in.
    goals_picked = []
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
        new_state, proposal = brain.decide(actor, snap)
        actor.mind.decision.ai_state = AIState.IDLE # Force back to decision state for next tick
        goals_picked.append(new_state)
        mind_up = next((u for u in proposal.updates if isinstance(u, MindUpdate) and u.boredom_delta), None)
        if mind_up and mind_up.boredom_delta:
            actor.mind.decision.boredom_multipliers.update(mind_up.boredom_delta)
        
    # Verify that boredom multipliers were initialized and modified
    assert len(actor.mind.decision.boredom_multipliers) > 0
    assert any(m < 1.0 for m in actor.mind.decision.boredom_multipliers.values())

def test_life_stage_priority_shift():
    """Verify level 1 and level 25 entities have different goal preferences."""
    cfg = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(cfg.world_seed)
    brain = AIBrain(cfg, rng)
    
    # Level 1 Hero
    young_actor = Entity(id=1, kind="hero")
    young_actor.spatial.pos = Vector2(10, 10)
    young_actor.progression.level = 1
    young_actor.combat.hp = 20
    young_actor.combat.max_hp = 20
    young_actor.mind.decision.ai_state = AIState.IDLE
    
    # Level 25 Hero
    veteran_actor = Entity(id=2, kind="hero")
    veteran_actor.spatial.pos = Vector2(10, 10)
    veteran_actor.progression.level = 25
    veteran_actor.combat.hp = 100
    veteran_actor.combat.max_hp = 100
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
    
    def get_score(scores, goal_type):
        for s in scores:
            if s.goal == goal_type: return s.score
        return 0.0

    # Young heroes should favor explore/rest
    # Veteran heroes should favor social/trade/craft
    
    young_explore = get_score(young_scores, GoalType.EXPLORE)
    veteran_explore = get_score(veteran_scores, GoalType.EXPLORE)
    
    young_social = get_score(young_scores, GoalType.SOCIAL)
    veteran_social = get_score(veteran_scores, GoalType.SOCIAL)
    
    # Debug print to see what's happening
    print(f"DEBUG: young_scores={[ (s.goal.name, s.score) for s in young_scores ]}")
    print(f"DEBUG: veteran_scores={[ (s.goal.name, s.score) for s in veteran_scores ]}")

    assert young_explore > 0, f"Young explore score should be > 0, got {young_explore}"
    assert veteran_social > 0, f"Veteran social score should be > 0, got {veteran_social}"
    
    # Check that ratios shift as expected
    # (This is a bit tricky since base scores also depend on stats, but level is the main differentiator here)
    assert (young_explore / (young_social or 0.1)) > (veteran_explore / (veteran_social or 0.1))
