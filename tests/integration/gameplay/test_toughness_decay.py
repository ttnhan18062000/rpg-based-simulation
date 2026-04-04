from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


"""Tests for toughness hardening and stat decay systems.

Refactored for AOA Stabilization:
- Updated imports to modern AOA paths.
- Used EntityBuilder for entity construction.
- Corrected attribute access (e.g., e.combat.hp, e.progression.level).
- Restored toughness hardening logic in src/actions/combat.py (already done).
- Updated stat decay test to call decay_attributes directly.
"""

import pytest
from src.config import SimulationConfig
from src.core.entities.entity import Entity
from src.core.models.vectors import Vector2
from src.core.gameplay.attributes import Attributes, AttributeCaps, decay_attributes
from src.core.models.enums import AIState, ActionType, Domain
from src.core.models.world_state import WorldState
from src.actions.combat import CombatAction
from src.platform.rng import DeterministicRNG
from src.core.world.grid import Grid
from src.systems.spatial_hash import SpatialHash
from unittest.mock import MagicMock, patch, ANY
from src.core.entities.entity_builder import EntityBuilder

def test_near_death_hardening():
    """Verify that surviving at low HP increases Max HP."""
    cfg = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(cfg.world_seed)
    combat_action = CombatAction(cfg, rng)
    
    # Setup Attacker
    attacker = (
        EntityBuilder(rng, 1)
        .kind("hero")
        .at(Vector2(10, 10))
        .with_base_stats(hp=20, atk=10)
        .build()
    )
    
    # Setup Defender
    defender = (
        EntityBuilder(rng, 2)
        .kind("goblin")
        .at(Vector2(11, 10))
        .with_base_stats(hp=11, def_=0)
        .build()
    )
    # Ensure max_hp is 20 for the 15% threshold check (11/20 > 15%, but after 10 dmg: 1/20 < 15%)
    defender.combat.max_hp = 20
    defender.combat.hp = 11
    
    grid = Grid(20, 20)
    spatial = SpatialHash(cell_size=2)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    world.add_entity(attacker)
    world.add_entity(defender)
    
    from src.actions.base import ActionProposal
    proposal = ActionProposal(actor_id=attacker.id, verb=ActionType.ATTACK, target=defender.id, reason="Test")
    
    old_max_hp = defender.combat.max_hp
    # Force damage to trigger hardening
    with patch('src.actions.combat.DamageResolutionService.resolve', return_value=(10, False, False, {"raw_damage": 10, "mitigation": 0})):
        combat_action.apply(proposal, world)
    
    # In AOA, CombatAction.apply DOES NOT mutate defender.combat.hp directly.
    # It appends updates to the proposal.
    # However, it SHOULD still update max_hp if the threshold is met by predicted damage.
    assert defender.combat.max_hp == old_max_hp + 1

def test_stat_decay_inactivity():
    """Verify that stat decay can be triggered."""
    cfg = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(cfg.world_seed)
    
    # Entity with some training progress
    actor = (
        EntityBuilder(rng, 1)
        .kind("hero")
        .at(Vector2(10, 10))
        .build()
    )
    actor.progression.attributes = Attributes(str_=10, _str_frac=0.5)
    actor.progression.attribute_caps = AttributeCaps(str_cap=20)
    actor.mind.decision.consecutive_idle_ticks = 1001
    
    # Call decay directly since WorldLoop internal methods are gone
    # decay_attributes picks a random attribute to decay
    with patch('src.platform.rng.DeterministicRNG.next_int', return_value=0): # 0 is str
        # Force decay by providing a larger amount than 0.5 to trigger integer decay
        decay_attributes(actor, rng, decay_amount=0.6)
        # Should have triggered 0.5 - 0.6 = -0.1 < 0, so str_ becomes 9 and _str_frac becomes 0.9
        assert actor.progression.attributes.str_ == 9
        assert actor.progression.attributes._str_frac == 0.9

def test_toughness_hardening_integration():
    """Integration test for the restored hardening logic in CombatAction."""
    cfg = SimulationConfig(world_seed=42)
    rng = DeterministicRNG(cfg.world_seed)
    combat_action = CombatAction(cfg, rng)
    
    defender = (
        EntityBuilder(rng, 2)
        .at(Vector2(11, 10))
        .with_base_stats(hp=20)
        .build()
    )
    # Force low HP
    defender.combat.hp = 2 
    # 2/20 = 10% < 15%
    
    attacker = (
        EntityBuilder(rng, 1)
        .at(Vector2(10, 10))
        .with_base_stats(atk=10)
        .build()
    )
    
    world = WorldState(seed=42, grid=Grid(20, 20), spatial_index=SpatialHash(2))
    world.add_entity(attacker)
    world.add_entity(defender)
    
    from src.actions.base import ActionProposal
    proposal = ActionProposal(actor_id=attacker.id, verb=ActionType.ATTACK, target=defender.id)
    
    old_max_hp = defender.combat.max_hp
    
    # We must ensure DamageResolutionService doesn't kill the defender
    # Mock resolve to return 0 damage but NOT evasion
    # AOA FIX: resolve returns 4 items: (damage, is_crit, is_evasion, details)
    with patch('src.actions.combat.DamageResolutionService.resolve') as mock_resolve:
        mock_resolve.return_value = (0, False, False, {"raw_damage": 0, "mitigation": 0})
        combat_action.apply(proposal, world)
        
    assert defender.combat.max_hp == old_max_hp + 1
