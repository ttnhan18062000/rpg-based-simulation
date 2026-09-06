import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.systems.social_systems.appraisal import SocialAppraisalSystem
from src.core.enums import EntityRole

def create_mock_entity(eid: int, gold: int = 10, hp: int = 100):
    from src.core.builder import V2EntityBuilder
    from src.core.enums import Faction
    return (V2EntityBuilder(eid)
        .kind("hero")
        .location(0, 0)
        .identity(role=EntityRole.HERO)
        .identity(faction=Faction.HERO_GUILD)
        .combat(hp=hp, max_hp=100)
        .inventory(gold=gold)
        .combat(alive=True)
        .build())

def test_appraise_recruitment_low_trust_low_pay():
    entity = create_mock_entity(1)
    contract = ContractState(
        id="c1",
        kind=ContractKind.RECRUITMENT,
        source_id=2,
        target_id=1,
        terms={"daily_pay": 2} # Very low pay
    )
    state = AuthoritativeState(tick=100, seed=42)
    
    from src.core.enums import ReasonCode
    status, reason, counter = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.CANCELLED
    assert reason == ReasonCode.INSUFFICIENT_INCENTIVE

def test_appraise_recruitment_haggling():
    entity = create_mock_entity(1, gold=10) # Not desperate
    contract = ContractState(
        id="c1",
        kind=ContractKind.RECRUITMENT,
        source_id=2,
        target_id=1,
        terms={"daily_pay": 5} # Low but hagglable (utility 0.5, trust 0.5 -> score 0.4ish)
    )
    state = AuthoritativeState(tick=100, seed=42)
    
    from src.core.enums import ReasonCode
    status, reason, counter = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.COUNTERED
    assert reason == ReasonCode.HAGGLING_FOR_PAY
    assert counter["daily_pay"] == 10 # Should haggle for fair pay

def test_appraise_recruitment_high_trust():
    entity = create_mock_entity(1)
    from src.core.state import SocialBond
    new_social = replace(entity.social, bonds={2: SocialBond(target_id=2, sentiment=1.0)})
    entity = replace(entity, social=new_social)
    
    contract = ContractState(
        id="c1",
        kind=ContractKind.RECRUITMENT,
        source_id=2,
        target_id=1,
        terms={"daily_pay": 5} # Low pay but high trust
    )
    state = AuthoritativeState(tick=100, seed=42)
    
    from src.core.enums import ReasonCode
    status, reason, counter = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.ACCEPTED
    assert reason == ReasonCode.LOYALTY_ACCEPTANCE

def test_appraise_recruitment_danger_low_hp():
    entity = create_mock_entity(1, hp=40) # Low HP (40%)
    contract = ContractState(
        id="c1",
        kind=ContractKind.RECRUITMENT,
        source_id=2,
        target_id=1,
        terms={"daily_pay": 20, "risk_level": "HIGH"}
    )
    state = AuthoritativeState(tick=100, seed=42)
    
    from src.core.enums import ReasonCode
    status, reason, counter = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.FAILED
    assert reason == ReasonCode.LOW_HP_RETREAT


def _make_source_with_reputation(entity_id: int, public_reputation: float):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(entity_id)
        .kind("human").location(1, 1)
        .social(public_reputation=public_reputation)
        .combat(readiness=100.0)
        .build())


def test_stranger_judgment_incorporates_clan_reputation():
    """Idea 54/M5 (SOC-268): a stranger with no direct SocialBond/familiarity
    history toward a clan member gets a trust prior that incorporates that
    member's clan's clan_reputation -- low vs. high clan_reputation produces
    a distinguishably different appraisal outcome for the same base entity
    setup (public_reputation=0.2 puts the no-clan-influence trust_score close
    to the 0.2 TOTAL_DISTRUST threshold)."""
    from src.core.state import ClanState
    from src.core.enums import ReasonCode

    observer = create_mock_entity(1)
    source = _make_source_with_reputation(10, public_reputation=0.2)

    contract = ContractState(
        id="c_clan_stranger",
        kind=ContractKind.RECRUITMENT,
        source_id=10,
        target_id=1,
        terms={"daily_pay": 20},
        status=ContractStatus.OFFERED,
    )

    low_clan = ClanState(clan_id="lowrep", member_entity_ids=(10,), clan_reputation=0.0)
    high_clan = ClanState(clan_id="highrep", member_entity_ids=(10,), clan_reputation=2.0)

    state_low = AuthoritativeState(entities={1: observer, 10: source}, tick=1, seed=1, clans={"lowrep": low_clan})
    state_high = AuthoritativeState(entities={1: observer, 10: source}, tick=1, seed=1, clans={"highrep": high_clan})

    status_low, reason_low, _ = SocialAppraisalSystem.appraise_contract(observer, contract, state_low)
    status_high, reason_high, _ = SocialAppraisalSystem.appraise_contract(observer, contract, state_high)

    assert status_low == ContractStatus.CANCELLED
    assert reason_low == ReasonCode.TOTAL_DISTRUST
    assert not (status_high == ContractStatus.CANCELLED and reason_high == ReasonCode.TOTAL_DISTRUST), (
        f"High clan_reputation should clear the trust gate, got status={status_high} reason={reason_high}"
    )


def test_stranger_judgment_clan_reputation_does_not_leak_into_bond_branch():
    """AC3 regression guard: an observer with direct history (a SocialBond)
    toward the source must be judged identically regardless of the source's
    clan's clan_reputation -- the bond branch (appraisal.py:39-41) stays
    clan-blind."""
    from src.core.state import ClanState, SocialBond

    bond = SocialBond(target_id=10, sentiment=0.5)
    observer = create_mock_entity(1)
    observer = replace(observer, social=replace(observer.social, bonds={10: bond}))
    source = _make_source_with_reputation(10, public_reputation=0.2)

    contract = ContractState(
        id="c_clan_bond",
        kind=ContractKind.RECRUITMENT,
        source_id=10,
        target_id=1,
        terms={"daily_pay": 20},
        status=ContractStatus.OFFERED,
    )

    low_clan = ClanState(clan_id="lowrep", member_entity_ids=(10,), clan_reputation=0.0)
    high_clan = ClanState(clan_id="highrep", member_entity_ids=(10,), clan_reputation=2.0)

    state_low = AuthoritativeState(entities={1: observer, 10: source}, tick=1, seed=1, clans={"lowrep": low_clan})
    state_high = AuthoritativeState(entities={1: observer, 10: source}, tick=1, seed=1, clans={"highrep": high_clan})

    result_low = SocialAppraisalSystem.appraise_contract(observer, contract, state_low)
    result_high = SocialAppraisalSystem.appraise_contract(observer, contract, state_high)

    assert result_low == result_high


# --- TCK-20260824-AFFECTION-CONTRACT-GATE: shared gate generalization ------------------------


def test_shared_gate_no_fallthrough_for_gated_kinds():
    """No ContractKind handled by appraise_contract() may reach the generic
    CANCELLED/UNKNOWN fallthrough -- CANCELLED is a legitimate kind-specific outcome,
    only ReasonCode.UNKNOWN signals a fallthrough."""
    from src.core.enums import ReasonCode

    entity = create_mock_entity(1)
    state = AuthoritativeState(tick=100, seed=42)

    kind_terms = {
        ContractKind.RECRUITMENT: {"daily_pay": 20},
        ContractKind.LOAN: {"amount": 10, "interest_rate": 0.05},
        ContractKind.POSITION_SWAP: {},
        ContractKind.MERCHANT: {"price": 100, "item_value": 100},
        ContractKind.TEAM_UP: {"risk_level": "NORMAL"},
        ContractKind.PAID_INFORMATION: {},
        ContractKind.TEACH: {},
        ContractKind.MARRIAGE: {},
    }
    for kind, terms in kind_terms.items():
        contract = ContractState(id=f"c_{kind.value}", kind=kind, source_id=2, target_id=1, terms=terms)
        status, reason, _ = SocialAppraisalSystem.appraise_contract(entity, contract, state)
        assert reason != ReasonCode.UNKNOWN, f"{kind} fell through to generic UNKNOWN"


def test_shared_gate_dispatches_by_kind():
    """The shared helper accepts a ContractKind and returns a real
    (ContractStatus, ReasonCode, Dict[str, Any]) tuple for each new kind."""
    from src.core.enums import ReasonCode

    entity = create_mock_entity(1)
    state = AuthoritativeState(tick=100, seed=42)

    for kind, terms in (
        (ContractKind.MERCHANT, {"price": 100, "item_value": 100}),
        (ContractKind.TEAM_UP, {"risk_level": "NORMAL"}),
        (ContractKind.PAID_INFORMATION, {}),
    ):
        contract = ContractState(id=f"disp_{kind.value}", kind=kind, source_id=2, target_id=1, terms=terms)
        status, reason, terms_out = SocialAppraisalSystem.appraise_contract(entity, contract, state)
        assert isinstance(status, ContractStatus)
        assert isinstance(reason, ReasonCode)
        assert isinstance(terms_out, dict)


def test_trade_merchant_kind_appraisal():
    from src.core.enums import ReasonCode
    from src.core.state import SocialBond

    state = AuthoritativeState(tick=100, seed=42)

    # Accept: fair price relative to item value at neutral trust.
    accepted_entity = create_mock_entity(1)
    accepted_contract = ContractState(
        id="c_trade_accept", kind=ContractKind.MERCHANT, source_id=2, target_id=1,
        terms={"price": 100, "item_value": 100},
    )
    status, reason, _ = SocialAppraisalSystem.appraise_contract(accepted_entity, accepted_contract, state)
    assert status == ContractStatus.ACCEPTED
    assert reason == ReasonCode.FAIR_COMPENSATION

    # Hard-cancel via the untouched shared prelude (bond.sentiment < -0.8).
    distrustful_entity = create_mock_entity(1)
    distrustful_entity = replace(
        distrustful_entity,
        social=replace(distrustful_entity.social, bonds={2: SocialBond(target_id=2, sentiment=-0.9)}),
    )
    distrust_contract = ContractState(
        id="c_trade_distrust", kind=ContractKind.MERCHANT, source_id=2, target_id=1,
        terms={"price": 100, "item_value": 100},
    )
    status, reason, _ = SocialAppraisalSystem.appraise_contract(distrustful_entity, distrust_contract, state)
    assert status == ContractStatus.CANCELLED
    assert reason == ReasonCode.TOTAL_DISTRUST

    # Countered: fair-but-low offer triggers haggling.
    haggle_entity = create_mock_entity(1)
    haggle_contract = ContractState(
        id="c_trade_haggle", kind=ContractKind.MERCHANT, source_id=2, target_id=1,
        terms={"price": 50, "item_value": 100},
    )
    status, reason, counter = SocialAppraisalSystem.appraise_contract(haggle_entity, haggle_contract, state)
    assert status == ContractStatus.COUNTERED
    assert reason == ReasonCode.HAGGLING_FOR_PAY
    assert counter["price"] == 100


def test_team_up_kind_appraisal():
    from src.core.enums import ReasonCode
    from src.core.state import SocialBond

    state = AuthoritativeState(tick=100, seed=42)

    # Accept: high trust bond.
    trusting_entity = create_mock_entity(1)
    trusting_entity = replace(
        trusting_entity,
        social=replace(trusting_entity.social, bonds={2: SocialBond(target_id=2, sentiment=0.5)}),
    )
    accept_contract = ContractState(
        id="c_team_up_accept", kind=ContractKind.TEAM_UP, source_id=2, target_id=1,
        terms={"risk_level": "NORMAL"},
    )
    status, reason, _ = SocialAppraisalSystem.appraise_contract(trusting_entity, accept_contract, state)
    assert status == ContractStatus.ACCEPTED
    assert reason == ReasonCode.TEAM_UP_ACCEPTED

    # Decline: default (neutral, below-threshold) trust.
    neutral_entity = create_mock_entity(1)
    decline_contract = ContractState(
        id="c_team_up_decline", kind=ContractKind.TEAM_UP, source_id=2, target_id=1,
        terms={"risk_level": "NORMAL"},
    )
    status, reason, _ = SocialAppraisalSystem.appraise_contract(neutral_entity, decline_contract, state)
    assert status == ContractStatus.CANCELLED
    assert reason == ReasonCode.TEAM_UP_DECLINED

    # Failed: HIGH risk while at low HP, regardless of trust.
    wounded_entity = create_mock_entity(1, hp=40)
    wounded_entity = replace(
        wounded_entity,
        social=replace(wounded_entity.social, bonds={2: SocialBond(target_id=2, sentiment=1.0)}),
    )
    risky_contract = ContractState(
        id="c_team_up_failed", kind=ContractKind.TEAM_UP, source_id=2, target_id=1,
        terms={"risk_level": "HIGH"},
    )
    status, reason, _ = SocialAppraisalSystem.appraise_contract(wounded_entity, risky_contract, state)
    assert status == ContractStatus.FAILED
    assert reason == ReasonCode.LOW_HP_RETREAT


def test_paid_information_kind_appraisal_accepts_once_prelude_passes():
    from src.core.enums import ReasonCode

    entity = create_mock_entity(1)
    state = AuthoritativeState(tick=100, seed=42)
    contract = ContractState(
        id="c_info", kind=ContractKind.PAID_INFORMATION, source_id=2, target_id=1, terms={},
    )
    status, reason, _ = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.ACCEPTED
    assert reason == ReasonCode.INFORMATION_SALE_ACCEPTED


def test_teach_kind_appraisal_accepts_once_prelude_passes():
    from src.core.enums import ReasonCode

    entity = create_mock_entity(1)
    state = AuthoritativeState(tick=100, seed=42)
    contract = ContractState(
        id="c_teach", kind=ContractKind.TEACH, source_id=2, target_id=1, terms={},
    )
    status, reason, _ = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.ACCEPTED
    assert reason == ReasonCode.TEACH_ACCEPTED


def test_teach_boundary_trust_score_matches_recruitment_and_team_up_just_below_0_2():
    """A trust score just below the shared hard-cancel threshold (0.2, strict '<') must
    produce the same CANCELLED/TOTAL_DISTRUST outcome for TEACH as it already does for
    RECRUITMENT/TEAM_UP at that same trust score -- proving no kind-specific threshold
    drift was introduced by _appraise_teach. (trust_score == 0.2 exactly does NOT trigger
    the hard-cancel, since the prelude's comparison is strict '<' -- appraisal.py:48 --
    so the boundary value used here is just under it, not exactly on it.)"""
    from src.core.enums import ReasonCode
    from src.core.state import SocialBond

    def entity_at_boundary_trust():
        entity = create_mock_entity(1)
        # trust_score = (sentiment + 1.0) / 2.0 == 0.195 -> sentiment == -0.61
        return replace(
            entity,
            social=replace(entity.social, bonds={2: SocialBond(target_id=2, sentiment=-0.61)}),
        )

    state = AuthoritativeState(tick=100, seed=42)

    recruitment_contract = ContractState(
        id="c_recruit_boundary", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
        terms={"daily_pay": 20},
    )
    team_up_contract = ContractState(
        id="c_team_up_boundary", kind=ContractKind.TEAM_UP, source_id=2, target_id=1,
        terms={"risk_level": "NORMAL"},
    )
    teach_contract = ContractState(
        id="c_teach_boundary", kind=ContractKind.TEACH, source_id=2, target_id=1, terms={},
    )

    recruit_status, recruit_reason, _ = SocialAppraisalSystem.appraise_contract(
        entity_at_boundary_trust(), recruitment_contract, state
    )
    team_up_status, team_up_reason, _ = SocialAppraisalSystem.appraise_contract(
        entity_at_boundary_trust(), team_up_contract, state
    )
    teach_status, teach_reason, _ = SocialAppraisalSystem.appraise_contract(
        entity_at_boundary_trust(), teach_contract, state
    )

    assert recruit_status == team_up_status == teach_status == ContractStatus.CANCELLED
    assert recruit_reason == team_up_reason == teach_reason == ReasonCode.TOTAL_DISTRUST


def test_marriage_boundary_trust_score_matches_recruitment_and_team_up_and_teach_just_below_0_2():
    """Same boundary-value proof as the TEACH test above, extended to MARRIAGE: a trust score
    just under the shared hard-cancel threshold (0.195, not exactly 0.2 -- strict '<' comparison
    at appraisal.py:48) must produce the same CANCELLED/TOTAL_DISTRUST outcome for MARRIAGE as it
    already does for RECRUITMENT/TEAM_UP/TEACH -- proving no marriage-specific threshold drift."""
    from src.core.enums import ReasonCode
    from src.core.state import SocialBond

    def entity_at_boundary_trust():
        entity = create_mock_entity(1)
        # trust_score = (sentiment + 1.0) / 2.0 == 0.195 -> sentiment == -0.61
        return replace(
            entity,
            social=replace(entity.social, bonds={2: SocialBond(target_id=2, sentiment=-0.61)}),
        )

    state = AuthoritativeState(tick=100, seed=42)

    recruitment_contract = ContractState(
        id="c_recruit_boundary_marriage", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
        terms={"daily_pay": 20},
    )
    team_up_contract = ContractState(
        id="c_team_up_boundary_marriage", kind=ContractKind.TEAM_UP, source_id=2, target_id=1,
        terms={"risk_level": "NORMAL"},
    )
    teach_contract = ContractState(
        id="c_teach_boundary_marriage", kind=ContractKind.TEACH, source_id=2, target_id=1, terms={},
    )
    marriage_contract = ContractState(
        id="c_marriage_boundary", kind=ContractKind.MARRIAGE, source_id=2, target_id=1, terms={},
    )

    recruit_status, recruit_reason, _ = SocialAppraisalSystem.appraise_contract(
        entity_at_boundary_trust(), recruitment_contract, state
    )
    team_up_status, team_up_reason, _ = SocialAppraisalSystem.appraise_contract(
        entity_at_boundary_trust(), team_up_contract, state
    )
    teach_status, teach_reason, _ = SocialAppraisalSystem.appraise_contract(
        entity_at_boundary_trust(), teach_contract, state
    )
    marriage_status, marriage_reason, _ = SocialAppraisalSystem.appraise_contract(
        entity_at_boundary_trust(), marriage_contract, state
    )

    assert recruit_status == team_up_status == teach_status == marriage_status == ContractStatus.CANCELLED
    assert recruit_reason == team_up_reason == teach_reason == marriage_reason == ReasonCode.TOTAL_DISTRUST


def test_contract_kind_merchant_does_not_conflate_with_information_provider_archetype():
    """ContractKind.MERCHANT and InformationProviderArchetype.MERCHANT share a string value
    but are unrelated enums on unrelated classes -- Trade's appraisal must never compare
    against the archetype enum."""
    from src.domains.information.providers import InformationProviderArchetype

    assert ContractKind.MERCHANT is not InformationProviderArchetype.MERCHANT
    assert ContractKind.MERCHANT.__class__ is not InformationProviderArchetype.MERCHANT.__class__
