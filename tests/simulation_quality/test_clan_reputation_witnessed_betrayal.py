"""Idea 54 (Guilt by Association) corpus proof (TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS).

No registered corpus world carries real `ClanState` content (confirmed via grep) -- Unit-tier
synthetic content is idiomatic here (corpus_tier_taxonomy.md), matching M9 ticket 2's own precedent.

`CLAN_REPUTATION_MISCONDUCT_DELTA`'s only LIVE pipeline write site is the real party-defection
trigger (src/engine/pipeline_phases/groups.py, GroupPhase.resolve()) -- the alternative
contract-betrayal site (src/systems/social_systems/contracts.py) is explicitly self-documented as
never wired to any live pipeline caller. This test exercises the real, live defection path through
one real Kernel.tick_once(), then directly proves the resulting clan_reputation degradation changes
a stranger's SocialAppraisalSystem.appraise_contract() decision for an unmet same-Clan member.

appraise_contract()'s internal trust_score is not returned to callers (confirmed via read) -- its
real, externally-observable proxy is the ReasonCode/ContractStatus decision _appraise_loan() derives
from it (`trust_score > 0.5` -> ReasonCode.FRIENDLY_LOAN/ACCEPTED, else UNNECESSARY_DEBT/CANCELLED).
The observer's public_reputation is tuned so baseline trust_score sits just above 0.5 (ACCEPTED) --
CLAN_INFLUENCE_WEIGHT's max single-defection swing (-0.025) is real, correctly small by design
(SOC-268's own "bounded influence" intent), so this test targets the exact boundary the real delta
is guaranteed to cross, not an arbitrary threshold.
"""
from __future__ import annotations

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction, ReasonCode
from src.core.state import AuthoritativeState, ClanState, GroupRecord
from src.core.strategic import ContractKind, ContractState, ContractStatus
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.systems.social_systems.appraisal import SocialAppraisalSystem

# Tuned so baseline trust_score = 0.7*public_trust + 0.3*0.5 + (0.5-0.5)*0.2 lands just above 0.5
# (public_reputation=1.04 -> public_trust=0.52 -> 0.7*0.52 + 0.15 = 0.514), so
# CLAN_INFLUENCE_WEIGHT's real -0.025 max single-defection swing (clan_trust 0.5 -> 0.375) crosses
# back under 0.5 (0.514 - 0.025 = 0.489).
_OBSERVER_TUNED_PUBLIC_REPUTATION = 1.04


def _two_clans_of_four(defector_grievances: int) -> AuthoritativeState:
    entities = {}
    clan_a_ids = (1, 2, 3, 4)
    clan_b_ids = (5, 6, 7, 8)
    for eid in clan_a_ids + clan_b_ids:
        builder = (
            V2EntityBuilder(eid)
            .kind("citizen")
            .location(float(eid), 0.0)
            .identity(faction=Faction.TOWN_COUNCIL)
        )
        if eid == 3:
            builder = builder.social(public_reputation=_OBSERVER_TUNED_PUBLIC_REPUTATION)
        entities[eid] = builder.build()

    group = GroupRecord(
        id=100,
        leader_id=1,
        member_ids={1, 2},
        anchor=(1.0, 0.0),
        grievance_log=tuple(f"grievance_{i}" for i in range(defector_grievances)),
    )
    clans = {
        "clan_a": ClanState(clan_id="clan_a", name="Clan A", member_entity_ids=clan_a_ids, clan_reputation=1.0),
        "clan_b": ClanState(clan_id="clan_b", name="Clan B", member_entity_ids=clan_b_ids, clan_reputation=1.0),
    }
    return AuthoritativeState(tick=0, seed=42, entities=entities, groups={100: group}, clans=clans)


def _loan_decision_from_unmet_clan_a_member(source_entity_id: int, state: AuthoritativeState):
    observer = V2EntityBuilder(999).kind("citizen").location(0.0, 0.0).identity(faction=Faction.TOWN_COUNCIL).build()
    contract = ContractState(
        id="c1", kind=ContractKind.LOAN, source_id=source_entity_id, target_id=999,
        status=ContractStatus.OFFERED, terms={"amount": 10, "interest_rate": 0.05},
    )
    status, reason, _ = SocialAppraisalSystem.appraise_contract(observer, contract, state)
    return status, reason


def test_defection_degrades_clan_reputation_and_flips_stranger_loan_decision():
    baseline_state = _two_clans_of_four(defector_grievances=0)
    baseline_status, baseline_reason = _loan_decision_from_unmet_clan_a_member(source_entity_id=3, state=baseline_state)
    assert (baseline_status, baseline_reason) == (ContractStatus.ACCEPTED, ReasonCode.FRIENDLY_LOAN), (
        "baseline (no clan misconduct) must accept the loan from an observer whose tuned trust_score "
        "sits just above the 0.5 threshold"
    )

    state = _two_clans_of_four(defector_grievances=3)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        kernel.tick_once()
    finally:
        kernel.shutdown()

    final_clan_a = kernel.state.clans["clan_a"]
    assert round(1.0 - final_clan_a.clan_reputation, 4) == 0.25, (
        "a real party defection by a Clan A member must degrade Clan A's clan_reputation by "
        "exactly CLAN_REPUTATION_MISCONDUCT_DELTA (0.25) through the real, live GroupPhase pipeline"
    )

    post_status, post_reason = _loan_decision_from_unmet_clan_a_member(source_entity_id=3, state=kernel.state)
    assert (post_status, post_reason) == (ContractStatus.CANCELLED, ReasonCode.UNNECESSARY_DEBT), (
        "after another Clan A member's witnessed defection degraded Clan A's own reputation, a "
        "stranger's trust toward an UNMET Clan A member must drop enough to flip the same loan "
        "decision from ACCEPTED to CANCELLED -- a real, measurable, attributable guilt-by-association "
        "effect, not a tautology"
    )
