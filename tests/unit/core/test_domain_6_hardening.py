import pytest
from src.core.state import AttributeComponent, IdentityComponent, CombatComponent, EquipmentComponent
from src.progression.leveling import LevelingService
from src.engine.rpg_depth import SkillScalingService
from src.engine.apply import ApplyPath
from src.core.updates import EntityUpdate, IdentityUpdate

def test_role_hysteresis():
    """Verify that roles don't flicker unless the lead is significant (>5)."""
    # Base attributes: Str=10, Agi=11, Vit=10 -> Current role is SKIRMISHER (Agi lead by 1)
    attrs = AttributeComponent(strength=10, agility=11, vitality=10)
    
    # 1. Start as SKIRMISHER
    stats = LevelingService.recalculate_combat_stats(attrs, current_role="SKIRMISHER")
    assert stats["tactical_role"] == "SKIRMISHER"
    
    # 2. Increase Strength to 15 (Lead over Agi is 4)
    # Difference is 15 - 11 = 4. Hysteresis requires > 5 to switch.
    attrs_v2 = AttributeComponent(strength=15, agility=11, vitality=10)
    stats_v2 = LevelingService.recalculate_combat_stats(attrs_v2, current_role="SKIRMISHER")
    assert stats_v2["tactical_role"] == "SKIRMISHER", "Should NOT switch to VANGUARD yet (diff=4)"
    
    # 3. Increase Strength to 17 (Lead over Agi is 6)
    # Difference is 17 - 11 = 6. Should switch.
    attrs_v3 = AttributeComponent(strength=17, agility=11, vitality=10)
    stats_v3 = LevelingService.recalculate_combat_stats(attrs_v3, current_role="SKIRMISHER")
    assert stats_v3["tactical_role"] == "VANGUARD", "Should switch to VANGUARD (diff=6)"

def test_trait_composition():
    """Verify that traits correctly modify effective stats."""
    attrs = AttributeComponent(strength=10, agility=10, vitality=10)
    
    # Base stats (No traits)
    stats_base = SkillScalingService.get_effective_stats(attrs)
    base_hp = stats_base["max_hp"]
    base_atk = stats_base["atk"]
    base_eva = stats_base["evasion"]
    
    # With traits
    traits = {"Tough", "Strong", "Quick"}
    stats_traits = SkillScalingService.get_effective_stats(attrs, traits=traits)
    
    assert stats_traits["max_hp"] == base_hp + 20
    assert stats_traits["atk"] == base_atk + 3
    assert stats_traits["evasion"] == pytest.approx(base_eva + 0.02)

def test_apply_path_derived_propagation():
    """Verify that ApplyPath correctly propagates derived tactical_role."""
    from src.core.state import AuthoritativeState
    from src.core.enums import Faction, EntityRole
    from src.core.builder import V2EntityBuilder
    # Setup entity: Agi=10, Str=10 -> Role=VANGUARD
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .location(0, 0)
              .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
              .attributes(strength=10, agility=10, vitality=10)
              .combat(hp=100, max_hp=100)
              .build())
    # Note: V2EntityBuilder initializes tactical_role based on attributes.
    # At 10/10/10 it should be VANGUARD.
    
    from src.core.updates import EntityUpdate, AttributeUpdate
    # Update Agi by +10 -> 10 + 10 = 20. Should trigger role shift to SKIRMISHER
    # (Diff = 20 - 10 = 10, which is > 5)
    upd = EntityUpdate(
        entity_id=1,
        attributes=AttributeUpdate(agility_delta=10)
    )
    
    # We need to set the attributes explicitly in the update to trigger the dirty flag
    # Actually, in ApplyPath, if update.attributes is not None, it uses replace().
    
    from src.core.updates import StateUpdate
    state_upd = StateUpdate(entity_updates={1: upd})
    
    from src.engine.apply import ApplyPath
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    
    new_entity = new_state.entities[1]
    assert new_entity.attributes.agility == 20
    assert new_entity.combat.tactical_role == "SKIRMISHER", "Role should have been updated via derived stats gate"

def test_apply_path_trait_updates():
    """Verify that trait updates are correctly applied and reflected in stats."""
    from src.core.state import AuthoritativeState
    from src.core.enums import Faction, EntityRole
    from src.core.updates import StateUpdate
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .location(0, 0)
              .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
              .attributes(strength=10, agility=10, vitality=10)
              .combat(hp=100, max_hp=100)
              .build())
    
    # Add "Tough" trait
    upd = EntityUpdate(
        entity_id=1,
        identity=IdentityUpdate(traits_add=["Tough"])
    )
    state_upd = StateUpdate(entity_updates={1: upd})
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    new_state = ApplyPath.apply_generation(state, state_upd)
    
    new_entity = new_state.entities[1]
    assert "Tough" in new_entity.identity.traits
    assert new_entity.combat.max_hp == 142, "Max HP should have increased to 142 due to Tough trait"
    
    # Remove "Tough" trait
    upd_rem = EntityUpdate(
        entity_id=1,
        identity=IdentityUpdate(traits_remove=["Tough"])
    )
    state_upd_rem = StateUpdate(entity_updates={1: upd_rem})
    new_state_rem = ApplyPath.apply_generation(new_state, state_upd_rem)
    new_entity_rem = new_state_rem.entities[1]
    assert "Tough" not in new_entity_rem.identity.traits
    assert new_entity_rem.combat.max_hp == 122, "Max HP should have reverted to 122"

if __name__ == "__main__":
    pytest.main([__file__])
