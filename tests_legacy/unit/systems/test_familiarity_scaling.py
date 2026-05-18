import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


"""Tests for familiarity scaling based on Charisma."""

import pytest
from unittest.mock import MagicMock
from src_legacy.systems.lifecycle.hero_lifecycle_system import HeroLifecycleSystem
from src_legacy.systems.infrastructure.base import SystemContext
from src_legacy.core.entities.entity_builder import EntityBuilder
from src_legacy.core.entities.entity import Vector2
from src_legacy.platform.rng import DeterministicRNG

def test_cha_impacts_familiarity_gain():
    """Verify that a hero with higher CHA gains familiarity faster."""
    config = MagicMock()
    config.vision_range = 5
    rng = MagicMock()
    drng = DeterministicRNG(42)
    
    system = HeroLifecycleSystem(config, rng)
    
    # Hero 1: High CHA (50)
    h1 = (
        EntityBuilder(drng, 1).kind("hero")
        .at(Vector2(0, 0))
        .with_base_stats(hp=100)
        .with_attributes(cha=50)
        .build()
    )
    
    # Hero 2: Low CHA (0)
    h2 = (
        EntityBuilder(drng, 2).kind("hero")
        .at(Vector2(1, 1))
        .with_base_stats(hp=100)
        .with_attributes(cha=0)
        .build()
    )
    
    world = MagicMock()
    world.entities = {1: h1, 2: h2}
    world.entities_at_radius.return_value = [h2, h1]
    
    # Mock social registry in world
    from src_legacy.core.models.social import SocialRegistry
    world.social_registry = SocialRegistry()
    
    ctx = SystemContext(
        config=config,
        world=world,
        rng=rng,
        generator=MagicMock(),
        faction_reg=MagicMock(),
        emit=MagicMock()
    )
    
    # Initial run
    system._tick_proximity_familiarity(ctx, 100)
    
    # Expected gain for CHA 50: 0.002 * (1 + 50*0.01) = 0.002 * 1.5 = 0.003
    bond = world.social_registry.get_bond(h1.id, h2.id)
    fam_score = bond.familiarity
    assert fam_score > 0.002 # Should be 0.003
    assert fam_score == pytest.approx(0.003)
