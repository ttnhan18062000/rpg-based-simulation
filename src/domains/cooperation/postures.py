"""
src/domains/cooperation/postures.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 — Cooperation Postures.
Frozen, immutable dataclasses and canonical constants.
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass

class CooperationPosture(str, Enum):
    SOLO = "SOLO"
    REQUEST_HELP = "REQUEST_HELP"
    OFFER_HELP = "OFFER_HELP"
    JOIN_PARTY = "JOIN_PARTY"
    HIRE_SUPPORT = "HIRE_SUPPORT"
    FOLLOW_LEADER = "FOLLOW_LEADER"
    LEAD_PARTY = "LEAD_PARTY"
    AVOID_PARTNER = "AVOID_PARTNER"
    DEFER_NO_PARTNER = "DEFER_NO_PARTNER"
    ABANDON_PARTY = "ABANDON_PARTY"
    RESCUE_ALLY = "RESCUE_ALLY"
    GUARD_ALLY = "GUARD_ALLY"

@dataclass(frozen=True, slots=True)
class PostureDefinition:
    posture: CooperationPosture
    description: str
    intent_mapping: str

POSTURE_DEFINITIONS = {
    CooperationPosture.SOLO: PostureDefinition(
        CooperationPosture.SOLO,
        "Objective is acceptable alone.",
        "proceed_solo"
    ),
    CooperationPosture.REQUEST_HELP: PostureDefinition(
        CooperationPosture.REQUEST_HELP,
        "Ask another entity to assist.",
        "create_recruitment_offer"
    ),
    CooperationPosture.OFFER_HELP: PostureDefinition(
        CooperationPosture.OFFER_HELP,
        "Help another entity's objective.",
        "offer_cooperation"
    ),
    CooperationPosture.JOIN_PARTY: PostureDefinition(
        CooperationPosture.JOIN_PARTY,
        "Join existing group.",
        "accept_recruitment_offer"
    ),
    CooperationPosture.HIRE_SUPPORT: PostureDefinition(
        CooperationPosture.HIRE_SUPPORT,
        "Pay for help.",
        "create_paid_recruitment_offer"
    ),
    CooperationPosture.FOLLOW_LEADER: PostureDefinition(
        CooperationPosture.FOLLOW_LEADER,
        "Align with leader objective.",
        "boost_leader_goals"
    ),
    CooperationPosture.LEAD_PARTY: PostureDefinition(
        CooperationPosture.LEAD_PARTY,
        "Recruit or coordinate others.",
        "issue_group_directive"
    ),
    CooperationPosture.AVOID_PARTNER: PostureDefinition(
        CooperationPosture.AVOID_PARTNER,
        "Reject risky or untrusted partner.",
        "add_social_blocker"
    ),
    CooperationPosture.DEFER_NO_PARTNER: PostureDefinition(
        CooperationPosture.DEFER_NO_PARTNER,
        "Objective too risky without help.",
        "defer_objective_blocker"
    ),
    CooperationPosture.ABANDON_PARTY: PostureDefinition(
        CooperationPosture.ABANDON_PARTY,
        "Leave because of risk or trust violation.",
        "cancel_contract_betrayal"
    ),
    CooperationPosture.RESCUE_ALLY: PostureDefinition(
        CooperationPosture.RESCUE_ALLY,
        "Interrupt to help ally.",
        "emergency_rescue_project"
    ),
    CooperationPosture.GUARD_ALLY: PostureDefinition(
        CooperationPosture.GUARD_ALLY,
        "Protect ally during objective.",
        "tactical_guard_directive"
    ),
}

def get_posture_definition(posture: CooperationPosture | str) -> PostureDefinition:
    if isinstance(posture, str):
        try:
            posture = CooperationPosture(posture)
        except ValueError:
            raise ValueError(f"Unknown posture: {posture}")
    return POSTURE_DEFINITIONS[posture]
