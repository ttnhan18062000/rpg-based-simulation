import pytest
from src.core.entities.entity_builder import EntityBuilder
from src.core.models.enums import Archetype, GoalType, AIState
from src.core.models.social import SocialRegistry
from src.ai.brain import AIBrain
from src.config import SimulationConfig
from src.platform.rng import DeterministicRNG
from src.core.models.snapshot import Snapshot
from unittest.mock import MagicMock

@pytest.fixture
def config():
    return SimulationConfig()

@pytest.fixture
def rng():
    return DeterministicRNG(seed=100)

def test_archetype_behavioral_divergence(config, rng):
    """Verifies that different archetypes produce distinct motives in the same visible context."""
    # 1. Setup a Social Registry with a "Threatening Rival"
    registry = SocialRegistry()
    registry.update_bond(source_id=1, target_id=99, rivalry_delta=0.8, fear_delta=0.5)
    registry.update_bond(source_id=2, target_id=99, rivalry_delta=0.8, fear_delta=0.5)
    
    # 2. Build two entities with different archetypes
    # Slayer: aggressive, low agreeableness
    slayer = EntityBuilder(rng, 1).kind("hero").with_archetype(Archetype.BLOODTHIRSTY_SLAYER).build()
    # Defender: protective, high conscientiousness
    defender = EntityBuilder(rng, 2).kind("hero").with_archetype(Archetype.HONORABLE_DEFENDER).build()
    
    # 3. Visible Rival
    rival = EntityBuilder(rng, 99).kind("monster").build()
    
    # 4. Mock Snapshot
    snapshot = MagicMock(spec=Snapshot)
    snapshot.tick = 100
    snapshot.social_registry = registry
    snapshot.entities = {99: rival}
    snapshot.grid = MagicMock()
    snapshot.ground_items = {}
    snapshot.camps = []
    snapshot.nearby_entity_ids.return_value = [99]
    
    # 5. Run Brain appraisal for both
    brain = AIBrain(config, rng)
    
    def get_motives(actor):
        updates = []
        # _sensory_perception_phase returns (ctx, social_biases)
        ctx, biases = brain._sensory_perception_phase(actor, snapshot, updates)
        brain._memory_appraisal_phase(ctx, updates, biases)
        return next(u for u in updates if hasattr(u, "motives") and u.motives)

    # Slayer appraisal
    motive_update_slayer = get_motives(slayer)
    
    # Defender appraisal
    motive_update_defender = get_motives(defender)
    
    # 6. Compare COMBAT vs FLEE motives
    print(f"\nSlayer Motives: {motive_update_slayer.motives}")
    print(f"Defender Motives: {motive_update_defender.motives}")
    
    # Bloodthirsty Slayer has low Neuroticism (0.3) -> lower FLEE utility multiplier
    # Honorable Defender has low Neuroticism (0.2) -> even lower FLEE utility multiplier
    # But Slayer has high rivalry/aggressive archetypal traits.
    
    # The test should check if biases exist and are different
    assert GoalType.FLEE in motive_update_slayer.motive_utility_biases
    assert GoalType.COMBAT in motive_update_slayer.motive_utility_biases
    assert motive_update_slayer.motive_utility_biases != motive_update_defender.motive_utility_biases
