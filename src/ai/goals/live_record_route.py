# Compliance IDs: STRAT-289
"""Where a winning goal's live record of its kind goes: continue, resume, make current, or become a switch candidate.

TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED (divergence 2.143). Pure reads of the entity: nothing here writes state; the caller
carries the returned `StrategicUpdate` through the authoritative apply path.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable, Optional

from src.core.state import EntityState
from src.core.strategic import (
    ProjectState,
    ProjectStatus,
    live_projects,
    project_target_matches,
    same_kind_record,
    supersede_record,
)
from src.core.updates import StrategicUpdate


@dataclass(frozen=True, slots=True)
class LiveRecordRoute:
    """The live record of the winning goal's kind, whether its target matches, and what to do with it.

    `update` is set when the record is dealt with here (continue, resume, make current): the caller returns it with its own bookkeeping deltas. `orphan` is set for an ACTIVE
    record at the matching target while ANOTHER live project is current: it goes through the switch check as the candidate."""
    existing: Optional[ProjectState]
    target_matches: bool
    update: Optional[StrategicUpdate] = None
    orphan: Optional[ProjectState] = None


def route_live_record(entity: EntityState, best_candidate: Any, resume: Callable[[EntityState, str], Optional[StrategicUpdate]]) -> LiveRecordRoute:
    """The live record a goal of `best_candidate.kind` continues, resumes, makes current or contests the current project with (see the module docstring).

    The record is the current project when it is of the kind, else the newest live one (`same_kind_record`); a COMPLETED or ABANDONED record and storage order take no part. A
    matching target never creates a same-target duplicate: the current project continues; a SUSPENDED record is resumed (`resume`, existing behaviour); an ACTIVE one that lost
    `current_project_id` (several writers clear it without ending the project) is made current again, or, beside another live current project, contests it through the switch check.
    A different target returns the record with `update` None: the caller's candidate may supersede it."""
    strat = entity.strategic
    existing = same_kind_record(strat.projects, best_candidate.kind, strat.current_project_id)
    matches = existing is not None and project_target_matches(existing, best_candidate.target_id, best_candidate.target_entity_id)
    if existing is None or not matches:
        return LiveRecordRoute(existing, matches)
    if existing.id == strat.current_project_id:
        return LiveRecordRoute(existing, matches, StrategicUpdate())
    if existing.status == ProjectStatus.SUSPENDED:
        return LiveRecordRoute(existing, matches, resume(entity, existing.id) or StrategicUpdate())
    if strat.current_project_id and strat.current_project_id in live_projects(strat.projects):
        return LiveRecordRoute(existing, matches, None, existing)
    return LiveRecordRoute(existing, matches, StrategicUpdate(current_project_id_set=existing.id, current_objective_id_set=existing.active_objective_id))


def orphan_switch_candidate(route: LiveRecordRoute, candidate: ProjectState, utility: float, current_tick: int) -> ProjectState:
    """The project the switch check weighs: the orphan as a fresh commitment at today's utility, locked like any freshly switched-in project (min(t+10, t+50)); the stored score
    and lock are written only on a win. `same_kind` is class-strict, so the orphan is never a ProjectKind record: its score is on the utility scale like a new candidate's.
    Without an orphan the generated `candidate` is returned unchanged."""
    if route.orphan is None:
        return candidate
    return replace(route.orphan, score=utility, lock_until_tick=min(current_tick + 10, current_tick + 50))


def supersede_on_win(switch_up: Optional[StrategicUpdate], route: LiveRecordRoute, candidate: ProjectState) -> Optional[StrategicUpdate]:
    """A winning candidate at a DIFFERENT target ends the live record of its kind, cap-neutral (the gate was not consulted). Only that one record ends; older same-kind duplicates
    are left to the existing trims. The update that makes the candidate current also ends the record, with the typed reason. A loss, or a matching target, changes nothing."""
    existing = route.existing
    if not switch_up or existing is None or route.target_matches or existing.id == candidate.id:
        return switch_up
    return replace(switch_up, projects_add_or_update=[
        supersede_record(existing),
        *[p for p in switch_up.projects_add_or_update if p.id != existing.id],
    ])
