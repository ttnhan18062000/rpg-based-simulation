from dataclasses import replace
import pytest
from src.core.state import (
    EntityState, AuthoritativeState, InventoryComponent, ItemStack,
    CombatComponent, NavigationComponent, IntentResult, StrategicComponent
)
from src.core.strategic import (
    ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus, BlockerState, LeadState, LeadCertainty
)
from src.systems.strategic import StrategicIntelligenceSystem
from src.systems.routine import RoutineService
from src.systems.strategic_systems.detour import DetourSuggestionSystem
from src.core.builder import V2EntityBuilder

@pytest.fixture
def base_state():
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .location(100, 100)
              .replace_inventory(InventoryComponent(max_slots=2, items=[]))
              .build())
    return AuthoritativeState(
        tick=1000,
        seed=42,
        entities={1: entity},
        resource_nodes={}
    )

def test_inventory_full_to_town_detour(base_state):
    entity = base_state.entities[1]
    # 1. Simulate Inventory Full rejection
    entity = replace(entity, inventory=replace(entity.inventory, items=[ItemStack("wood", 1), ItemStack("wood", 1)]))
    
    # Simulate a rejected intent in latest_intent_results
    entity = replace(entity, identity=replace(entity.identity, latest_intent_results=[
        IntentResult(transaction_id="t1", accepted=False, reason="INVENTORY_FULL", source_kind="NODE", source_id=101)
    ]))
    
    # 2. Infer Blocker
    upd = StrategicIntelligenceSystem.infer_blockers(
        entity, 
        last_task="ENTITY_ACT", 
        last_payload={"action": "INTERACT", "target_id": 101},
        current_project=ProjectState(id="p1", kind="harvesting")
    )
    
    assert len(upd.blockers_add_or_update) == 1
    blocker = upd.blockers_add_or_update[0]
    assert blocker.kind == "inventory"
    assert blocker.subject == "capacity"
    
    # Apply blocker to entity for detour test
    entity = replace(entity, strategic=replace(entity.strategic, blockers={blocker.id: blocker}))
    
    # 3. Add a lead for town
    town_lead = LeadState(id="lead_town", kind="location", subject="town", detail="Town Center", certainty=LeadCertainty.PRECISE)
    entity = replace(entity, strategic=replace(entity.strategic, leads={town_lead.id: town_lead}, blockers=entity.strategic.blockers))
    
    # 4. Suggest Detour
    suggestions = DetourSuggestionSystem.suggest_detours(entity, base_state.tick)
    assert len(suggestions) > 0
    best = suggestions[0]
    assert best.objective_kind == "reach_location"
    assert best.target == "Town Center"

def test_low_hp_retreat_detour(base_state):
    entity = base_state.entities[1]
    # 1. Set Low HP
    entity = replace(entity, combat=replace(entity.combat, hp=10))
    
    # 2. Evaluate Concerns
    concerns = RoutineService.evaluate_biological_needs(entity, base_state.world_time)
    assert any(c.kind == "danger" for c in concerns)
    
    # Add danger blocker manually to trigger detour (usually inferred from combat failure or high concern)
    danger_blocker = BlockerState(id="blocker_low_hp", kind="danger", subject="safety", severity=0.9)
    entity = replace(entity, strategic=replace(entity.strategic, blockers={danger_blocker.id: danger_blocker}))
    
    # 3. Add a lead for safe zone
    safe_lead = LeadState(id="lead_safe", kind="location", subject="safe_zone", detail="Origin", certainty=LeadCertainty.PRECISE)
    entity = replace(entity, strategic=replace(entity.strategic, leads={safe_lead.id: safe_lead}, blockers=entity.strategic.blockers))
    
    # 4. Suggest Detour
    suggestions = DetourSuggestionSystem.suggest_detours(entity, base_state.tick)
    assert len(suggestions) > 0
    best = suggestions[0]
    assert best.objective_kind == "reach_location"
    assert best.target == "Origin"

def test_strategic_learning_bias(base_state):
    entity = base_state.entities[1]
    
    # 1. Process a Victory
    proj = ProjectState(id="p1", kind="combat", score=20.0)
    entity = replace(entity, strategic=replace(entity.strategic, projects={proj.id: proj}))
    
    upd = StrategicIntelligenceSystem.process_project_outcome(
        entity, proj.id, ProjectStatus.COMPLETED, base_state.tick
    )
    
    assert len(upd.turning_points_add) == 1
    tp = upd.turning_points_add[0]
    assert tp.kind == "great_victory" # score 20.0 > 15.0
    assert upd.boredom_delta["combat"] == -2.0
    
    # 2. Apply and Verify Bias
    entity = replace(entity, strategic=replace(entity.strategic,
        turning_points=upd.turning_points_add,
        boredom={"combat": -2.0}
    ))
    
    from src.ai.score_modifiers import ScoreModifierSystem
    from src.ai.goals.base import GoalScore
    
    scores = [GoalScore(kind="combat", utility=50.0, target_id=101)]
    modified = ScoreModifierSystem.apply_modifiers(entity, base_state, scores)
    
    # utility = 50.0 - (-2.0 * 0.5) + (0.6 * 10.0) = 50.0 + 1.0 + 6.0 = 57.0
    assert modified[0].utility > 50.0

def test_lead_suppression_and_exhaustion(base_state):
    entity = base_state.entities[1]
    
    # 1. Lead fails once
    lead = LeadState(id="lead_1", kind="location", subject="resource", tested=True, test_outcome="FAILURE", failure_count=0)
    entity = replace(entity, strategic=replace(entity.strategic, leads={lead.id: lead}))
    
    upd = DetourSuggestionSystem.suppress_exhausted_leads(entity, base_state.tick)
    assert len(upd.leads_add_or_update) == 1
    u_lead = upd.leads_add_or_update[0]
    assert u_lead.suppression_until_tick == base_state.tick + 500
    assert u_lead.failure_count == 1
    
    # 2. Lead fails 3 times -> EXHAUSTED
    lead_3 = replace(u_lead, failure_count=2)
    entity = replace(entity, strategic=replace(entity.strategic, leads={lead_3.id: lead_3}))
    
    upd_3 = DetourSuggestionSystem.suppress_exhausted_leads(entity, base_state.tick)
    assert upd_3.leads_add_or_update[0].certainty == LeadCertainty.EXHAUSTED
