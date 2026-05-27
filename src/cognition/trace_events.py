"""
src/cognition/trace_events.py
───────────────────────────────────────────────────────────────────────────────
Phase 2 — Frozen trace events for entity self-model updates.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Dict, Any


@dataclass(frozen=True, slots=True)
class SelfAwarenessUpdatedEvent:
    entity_id: int
    tick: int
    weaknesses: Tuple[str, ...]
    strengths: Tuple[str, ...]
    confidence: float
    stress: float


@dataclass(frozen=True, slots=True)
class NeedInterpretedEvent:
    entity_id: int
    tick: int
    dominant_need: str
    needs_summary: Dict[str, float]


@dataclass(frozen=True, slots=True)
class CapabilityEstimateUpdatedEvent:
    entity_id: int
    tick: int
    estimates_summary: Dict[str, Dict[str, Any]]


@dataclass(frozen=True, slots=True)
class KnowledgeFactLearnedEvent:
    entity_id: int
    tick: int
    subject: str
    fact_type: str
    certainty: float


@dataclass(frozen=True, slots=True)
class KnowledgeUnknownRecordedEvent:
    entity_id: int
    tick: int
    subject: str
    reason: str
