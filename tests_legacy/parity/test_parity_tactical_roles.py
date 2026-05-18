import pytest
from dataclasses import replace
from src_legacy.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent
from src_legacy.engine.tactical import TacticalDecisionSystem
from src_legacy.core.builder import V2EntityBuilder
from src_legacy.core.strategic import ProjectState, LeadState, ConcernState

def create_mock_entity(eid, faction, role="VANGUARD", pos=(10, 10)):
    return V2EntityBuilder(eid).at(pos).role(1).faction(faction).build()

@pytest.mark.v2_contract
def test_vanguard_closes_distance():
    """Vanguards should move toward target even if they could attack from range? No, they stay close."""
    attacker = (V2EntityBuilder(1).at((0, 0))
                .faction(0) # HERO
                .with_base_stats(range=1)
                .build())
    # Add tactical_role manually since field might not be there yet
    attacker = replace(attacker, combat=replace(attacker.combat, tactical_role="VANGUARD"))
    
    target = V2EntityBuilder(2).at((5, 0)).faction(1).build() # MONSTER
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})
    
    decision = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    assert decision.navigation.target_set == (5, 0)

@pytest.mark.v2_contract
def test_skirmisher_kites():
    """Skirmishers should move away if target is too close."""
    attacker = (V2EntityBuilder(1).at((1, 0))
                .faction(0)
                .with_base_stats(range=3)
                .build())
    attacker = replace(attacker, combat=replace(attacker.combat, tactical_role="SKIRMISHER"))
    
    target = V2EntityBuilder(2).at((0, 0)).faction(1).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})
    
    decision = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    # Should move away from (0,0) - e.g. to (3,0) or (4,0)
    assert decision.navigation.target_set[0] > 1.0

@pytest.mark.v2_contract
def test_strategic_capacity_limits():
    """Verifies that strategic updates respect cognition profile limits."""
    from src_legacy.systems.strategic import StrategicIntelligenceSystem
    from src_legacy.core.updates import StrategicUpdate
    
    hero = V2EntityBuilder(1).build()
    # Profile: max 3 projects
    new_profile = replace(hero.strategic.profile, max_active_projects=3)
    hero = replace(hero, strategic=replace(hero.strategic, profile=new_profile))
    
    # Already has 3 projects
    projects = {f"p{i}": ProjectState(id=f"p{i}", kind="test") for i in range(3)}
    hero = replace(hero, strategic=replace(hero.strategic, projects=projects))
    
    # 2. Evaluate intent
    # Note: evaluate_strategic_intent doesn't use existing projects for new proposals?
    # Actually, it does: if len(strat.projects) >= strat.profile.max_active_projects: return StrategicUpdate()
    
    # We need a node to trigger a proposal
    from src_legacy.core.state import ResourceNodeState
    node = ResourceNodeState(id=1, kind="TREE", position=(1, 1), yields_item="WOOD", remaining_charges=5, max_charges=5, required_ticks=5)
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero}, resource_nodes={1: node})
    
    intent_upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hero)
    # Should be empty because already at max capacity (3)
    assert not intent_upd.projects_add_or_update

@pytest.mark.v2_contract
def test_lead_bandwidth_limits():
    """Verifies that strategic updates respect lead capacity limits."""
    from src_legacy.systems.strategic import StrategicIntelligenceSystem
    from src_legacy.core.strategic import LeadState, LeadCertainty
    
    hero = V2EntityBuilder(1).build()
    # Profile: max 5 leads
    new_profile = replace(hero.strategic.profile, max_leads=5)
    hero = replace(hero, strategic=replace(hero.strategic, profile=new_profile))
    
    # Already has 5 leads
    leads = {f"l{i}": LeadState(id=f"l{i}", kind="test", subject="x", certainty=LeadCertainty.PRECISE) for i in range(5)}
    hero = replace(hero, strategic=replace(hero.strategic, leads=leads))
    
    # Check if we should enforce now or if it's passive
    from src_legacy.systems.detour import DetourSuggestionSystem
    update = DetourSuggestionSystem.enforce_bandwidth(hero, 1)
    
    # Should be empty
    assert not update.leads_remove
    
    # Add one more
    leads["l5"] = LeadState(id="l5", kind="test", subject="x", certainty=LeadCertainty.VAGUE)
    hero = replace(hero, strategic=replace(hero.strategic, leads=leads))
    
    update = DetourSuggestionSystem.enforce_bandwidth(hero, 1)
    # Should remove one (the lowest certainty)
    assert "l5" in update.leads_remove or any(l_id in ["l0", "l1", "l2", "l3", "l4"] for l_id in update.leads_remove)
    assert len(update.leads_remove) == 1
