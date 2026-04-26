# tests/parity/test_social_continuity.py
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState
from src.core.enums import EntityRole, Faction
from src.core.builder import V2EntityBuilder
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel
from src.core.updates import StateUpdate, EntityUpdate
from tests.parity.test_parity_rpg_recovery import create_test_profile

@pytest.mark.v2_contract
def test_grudge_accumulation():
    """Verifies that taking damage creates a grudge against the attacker."""
    hero = (V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).build())
    goblin = (V2EntityBuilder(2).at((6, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).build())
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    kernel = Kernel(profile, state, rng)
    
    # Hero reaches readiness at tick 11
    for _ in range(11): kernel.tick_once()
    
    # Tick 12: Hero attacks Goblin
    kernel.tick_once()
    
    g2 = kernel.state.entities[2]
    # Goblin should have a grudge against Hero
    # Damage was 5. Max HP was 112. Grudge impact ~0.044.
    assert g2.social.grudge_history.get(1, 0.0) > 0.04

@pytest.mark.v2_contract
def test_nemesis_panic():
    """Verifies that grudges bias appraisal toward fear/panic."""
    hero = (V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).build())
    # Goblin at 50% HP (Normally wouldn't flee)
    goblin = (V2EntityBuilder(2).at((6, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).build())
    # max_hp=22, so 11 HP is 50%
    goblin = replace(goblin, combat=replace(goblin.combat, hp=11))
    
    # Hero is a Nemesis! (High grudge)
    goblin = replace(goblin, social=replace(goblin.social, grudge_history={1: 1.0}))
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin})
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    kernel = Kernel(profile, state, rng)
    
    # Goblin reaches readiness at tick 11
    for _ in range(11): kernel.tick_once()
    
    g2 = kernel.state.entities[2]
    # Panic threshold is 0.4. Grudge bias (1.0 * 0.3 = 0.3) + baseline might push it.
    # Wait, 50% HP doesn't give much baseline panic.
    # But 1.0 grudge * 0.3 = 0.3. 
    # Appraisal also factors in threat ratio.
    assert g2.task.payload.get("reason") == "PANIC_RETREAT"
