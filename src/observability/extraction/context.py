"""The read-only context every extraction function receives."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from src.core.state import AuthoritativeState
from src.observability.config import ObservabilityMode
from src.observability.events import SimulationEvent


class RunState(Protocol):
    """The per-run emit-once collections and thresholds EventExtractor owns, read at call time.

    The facade class is passed as-is so the lookups stay on ``EventExtractor``: a test that reassigns or patches one of these attributes
    still changes what the extraction functions see.
    """

    _seen_routing_families: dict[int, set[str]]
    _last_xp_tick: dict[int, int]
    _emitted_plateau: set[int]
    _emitted_stale_leads: dict[int, set[str]]
    _emitted_social_memory: set[tuple[int, int]]
    _emitted_contract_milestones: set[str]
    _last_capability_growth_tick: dict[int, int]
    _emitted_capability_stalled: set[int]
    _SOCIAL_MEMORY_THRESHOLD: float
    _CONTRACT_MILESTONE_THRESHOLDS: tuple[tuple[float, str], ...]


@dataclass(frozen=True)
class ExtractContext:
    """One extract() call: the two states, the update, the mode, the clock reading and the four resolved rollback flags."""

    prior_state: AuthoritativeState
    current_state: AuthoritativeState
    update: Any
    mode: ObservabilityMode
    tick: int
    now: float
    push_shapers_active: bool
    push_shapers_phase2_active: bool
    push_shapers_quest_active: bool
    push_shapers_agency_active: bool
    max_consecutive_rejections: int
    run_state: Any
    # commitment_abandoned needs src.domains.commitment, which the phase18 import allowlist lets only event_extractor.py import
    abandonment_events: Callable[..., list[SimulationEvent]]
