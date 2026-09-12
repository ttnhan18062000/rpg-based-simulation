"""
tests/integration/domains/cooperation/test_phase7_cooperation_phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 Integration Tests for orchestrating CooperationPhase.
"""

import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, GroupRecord
from src.core.builder import V2EntityBuilder
from src.core.strategic import RiskLevel, ProjectState, ProjectKind, ObjectiveState, ObjectiveKind
from src.core.updates import StateUpdate
from src.domains.cooperation.phase import CooperationPhase
from src.domains.cooperation.postures import CooperationPosture
from src.domains.combat_engagement.phase import build_combat_risk_belief
from src.systems.social_systems.contracts import ContractService, COOPERATION_OFFER_COOLDOWN_TICKS


def test_phase_skips_entity_without_help_need():
    # If no objective / no help needs exists and not in group, no evaluations are done
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).lifecycle(active=True).build())
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    
    update = StateUpdate()
    refined = CooperationPhase.execute(state, update)
    
    # cooperation_evaluations metric remains 0
    assert refined.metric_counters.get("cooperation_evaluations", 0) == 0


def test_phase_runs_when_help_need_exists():
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).combat(hp=20, max_hp=100).lifecycle(active=True).build())
    # low HP creates healer/protection need
    object.__setattr__(req.strategic, "current_objective_id", "obj_1")
    
    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    
    update = StateUpdate()
    refined = CooperationPhase.execute(state, update)
    
    assert refined.metric_counters.get("cooperation_evaluations", 0) == 1
    assert 1 in refined.entity_updates
    ent_up = refined.entity_updates[1]
    assert "last_cooperation_decision" in ent_up.property_updates


def test_cooperation_phase_no_immediate_reoffer_after_expiry_tick():
    # Tick T: entity A has a RECRUITMENT offer to trusted ally B that has just expired.
    a = (V2EntityBuilder(1)
         .kind("HERO")
         .location(0.0, 0.0)
         .combat(hp=100, max_hp=100, tactical_role="SUPPORT")
         .lifecycle(active=True)
         .build())

    b = (V2EntityBuilder(2)
         .kind("HERO")
         .location(1.0, 1.0)
         .combat(hp=100, max_hp=100, tactical_role="VANGUARD")
         .lifecycle(active=True)
         .build())

    obj = ObjectiveState(id="obj_wolf", kind=ObjectiveKind.DEFEAT_ENEMY)
    proj = ProjectState(id="proj_wolf", kind=ProjectKind.COMBAT, objectives=[obj], active_objective_id="obj_wolf")

    # TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN: real BeliefEntry (death_risk 0.6 -> HIGH)
    a.strategic.beliefs["combat_risk"] = build_combat_risk_belief(death_risk=0.6, current_tick=1)
    a.strategic.projects["proj_wolf"] = proj
    object.__setattr__(a.strategic, "current_project_id", "proj_wolf")
    object.__setattr__(a.strategic, "current_objective_id", "obj_wolf")

    a.social.trust_history[2] = 0.8

    expired_offer = ContractService.create_recruitment_contract(
        "cnt_recruit_1_2_90",
        source_id=1,
        target_id=2,
        tick=90,
    )
    assert expired_offer.expiry_tick == 100

    a = replace(
        a,
        strategic=replace(a.strategic, contracts={expired_offer.id: expired_offer}),
    )

    current_tick = 100
    state_t = AuthoritativeState(entities={1: a, 2: b}, tick=current_tick, seed=123)

    reap_update = ContractService.reap_expired_offers(state_t, StateUpdate())
    a_reap_up = reap_update.entity_updates[1]
    assert expired_offer.id in a_reap_up.strategic.contracts_remove
    ready_tick = a_reap_up.identity.cooldown_updates["cooperation_offer_retry"]
    assert ready_tick == current_tick + COOPERATION_OFFER_COOLDOWN_TICKS

    # Tick T+1: apply the authoritative effects of the reap (contract removed,
    # cooldown set) to build entity A's post-tick state, then re-run the
    # cooperation phase with the same eligible partner still available.
    a_next = replace(
        a,
        strategic=replace(a.strategic, contracts={}),
        identity=replace(a.identity, cooldowns={"cooperation_offer_retry": ready_tick}),
    )

    state_t1 = AuthoritativeState(entities={1: a_next, 2: b}, tick=current_tick + 1, seed=123)
    refined = CooperationPhase.execute(state_t1, StateUpdate())

    assert 1 in refined.entity_updates
    a_up_t1 = refined.entity_updates[1]
    decision_posture = a_up_t1.property_updates["last_cooperation_decision"]
    assert decision_posture != CooperationPosture.REQUEST_HELP.value
    assert decision_posture != CooperationPosture.HIRE_SUPPORT.value
    if a_up_t1.strategic is not None:
        assert not any(
            c.kind.name == "RECRUITMENT"
            for c in a_up_t1.strategic.contracts_add_or_update
        )


def test_phase_respects_feature_flag():
    req = (V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).combat(hp=20, max_hp=100).lifecycle(active=True).build())
    object.__setattr__(req.strategic, "current_objective_id", "obj_1")

    state = AuthoritativeState(entities={1: req}, tick=1, seed=123)
    state.periodic_due_ticks["social_cooperation_disabled"] = 1

    update = StateUpdate()
    refined = CooperationPhase.execute(state, update)

    assert 1 not in refined.entity_updates
    assert refined.metric_counters == {}


# ---------------------------------------------------------------------------
# TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION:
# party cohesion collapse (LEADER_LOST) must route through the real
# CooperationLearningService.learn() -- not a hand-copied inline shortcut --
# so trust_delta AND grudge_delta both accumulate, matching learn()'s own
# "abandoned" outcome_type exactly.
# ---------------------------------------------------------------------------

def test_party_cohesion_leader_lost_writes_trust_and_grudge_via_real_learning_service():
    leader = (
        V2EntityBuilder(1)
        .kind("HERO")
        .location(0.0, 0.0)
        .combat(hp=0, max_hp=100, alive=False)
        .build()
    )
    member = (
        V2EntityBuilder(2)
        .kind("HERO")
        .location(1.0, 1.0)
        .combat(hp=100, max_hp=100, alive=True)
        .build()
    )
    group = GroupRecord(id=1, leader_id=1, member_ids={1, 2}, anchor=(0.0, 0.0))
    state = AuthoritativeState(
        entities={1: leader, 2: member},
        groups={1: group},
        tick=5,
        seed=123,
    )

    refined = CooperationPhase.execute(state, StateUpdate())

    assert 2 in refined.entity_updates
    member_up = refined.entity_updates[2]
    assert member_up.social is not None

    # These values come from CooperationLearningService.learn()'s own real "abandoned"
    # outcome_type computation (services.py), not a hardcoded literal in this test --
    # asserted against the same real service to prove the phase actually calls it.
    from src.domains.cooperation.services import CooperationLearningService, CooperationOutcomeEvent
    expected = CooperationLearningService.learn(
        member,
        CooperationOutcomeEvent(tick=5, partner_id=1, outcome_type="abandoned", description=""),
        state,
    )

    assert member_up.social.trust_delta[1] == pytest.approx(expected.trust_delta)
    assert member_up.social.grudge_delta[1] == pytest.approx(expected.grudge_delta)
    # Confirms this isn't the old hardcoded -0.25-only branch that silently dropped grudge.
    assert member_up.social.grudge_delta[1] != 0.0


# ---------------------------------------------------------------------------
# TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION: JOIN_PARTY promotes the offering
# entity's own pending recruitment offer to ACTIVE, the real precondition
# GroupSystem.update_groups() (a later phase) needs to actually form a group.
# ---------------------------------------------------------------------------

def test_join_party_promotes_offerers_contract_to_active_with_extended_expiry():
    from src.core.strategic import ContractState, ContractKind, ContractStatus

    offerer = (
        V2EntityBuilder(1)
        .kind("HERO")
        .location(0.0, 0.0)
        .combat(hp=100, max_hp=100, alive=True)
        .build()
    )
    target = (
        V2EntityBuilder(2)
        .kind("HERO")
        .location(1.0, 1.0)
        .combat(hp=100, max_hp=100, alive=True)
        .build()
    )
    contract = ContractState(
        id="cnt_recruit_1_2_5",
        kind=ContractKind.RECRUITMENT,
        source_id=1,
        target_id=2,
        terms={"daily_pay": 0, "duration": 100},
        status=ContractStatus.OFFERED,
        created_tick=5,
        expiry_tick=15,
    )
    offerer = replace(offerer, strategic=replace(offerer.strategic, contracts={contract.id: contract}))
    state = AuthoritativeState(entities={1: offerer, 2: target}, tick=10, seed=123)

    refined = CooperationPhase.execute(state, StateUpdate())

    assert 1 in refined.entity_updates, "expected a promotion EntityUpdate for the offering entity"
    offerer_up = refined.entity_updates[1]
    assert offerer_up.strategic is not None
    promoted = {c.id: c for c in offerer_up.strategic.contracts_add_or_update}
    assert contract.id in promoted
    activated = promoted[contract.id]
    assert activated.status == ContractStatus.ACTIVE
    # Real regression guard for the bug found and fixed within this same ticket: a naive
    # status-only replace() would carry over the original ~10-tick OFFER-stage expiry_tick,
    # causing GroupSystem.update_groups() to treat the just-accepted contract as already
    # expired and immediately dissolve the group it just formed. accept_contract() (via
    # SocialContractSystem.transition_contract()) must reset expiry_tick to
    # tick + terms["duration"] instead.
    assert activated.expiry_tick == 10 + 100, (
        "expiry_tick must be reset to tick + duration on activation, not carried over from OFFERED"
    )
