import pytest
from dataclasses import replace
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, EntityRole, Faction, GroupRecord
from src.engine.tactical import TacticalDecisionSystem
from src.core.enums import ActionStyle

@pytest.mark.v2_contract
def test_cover_seeking_logic():
    """Verifies that wounded skirmishers seek cover against ranged threats."""
    # 1. Setup: Skirmisher Hero vs Ranged Goblin
    hero = (V2EntityBuilder(1)
            .at((5, 5))
            .faction(Faction.HERO_GUILD)
            .with_base_stats(hp=20, tactical_role="SKIRMISHER") # Wounded
            .build())
    
    goblin = (V2EntityBuilder(2)
              .at((15, 5))
              .with_base_stats(range=10) # Ranged
              .role(EntityRole.MONSTER)
              .faction(Faction.MONSTER_HORDE)
              .build())
    
    # Wall at (10, 5) and (10, 4) and (10, 6)
    terrain = {(10, 5): "WALL", (10, 4): "WALL", (10, 6): "WALL"}
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin}, terrain=terrain)
    
    # Hero should see goblin and seek cover
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
    
    assert update.task is not None
    assert update.task.payload_set["reason"] == "SEEK_COVER"
    target_pos = update.navigation.target_set
    # Target pos should have no LoS to (15, 5)
    from src.engine.legality import LegalityServiceV2
    assert not LegalityServiceV2.has_line_of_sight(target_pos, (15, 5), state)

@pytest.mark.v2_contract
def test_bracketing_logic():
    """Verifies that vanguards in a group bracket their target."""
    # Target at (10, 10)
    target = V2EntityBuilder(3).at((10, 10)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).build()
    
    # Ally 1 at (9, 10) - already adjacent, targeting Target
    ally1 = (V2EntityBuilder(1)
             .at((9, 10))
             .group_id(1)
             .faction(Faction.HERO_GUILD)
             .with_base_stats(tactical_role="VANGUARD")
             .build())
    # Set its intent
    ally1 = replace(ally1, task=replace(ally1.task, work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 3}))
    
    # Hero (Ally 2) at (10, 8) - approaching
    hero = (V2EntityBuilder(2)
            .at((10, 8))
            .group_id(1)
            .faction(Faction.HERO_GUILD)
            .with_base_stats(tactical_role="VANGUARD")
            .build())
    
    group = GroupRecord(id=1, leader_id=1, member_ids={1, 2}, anchor=(10, 10))
    state = AuthoritativeState(tick=1, seed=42, entities={1: ally1, 2: hero, 3: target}, groups={1: group})
    
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
    
    assert update.task is not None
    # Hero should try to move to opposite side of Ally 1 (which is (11, 10) if Ally 1 is at (9, 10))
    assert update.task.payload_set["reason"] == "BRACKETING"
    assert update.navigation.target_set == (11.0, 10.0)

@pytest.mark.v2_contract
def test_anti_stalemate_oscillation():
    """Verifies that anti-stalemate detects oscillation."""
    hero = V2EntityBuilder(1).at((5, 5)).faction(Faction.HERO_GUILD).build()
    # Payload with oscillation: (5,5) -> (5,6) -> (5,5)
    hero = replace(hero, task=replace(hero.task, payload={"stale_ticks": 2, "recent_positions": [(5, 5), (5, 6), (5, 5)]}))
    
    target = V2EntityBuilder(2).at((10, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: target})
    
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
    
    assert update.task is not None
    # stale_ticks should be incremented + 5 (oscillation penalty)
    assert update.task.payload_set["stale_ticks"] >= 7

@pytest.mark.v2_contract
def test_action_style_bias():
    """Verifies that Aggressive style attacks from further away."""
    # Balanced Hero at (8, 5) targeting (10, 5) - Range 1. Dist is 2. Too far.
    hero_bal = (V2EntityBuilder(1)
                .at((8, 5))
                .faction(Faction.HERO_GUILD)
                .with_base_stats(range=1, action_style=0) # BALANCED
                .build())
    
    # Aggressive Hero at (8, 5) targeting (10, 5) - Range 1. Dist is 2. 
    # Aggressive style should ATTACK if dist <= range + 1.
    hero_agg = (V2EntityBuilder(2)
                .at((8, 5))
                .faction(Faction.HERO_GUILD)
                .with_base_stats(range=1, action_style=1) # AGGRESSIVE
                .build())
    
    target = V2EntityBuilder(3).at((10, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero_bal, 2: hero_agg, 3: target})
    
    upd_bal = TacticalDecisionSystem.evaluate_entity_intent(state, hero_bal)
    upd_agg = TacticalDecisionSystem.evaluate_entity_intent(state, hero_agg)
    
    assert upd_bal.task is not None
    assert upd_agg.task is not None
    
    # Balanced should PURSUE (move to (10, 5))
    assert upd_bal.task.work_kind_set == "ENTITY_MOVE"
    
    assert upd_agg.task.work_kind_set == "ENTITY_ACT"
    assert upd_agg.task.payload_set["action"] == "ATTACK"

@pytest.mark.v2_contract
def test_low_hp_retreat():
    """Verifies that critically wounded entities retreat to origin."""
    hero = (V2EntityBuilder(1)
            .at((10, 10))
            .faction(Faction.HERO_GUILD)
            .build())
    # Force low HP
    hero = replace(hero, combat=replace(hero.combat, hp=2)) # 2/22 HP < 15%
    
    goblin = V2EntityBuilder(2).at((11, 10)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin})
    
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
    
    assert update.task is not None
    assert update.task.payload_set["reason"] == "PANIC_RETREAT"
    assert update.navigation.target_set == (0.0, 0.0)

@pytest.mark.v2_contract
def test_evasive_style_kiting():
    """Verifies that Evasive style kites further than Balanced."""
    # Balanced Hero at (8, 5) targeting (10, 5) - Dist 2. Range 10.
    hero_bal = (V2EntityBuilder(1)
                .at((8, 5))
                .faction(Faction.HERO_GUILD)
                .with_base_stats(range=10, tactical_role="SKIRMISHER", action_style=0)
                .build())
    
    # Evasive Hero at (8, 5) targeting (10, 5)
    hero_eva = (V2EntityBuilder(2)
                .at((8, 5))
                .faction(Faction.HERO_GUILD)
                .with_base_stats(range=10, tactical_role="SKIRMISHER", action_style=2) # EVASIVE
                .build())
    
    target = V2EntityBuilder(3).at((10, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero_bal, 2: hero_eva, 3: target})
    
    upd_bal = TacticalDecisionSystem.evaluate_entity_intent(state, hero_bal)
    upd_eva = TacticalDecisionSystem.evaluate_entity_intent(state, hero_eva)
    
    # Balanced: dx = -2. kite_dist = 4. kite_pos = (8 + (-2*4), 5) = (0, 5)
    # Evasive: dx = -2. kite_dist = 6. kite_pos = (8 + (-2*6), 5) = (-4, 5)
    
    assert upd_bal.navigation.target_set == (0.0, 5.0)
    assert upd_eva.navigation.target_set == (-4.0, 5.0)

@pytest.mark.v2_contract
def test_chokepoint_holding():
    """Verifies that vanguards hold chokepoints instead of pursuing."""
    # Hero at (10, 10). Target at (10, 14).
    # Walls at (9, 10) and (11, 10). This makes (10, 10) a chokepoint.
    hero = (V2EntityBuilder(1)
            .at((10, 10))
            .faction(Faction.HERO_GUILD)
            .with_base_stats(tactical_role="VANGUARD", range=1)
            .build())
    
    target = (V2EntityBuilder(2)
              .at((10, 14))
              .role(EntityRole.MONSTER)
              .faction(Faction.MONSTER_HORDE)
              .build())
    
    terrain = {(9, 10): "WALL", (11, 10): "WALL"}
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: target}, terrain=terrain)
    
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
    
    assert update.task is not None
    assert update.task.payload_set["action"] == "HOLD"
    assert update.task.payload_set["reason"] == "HOLD_CHOKEPOINT"
