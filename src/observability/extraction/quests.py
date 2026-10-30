"""Quest progress and commitment_abandoned events of one entity."""

from __future__ import annotations

from typing import Any

from src.core.quests import QuestState
from src.observability.events import QuestEvent, SimulationEvent
from src.observability.extraction.context import ExtractContext


def _quest_status_events(ctx: ExtractContext, eid: int, qid: Any, prior_qstate: Any, qstate: Any) -> list[SimulationEvent]:
    """quest_event on a quest status change (rollback path only)."""
    tick = ctx.tick
    now = ctx.now
    _push_shapers_quest_active = ctx.push_shapers_quest_active
    events: list[SimulationEvent] = []
    if not _push_shapers_quest_active and isinstance(qstate, QuestState):
        # quest_status (QuestStatus: ACTIVE/COMPLETED/REWARD_PENDING/REWARDED) is the
        # field QuestService/QuestResolutionSystem actually mutate — NOT the generic
        # .status (ProjectStatus) inherited from ProjectState, which quest logic never
        # touches. .name.lower() (not str(enum)) so the status string matches what
        # quality_hub.py's _translate_quest_event() checks for ("completed"/"failed").
        # Explicit payload={"status": ...} — QuestEvent.status is a top-level Pydantic
        # field, never copied into .payload by ObservabilityEventEnvelope.
        # from_simulation_event() (which only carries .payload through), so without
        # this, quality_hub.py's translator is structurally blind to the real status
        # regardless of which field this branch reads — a second, deeper bug found
        # alongside the ProjectStatus/QuestStatus field mismatch itself.
        if prior_qstate is None or not isinstance(prior_qstate, QuestState):
            events.append(QuestEvent(
                tick=tick, timestamp=now, entity_id=eid,
                quest_id=qid, status="started",
                payload={"status": "started"},
            ))
        elif prior_qstate.quest_status != qstate.quest_status:
            _status_str = qstate.quest_status.name.lower()
            events.append(QuestEvent(
                tick=tick, timestamp=now, entity_id=eid,
                quest_id=qid, status=_status_str,
                payload={"status": _status_str},
            ))
    return events


def quest_events(ctx: ExtractContext, eid: int, entity: Any, prior_ent: Any) -> list[SimulationEvent]:
    """Per-project quest and abandonment events."""
    events: list[SimulationEvent] = []
    # Quest progress lifecycle events (TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG: gated to
    # real QuestState instances only — this loop previously iterated ALL strategic
    # projects of any kind, mislabeling unrelated GoalKind-typed AI strategic goals
    # (town_return, combat_engage, harvesting, etc.) as quest_event. commitment_abandoned
    # (below) is deliberately NOT gated the same way — it is a generic project-abandonment
    # classification that applies to any project kind, not quest-specific, and must keep
    # reading the generic ProjectStatus field).
    #
    # QuestEvent construction itself is flag-gated (TCK-20260807-QUEST-EVENT-PUSH-
    # MIGRATION): live behind NarrativeShaper when ENABLE_PUSH_EVENT_SHAPERS_QUEST is "ON"
    # (default); the branch below is the rollback path. commitment_abandoned stays
    # unconditional — not yet migrated (TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-
    # GAP).
    prior_projects = prior_ent.strategic.projects
    current_projects = entity.strategic.projects
    for qid, qstate in current_projects.items():
        prior_qstate = prior_projects.get(qid)
        events.extend(_quest_status_events(ctx, eid, qid, prior_qstate, qstate))
        events.extend(ctx.abandonment_events(ctx, eid, entity, qid, (prior_qstate, qstate)))
    return events
