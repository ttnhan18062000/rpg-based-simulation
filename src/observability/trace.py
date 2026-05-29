"""
src/observability/trace.py
───────────────────────────────────────────────────────────────────────────────
DecisionTrace schemas for Phase 17.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class DecisionOptionTrace:
    name: str
    score: float
    metadata: dict[str, Any] = None

@dataclass(frozen=True, slots=True)
class RejectedOptionTrace:
    name: str
    reason: str

@dataclass(frozen=True, slots=True)
class DecisionTrace:
    decision_id: str
    entity_id: int
    decision_kind: str
    noticed: tuple[str, ...]
    known: tuple[str, ...]
    needs: tuple[str, ...]
    capability_refs: tuple[str, ...]
    considered_options: tuple[DecisionOptionTrace, ...]
    selected_option: str | None
    rejected_options: tuple[RejectedOptionTrace, ...]
    reason: str
    expected_effects: tuple[str, ...]
