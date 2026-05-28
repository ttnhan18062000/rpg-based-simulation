"""
src/domains/cooperation/events.py
───────────────────────────────────────────────────────────────────────────────
Phase 7 — Observability Events for Social Cooperation.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional
from src.domains.cooperation.postures import CooperationPosture

@dataclass(frozen=True, slots=True)
class HelpNeedDetectedEvent:
    entity_id: int
    tick: int
    need_key: str
    severity: float
    reason: str

@dataclass(frozen=True, slots=True)
class PartnerCandidateConsideredEvent:
    entity_id: int
    tick: int
    candidate_id: int
    trust_score: float
    role_fit_score: float
    cost_gold: int
    reason: str

@dataclass(frozen=True, slots=True)
class PartnerSelectedEvent:
    entity_id: int
    tick: int
    partner_id: int
    posture: CooperationPosture
    fit_score: float
    reason: str

@dataclass(frozen=True, slots=True)
class PartnerRejectedEvent:
    entity_id: int
    tick: int
    candidate_id: int
    reason: str
    fit_score: float
    trust_score: float

@dataclass(frozen=True, slots=True)
class CooperationDecisionSelectedEvent:
    entity_id: int
    tick: int
    posture: CooperationPosture
    partner_id: Optional[int]
    reason: str

@dataclass(frozen=True, slots=True)
class CooperationOutcomeLearnedEvent:
    entity_id: int
    tick: int
    partner_id: int
    outcome_type: str
    trust_delta: float
    future_effect: str
