"""
P1 Semantic Hardening Tests.
- RPG-0058: social_party_cooperation
- RPG-0060: biological_needs_routines
- RPG-0068: target_stickiness_bias
- RPG-0041: project_interruption_resistance
- RPG-0046: strategic_detour_suggestion
- RPG-1400, RPG-1401, RPG-1402: strategic_retention
- RPG-1411: blocker_resolution
- RPG-1436: lead_suppression
- RPG-1425: detour_breadth
- RPG-0022, RPG-0023, RPG-0024, RPG-0026, RPG-0115: tactical_laws
- RPG-0033, RPG-0036, RPG-0037, RPG-0038: town_laws
- RPG-0178, RPG-0182, RPG-0183, RPG-0190, RPG-0192, RPG-0193: strategic_laws
- RPG-0441, RPG-0444: combat_stamina_laws
- RPG-1245, RPG-1246, RPG-1247, RPG-1248, RPG-1249, RPG-1250: movement_modes
- RPG-0025, RPG-0138: movement_laws
"""
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, GroupRecord, EntityState, IdentityComponent, CombatComponent, StrategicComponent, InventoryComponent, SocialComponent, TaskComponent, InteractionComponent, IntentResult
from src.core.enums import EntityRole, ActionStyle
from src.core.strategic import ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus, BlockerState, LeadState, LeadCertainty, DirectiveKind
from src.engine.tactical import TacticalDecisionSystem
from src.systems.strategic import StrategicIntelligenceSystem

from src.core.builder import V2EntityBuilder

def create_mock_entity(id, pos=(0.0, 0.0), hp=100, faction="HERO_FACTION"):
    from src.core.enums import Faction
    f_enum = Faction.HERO_GUILD if faction == "HERO_FACTION" else Faction.MONSTER_HORDE
    return (V2EntityBuilder(id)
        .kind("ACTOR")
        .location(*pos)
        .identity(role=EntityRole.HERO, faction=f_enum)
        .combat(hp=hp, max_hp=100, atk=10, attack_range=1, tactical_role="VANGUARD", readiness=100.0)
        .inventory(max_slots=10)
        .build())

def test_party_agency_panic_override():
    """
    Law: Injured members override leadership shared target with personal survival.
    Requirement 9: injured member overrides and retreats.
    """
    # Leader (Hero 1) is healthy and targeting Monster 99
    h1 = create_mock_entity(1, pos=(0,0))
    h1 = replace(h1, task=replace(h1.task, work_kind="ENTITY_ACT", payload={"target_id": 99}))
    
    # Member (Hero 2) is dying and near Monster 99
    h2 = create_mock_entity(2, pos=(1,1), hp=10) # 10% HP
    
    m99 = create_mock_entity(99, pos=(0,1), faction="MONSTER_FACTION")
    
    # Add anchor to GroupRecord
    group = GroupRecord(id=100, leader_id=1, member_ids={1, 2}, anchor=(0,0), shared_target_id=99)
    
    state = AuthoritativeState(tick=1, seed=1, entities={1: h1, 2: h2, 99: m99}, groups={100: group})
    
    # Evaluate Hero 2
    update = TacticalDecisionSystem.evaluate_entity_intent(state, h2)
    
    # Should be fleeing/retreating, NOT attacking 99
    assert update.task.work_kind_set == "ENTITY_MOVE"
    assert update.task.payload_set["reason"] == "PANIC_RETREAT"

def test_party_agency_trust_bias():
    """
    Law: Disobedient (low trust) members are less likely to follow leadership shared target.
    Requirement 9: low-trust member weakens obedience.
    """
    # Hero 1 is leader, targeting Monster 99
    h1 = create_mock_entity(1, pos=(0,0))
    
    # Hero 2 is member, hates Hero 1
    h2 = create_mock_entity(2, pos=(2,2))
    h2 = replace(h2, social=replace(h2.social, trust_history={1: -1.0}))
    
    # Two potential targets
    m99 = create_mock_entity(99, pos=(0,1), faction="MONSTER_FACTION") # Shared target
    m98 = create_mock_entity(98, pos=(2,1), faction="MONSTER_FACTION") # Closer to h2
    
    group = GroupRecord(id=100, leader_id=1, member_ids={1, 2}, anchor=(0,0), shared_target_id=99)
    
    state = AuthoritativeState(tick=1, seed=1, entities={1: h1, 2: h2, 98: m98, 99: m99}, groups={100: group})
    
    # Evaluate Hero 2
    update = TacticalDecisionSystem.evaluate_entity_intent(state, h2)
    
    # Target 98 should be chosen because it's closer and 99 has trust penalty
    assert update.task.payload_set["target_id"] == 98

def test_strategic_interruption_hp():
    """
    Requirement 10: low HP interrupts harvesting project.
    """
    h1 = create_mock_entity(1, pos=(0,0), hp=30) # 30% HP
    project = ProjectState(id="p1", kind="harvesting", status=ProjectStatus.ACTIVE)
    h1 = replace(h1, strategic=replace(h1.strategic, current_project_id="p1", projects={"p1": project}))
    
    m99 = create_mock_entity(99, pos=(5,5), faction="MONSTER_FACTION")
    # Skirmisher monster will trigger cover seeking/retreat
    m99 = replace(m99, combat=replace(m99.combat, tactical_role="SKIRMISHER", range=5))
    
    state = AuthoritativeState(tick=1, seed=1, entities={1: h1, 99: m99})
    
    # Evaluate Hero 1
    update = TacticalDecisionSystem.evaluate_entity_intent(state, h1)
    
    # Should suspend project
    assert update.strategic is not None
    assert update.strategic.projects_add_or_update[0].status == ProjectStatus.SUSPENDED
    
    # Should be moving (either seeking cover, retreating, or pursuing)
    assert update.task.work_kind_set == "ENTITY_MOVE"

def test_strategic_inventory_detour():
    """
    Requirement 10: full inventory creates town/sell/storage detour.
    """
    h1 = create_mock_entity(1)
    h1 = replace(h1, inventory=replace(h1.inventory, items=["iron_ore"] * 10)) # Full
    
    # Add a lead for town
    town_lead = LeadState(id="town_info", kind="location", subject="town", detail="(10, 10)", certainty=LeadCertainty.PRECISE)
    h1 = replace(h1, strategic=replace(h1.strategic, leads={"town_info": town_lead}))
    
    # Simulate a harvesting failure due to full inventory
    h1 = replace(h1, identity=replace(h1.identity, latest_intent_results=[IntentResult(transaction_id="t1", accepted=False, reason="INVENTORY_FULL", source_kind="NODE", source_id=50)]))
    
    # Infer blockers
    upd = StrategicIntelligenceSystem.infer_blockers(h1, "ENTITY_ACT", {"action": "INTERACT", "target_id": 50})
    
    # Set current project (e.g. harvesting) so detour logic triggers
    proj = ProjectState(id="p_harvest", kind="harvesting", status=ProjectStatus.ACTIVE)
    h1 = replace(h1, strategic=replace(h1.strategic, 
        current_project_id="p_harvest",
        projects={"p_harvest": proj},
        blockers={b.id: b for b in upd.blockers_add_or_update}
    ))
    
    assert "blocker_inventory_full" in h1.strategic.blockers
    
    # Evaluate strategic intent
    state = AuthoritativeState(tick=9, seed=1, entities={1: h1})
    strat_upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state, h1)
    
    # Should suggest and switch to a detour project to town
    detour = next((p for p in strat_upd.projects_add_or_update if p.kind == "detour"), None)
    assert detour is not None
    assert detour.objectives[0].target == "(10, 10)"
    assert strat_upd.current_project_id_set == detour.id

def test_strategic_reward_pending_detour():
    """
    Requirement 10: reward pending creates free-inventory detour.
    """
    from src.core.quests import QuestState, QuestStatus
    q1 = QuestState(id="q1", kind="quest", quest_status=QuestStatus.REWARD_PENDING, score=100.0, status=ProjectStatus.ACTIVE)
    h1 = create_mock_entity(1)
    # MUST set current_project_id
    h1 = replace(h1, strategic=replace(h1.strategic, current_project_id="q1", projects={"q1": q1}))
    
    # Add town lead
    town_lead = LeadState(id="town_info", kind="location", subject="town", detail="(10, 10)", certainty=LeadCertainty.PRECISE)
    h1 = replace(h1, strategic=replace(h1.strategic, leads={"town_info": town_lead}))
    
    # We need a blocker for reward_pending
    blocker = BlockerState(id="blocker_reward_pending", kind="inventory", subject="capacity", severity=1.0)
    h1 = replace(h1, strategic=replace(h1.strategic, blockers={blocker.id: blocker}))
    
    state = AuthoritativeState(tick=9, seed=1, entities={1: h1})
    strat_upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state, h1)
    
    detour = next((p for p in strat_upd.projects_add_or_update if p.kind == "detour"), None)
    assert detour is not None
    assert detour.objectives[0].target == "(10, 10)"

def test_strategic_lead_suppression():
    """
    RPG-1436: Rejected/tested leads are suppressed to avoid blind retries.
    """
    h1 = create_mock_entity(1)
    # Failed lead
    lead = LeadState(id="bad_lead", kind="location", subject="town", tested=True, test_outcome="FAILURE", failure_count=1)
    h1 = replace(h1, strategic=replace(h1.strategic, leads={"bad_lead": lead}))
    
    # Blocker that matches the lead
    blocker = BlockerState(id="b1", kind="inventory", subject="capacity", severity=1.0)
    h1 = replace(h1, strategic=replace(h1.strategic, blockers={"b1": blocker}))
    
    from src.systems.strategic_systems.detour import DetourSuggestionSystem
    # Suppress leads
    upd = DetourSuggestionSystem.suppress_exhausted_leads(h1, current_tick=100)
    h1 = replace(h1, strategic=replace(h1.strategic, leads={l.id: l for l in upd.leads_add_or_update}))
    
    assert h1.strategic.leads["bad_lead"].suppression_until_tick == 600 # 100 + 500
    
    # Suggest detours
    detours = DetourSuggestionSystem.suggest_detours(h1, current_tick=100)
    # Should be empty because bad_lead is suppressed
    assert len(detours) == 0
    
    # After tick 600, it should be usable again
    detours_future = DetourSuggestionSystem.suggest_detours(h1, current_tick=601)
    assert len(detours_future) == 1

def test_strategic_detour_breadth():
    """
    RPG-1425: Detour breadth obeys cognition profile capacity.
    """
    h1 = create_mock_entity(1)
    # 5 leads for town
    leads = {f"town_{i}": LeadState(id=f"town_{i}", kind="location", subject="town", detail=f"pos_{i}", certainty=LeadCertainty.PRECISE) for i in range(5)}
    h1 = replace(h1, strategic=replace(h1.strategic, leads=leads))
    
    # Blocker
    blocker = BlockerState(id="b1", kind="inventory", subject="capacity", severity=1.0)
    h1 = replace(h1, strategic=replace(h1.strategic, blockers={"b1": blocker}))
    
    from src.systems.strategic_systems.detour import DetourSuggestionSystem
    detours = DetourSuggestionSystem.suggest_detours(h1, current_tick=100)
    
    # Default breadth is 3
    assert len(detours) == 3

def test_wound_infliction():
    """
    RPG-0441: Massive hit (>25% max HP) inflicts a wound.
    RPG-0442: Wound persistence through updates.
    RPG-0445: Wound penalty application (trace verified).
    """
    h1 = create_mock_entity(1)
    m1 = create_mock_entity(2, faction="MONSTER_FACTION")
    
    # Force massive damage by boosting attacker ATK
    h1 = replace(h1, combat=replace(h1.combat, atk=100))
    state = AuthoritativeState(tick=1, seed=1, entities={1: h1, 2: m1})
    
    from src.engine.combat import CombatResolutionSystem
    combat_up = CombatResolutionSystem.resolve_attack(h1, m1, state)
    
    assert combat_up.wound_update is not None
    assert len(combat_up.wound_update.wounds_add) == 1
    assert combat_up.wound_update.wounds_add[0].severity > 0.25
    assert any("WOUND_INFLICTED" in t for t in combat_up.trace)

def test_stamina_drain():
    """RPG-0444: Attack drains stamina."""
    h1 = create_mock_entity(1)
    m1 = create_mock_entity(2, faction="MONSTER_FACTION")
    state = AuthoritativeState(tick=1, seed=1, entities={1: h1, 2: m1})
    
    from src.engine.domain_logic import SimulationDomainLogic
    from src.core.state import TaskComponent

    payload = {"action": "ATTACK", "target_id": 2}
    h1 = replace(h1, task=TaskComponent(work_kind="ENTITY_ACT", payload=payload))
    
    updates = SimulationDomainLogic.execute_action(h1, payload, 1, context=state)
    attacker_up = updates[1]
    
    assert attacker_up.stamina_update.current_delta == -5.0

def test_social_contract_transitions():
    """
    RPG-0182: Contract transitions follow strict state machine.
    RPG-1450: Contract offer has status.
    RPG-1455: Accepted contract creates explicit obligation/contract state.
    """
    from src.systems.social_contract import SocialContractSystem
    from src.core.strategic import ContractState, ContractStatus, ContractKind
    
    h1 = create_mock_entity(1)
    contract = ContractState(id="c1", kind=ContractKind.RECRUITMENT, source_id=1, target_id=2, status=ContractStatus.OFFERED)
    h1 = replace(h1, strategic=replace(h1.strategic, contracts={"c1": contract}))
    
    # 1. Valid: OFFERED -> ACCEPTED
    upd, _ = SocialContractSystem.transition_contract(h1, "c1", ContractStatus.ACCEPTED, tick=10)
    assert upd.contracts_add_or_update[0].status == ContractStatus.ACCEPTED
    
    # 2. Invalid: FULFILLED -> ACTIVE (Terminal)
    contract_fulfilled = replace(contract, status=ContractStatus.FULFILLED)
    h1_fulfilled = replace(h1, strategic=replace(h1.strategic, contracts={"c1": contract_fulfilled}))
    upd_invalid, _ = SocialContractSystem.transition_contract(h1_fulfilled, "c1", ContractStatus.ACTIVE, tick=10)
    assert len(upd_invalid.contracts_add_or_update) == 0 # Rejected
    
    # 3. Valid: ACTIVE -> BETRAYED
    contract_active = replace(contract, status=ContractStatus.ACTIVE)
    h1_active = replace(h1, strategic=replace(h1.strategic, contracts={"c1": contract_active}))
    upd_betrayal, _ = SocialContractSystem.transition_contract(h1_active, "c1", ContractStatus.BETRAYED, tick=10)
    assert upd_betrayal.contracts_add_or_update[0].status == ContractStatus.BETRAYED

def test_contract_outcome_consequences():
    """
    RPG-1461: Contract outcome can affect private bonds.
    RPG-1460: Contract outcome can affect public reputation.
    RPG-1463: Contract outcome can affect strategic directives.
    RPG-0304: Contract outcome consequences.
    """
    from src.systems.social_systems.contracts import ContractService
    from src.core.strategic import ContractState, ContractStatus, ContractKind
    
    h1 = create_mock_entity(1)
    contract = ContractState(
        id="c1", kind=ContractKind.LOAN, source_id=1, target_id=2, 
        status=ContractStatus.ACTIVE, terms={"amount": 100}
    )
    h1_active = replace(h1, strategic=replace(h1.strategic, contracts={"c1": contract}))
    
    # Resolve with success
    strat_up, social_ups = ContractService.resolve_contract_outcome(h1_active, "c1", success=True)
    
    assert strat_up.contracts_add_or_update[0].status == ContractStatus.FULFILLED
    # source_up is for entity 1, but resolve_contract_outcome returns [source_up, target_up]
    # where source_up has bond_updates for target_id=2
    assert social_ups[0].bond_updates[0].sentiment_delta == 0.2
    assert social_ups[0].heroism_delta == 0.05
    
    # Resolve with betrayal
    strat_up_b, social_ups_b = ContractService.resolve_contract_outcome(h1_active, "c1", success=False, betrayal=True, betrayer_id=1)
    assert strat_up_b.contracts_add_or_update[0].status == ContractStatus.BETRAYED
    assert social_ups_b[0].notoriety_delta == 0.5
    assert social_ups_b[0].betrayal_increment == 1
    # Betrayal should trigger Avenge directive
    assert any(d.kind == DirectiveKind.COMBAT and d.target == "1" for d in strat_up_b.directives_add_or_update)
