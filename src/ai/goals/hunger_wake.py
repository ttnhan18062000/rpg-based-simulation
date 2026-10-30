"""
src/ai/goals/hunger_wake.py
TCK-20261030-SLEEP-WINS-OVER-STARVING-HUNGER-WHEN-NO-BED (SURV-07, Bible 04 "Standing Needs Escalate", divergence 2.152)

Bible 04 says a woken sleeper "eats if a way is open". Before this, the hunger wake (2.115) woke the brain of a chosen sleeper, but (1) the held sleep ended
only if the decision returned a task, and a hunger project already current only walks (a navigation-only update), so the sleep carried on; and (2) when the
sleep ended anyway, the next ordinary decision weighed the two needs by score and the sleep goal out-scored the hunger goal, so the subject rested again.

The rule, in one set of predicates asked at each site:
  * `hunger_wake_ends_chosen_sleep`: the wake decision of a CHOSEN sleeper (asleep, debt below the collapse line, hunger pressing) with a way to eat open and
    no present threat. At that decision the sleep ends (tactical) and the hunger project is HELD (`with_hunger_hold`).
  * `hunger_hold_active`: the subject's current hunger project is held. While it is, the sleep goal does not displace it and a rest in place does not fire.
  * `hold_end_reason`: the typed `HoldEnd` when the hold ends: collapse, a present threat to life, the meal, or the way closing.
The hold is a typed field of the hunger project (`ProjectState.held_for`), set and cleared through a `StrategicUpdate` and so on the authoritative apply path; this
module only reads state and returns updates. No score changes and no new constant: every line is an existing one (`SLEEP_DEBT.collapse_line`,
`need_pull.hunger_is_pressing`, `ways.ways_in_reach`, `present_threat_to`).
"""
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Optional

from src.ai.goals.present_threat import present_threat_to
from src.ai.goals.ways import ways_in_reach
from src.core.strategic import HoldEnd, ProjectHold, ProjectStatus
from src.core.updates import StrategicUpdate
from src.engine.need_pull import hunger_is_pressing
from src.engine.sleep_debt import is_asleep, must_collapse

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.strategic import ProjectState


def hunger_wake_ends_chosen_sleep(entity: "EntityState", state: "AuthoritativeState") -> bool:
    """True when `entity` is a CHOSEN sleeper (asleep, debt below the collapse line) at pressing hunger with a way to eat open and no present threat.

    "Open" is `ways_in_reach` (the one definition: carried food, an admitted inn meal, a forage, scavenge or hunt step, a sale, and a takeable
    shift that earns a priced meal). A present threat to life outranks it (SURV-07), and a collapse (debt at or above the line) is untouched."""
    return (
        is_asleep(entity)
        and not must_collapse(entity.biological.sleep_debt)
        and hunger_is_pressing(entity.biological.hunger)
        and bool(ways_in_reach(entity, state))
        and not present_threat_to(entity, state)
    )


def _held_projects(entity: "EntityState") -> list["ProjectState"]:
    return [p for p in entity.strategic.projects.values() if p.held_for is not None]


def hunger_hold_active(entity: "EntityState") -> bool:
    """True while the subject's CURRENT project is a held hunger project (ACTIVE, `held_for` set): the sleep goal does not displace it."""
    project = entity.strategic.projects.get(entity.strategic.current_project_id or "")
    return project is not None and project.held_for is not None and project.status == ProjectStatus.ACTIVE


def hold_end_reason(entity: "EntityState", state: "AuthoritativeState", project: "ProjectState") -> Optional[HoldEnd]:
    """The `HoldEnd` of a held `project` now, or None while the hold stands. In order: a collapse, a present threat to life, the meal, the way closing."""
    if must_collapse(entity.biological.sleep_debt):
        return HoldEnd.COLLAPSE
    if present_threat_to(entity, state):
        return HoldEnd.THREAT_ANSWERED
    if project.status == ProjectStatus.COMPLETED or not hunger_is_pressing(entity.biological.hunger):
        return HoldEnd.EATEN
    if project.status != ProjectStatus.ACTIVE or entity.strategic.current_project_id != project.id or not ways_in_reach(entity, state):
        return HoldEnd.WAY_CLOSED
    return None


def with_hunger_hold(entity: "EntityState", state: "AuthoritativeState", update: StrategicUpdate) -> StrategicUpdate:
    """`update` (the strategic decision of this tick) with the hold's bookkeeping merged in, all as project replacements on the apply path.

    Ends every held project of the subject whose `hold_end_reason` is set (recording the `HoldEnd`); and at the wake decision of a chosen sleeper
    (`hunger_wake_ends_chosen_sleep`) holds the hunger project the decision made current (or the current one), unless it is held already."""
    replacements: dict[str, "ProjectState"] = {}
    for held in _held_projects(entity):
        ended = hold_end_reason(entity, state, held)
        if ended is not None:
            replacements[held.id] = replace(held, held_for=None, hold_ended_by=ended)
    if hunger_wake_ends_chosen_sleep(entity, state):
        current_id = update.current_project_id_set or entity.strategic.current_project_id or ""
        projects = {p.id: p for p in entity.strategic.projects.values()}
        projects.update({p.id: p for p in update.projects_add_or_update})
        target = projects.get(current_id)
        if target is not None and target.kind == "hunger" and target.status == ProjectStatus.ACTIVE and target.held_for is None:
            replacements[target.id] = replace(replacements.get(target.id, target), held_for=ProjectHold.HUNGER_WAKE)
    if not replacements:
        return update
    kept = [p for p in update.projects_add_or_update if p.id not in replacements]
    return replace(update, projects_add_or_update=kept + list(replacements.values()))
