"""A held shift is woken by a present threat to life only (designer ruling 2026-10-29; Bible 04, Standing Needs Escalate).

The tactical pass's own tests, asked of the held subject: the living neighbours it perceives as hostile (``tactical.perceived_threats``) that make a present
threat (``tactical_threat.present_threat_terms``). Hunger is not asked: a shift is only taken if it finishes before the starvation line."""
from __future__ import annotations

from src.core.state import AuthoritativeState, EntityState
from src.engine.cognition import SensoryFilter
from src.engine.domain_logic import SimulationDomainLogic
from src.engine.tactical import perceived_threats
from src.engine.tactical_threat import present_threat_terms


def held_work_is_threatened(entity: EntityState, state: AuthoritativeState) -> bool:
    """True when a perceived hostile makes a present threat to the subject of a held shift (the brain then re-decides; the wage is forfeited)."""
    neighbors = SensoryFilter.filter_saliency(entity, SimulationDomainLogic.get_neighbor_view(state, entity, radius=10.0), max_targets=5)  # as the tactical pass
    hostiles = perceived_threats(entity, neighbors)
    return bool(hostiles) and bool(present_threat_terms(entity, hostiles))
