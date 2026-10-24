"""
src/ai/goals/escalation.py
TCK-20261020-A-ESCALATED-NEED-IS-NEVER-REFUSED-FOR-CAPACITY (SURV-07)

A hunger or sleep goal that wins scoring at or past its escalation onset is never refused for project capacity. Pure read of the subject's needs.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.strategic import GoalKind
from src.engine.need_pull import need_is_pressing

if TYPE_CHECKING:
    from src.core.state import EntityState


def escalated_need_wins(entity: "EntityState", goal_kind: object) -> bool:
    """True for a HUNGER or FATIGUE goal while that need is at or past its onset.

    The onset is the pull's own and the scheduler wake's (`need_is_pressing`: ESCALATION_ONSET of the consequence line), no new constant. The
    caller's `not existing` keeps it to one project per need, so a full cap is exceeded by at most one hunger and one sleep project; nothing is
    evicted, abandoned or resumed (a live need project is outside the capacity trims, `live_projects_in_the_trim`). Below the onset the cap applies."""
    kind = getattr(goal_kind, "value", goal_kind)
    if kind == GoalKind.HUNGER.value:
        return need_is_pressing(entity.biological.hunger, 0.0)
    if kind == GoalKind.FATIGUE.value:
        return need_is_pressing(0.0, entity.biological.sleep_debt)
    return False
