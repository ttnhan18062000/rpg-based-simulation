import pytest
from src.core.entities.entity_builder import EntityBuilder
from src.platform.rng import DeterministicRNG
from src.core.models.enums import Faction, EntityRole, TraitType, HeroClass

def test_entity_to_full_schema_no_crash():
    rng = DeterministicRNG(42)
    eb = EntityBuilder(rng, 1, 0)
    eb.kind("hero")
    eb.with_identity(display_name="Test Hero")
    eb.faction(Faction.HERO_GUILD)
    eb.role(EntityRole.HERO)
    eb.with_traits(trait_ids=[TraitType.ELEMENTALIST, TraitType.ARCANE_GIFTED])
    eb.with_base_stats(level=5)
    eb.with_hero_class(HeroClass.WARRIOR)
    
    entity = eb.build()
    
    # This should not crash
    schema = entity.to_full_schema()
    
    assert schema.id == 1
    assert schema.display_name == "Test Hero"
    assert schema.fire_dmg_mult == 1.2  # Base 1.0 + ELEMENTALIST 0.2
    assert schema.dark_dmg_mult == 1.2   # Base 1.0 + ARCANE_GIFTED 0.2
    assert schema.hero_class == "warrior"
    assert schema.progression.level == 5

def test_entity_to_full_schema_minimal():
    rng = DeterministicRNG(42)
    eb = EntityBuilder(rng, 2, 0)
    eb.kind("mob")
    entity = eb.build()
    
    # Minimal entity should also not crash
    schema = entity.to_full_schema()
    assert schema.id == 2
    assert schema.hero_class == "none"

if __name__ == "__main__":
    pytest.main([__file__])
