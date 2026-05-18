import pytest
import sys
import os
from pathlib import Path

# Add project root to path so we can import legacy 'src'
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src_legacy.core.entities.entity_builder import EntityBuilder as LegacyBuilder
from src_legacy.core.models.enums import EntityRole as LegacyRole, Faction as LegacyFaction
from src_legacy.core.builder import V2EntityBuilder
from src_legacy.core.enums import EntityRole as V2Role, Faction as V2Faction

@pytest.mark.differential
def test_entity_builder_parity():
    """
    Differential parity test for Entity construction.
    Compares LegacyBuilder and V2EntityBuilder outcomes.
    """
    # 1. Setup - Mocking RNG if needed, but for basic construction we just compare values
    from src_legacy.platform.rng import DeterministicRNG
    rng = DeterministicRNG(42)
    
    # 2. Construction - Basic Hero
    legacy_hero = (LegacyBuilder(rng, 1)
                  .kind("hero")
                  .role(LegacyRole.HERO)
                  .at({"x": 10, "y": 20})
                  .with_base_stats(hp=150, atk=25, def_=10)
                  .build())
    
    v2_builder = (V2EntityBuilder(1)
                  .kind("hero")
                  .role(V2Role.HERO)
                  .at((10.0, 20.0))
                  .with_base_stats(hp=150, atk=25, def_stat=10))
    
    v2_hero = v2_builder.build()
    
    # 3. Assertions - Identity & Spatial
    assert v2_hero.id == legacy_hero.id
    assert v2_hero.kind == legacy_hero.kind
    assert v2_hero.position[0] == float(legacy_hero.spatial.pos.x)
    assert v2_hero.position[1] == float(legacy_hero.spatial.pos.y)
    
    # 4. Assertions - Combat
    assert v2_hero.combat.hp == legacy_hero.combat.hp
    assert v2_hero.combat.max_hp == legacy_hero.combat.max_hp
    assert v2_hero.combat.atk == legacy_hero.combat.atk_base
    assert v2_hero.combat.def_stat == legacy_hero.combat.def_base
    
    # 5. Immutability Check
    with pytest.raises(AttributeError): # Frozen dataclass raises AttributeError on assignment
        v2_hero.position = (0.0, 0.0)

@pytest.mark.differential
def test_entity_builder_role_mapping():
    """Verifies that legacy int roles map correctly to V2 Enums."""
    # HERO role is 0 in both
    v2_hero = V2EntityBuilder(2).role(0).build()
    assert v2_hero.identity.role == V2Role.HERO
    
    # MONSTER role was 2 in V2, but check if we can pass it directly
    v2_monster = V2EntityBuilder(3).role(V2Role.MONSTER).build()
@pytest.mark.v2_contract
def test_phase3_field_integration():
    """SOC-052: Verify Entity and IdentityAspect absorb new Phase 3 fields."""
    builder = (V2EntityBuilder(1)
               .group_id(101)
               .with_aptitudes(int=1.2, vit=0.8, str=2.0))
    
    entity = builder.build()
    
    assert entity.group_id == 101
    assert entity.aptitude.learning_rate == 1.2
    assert entity.aptitude.stamina_efficiency == 0.8
    assert entity.aptitude.str_apt == 2.0
