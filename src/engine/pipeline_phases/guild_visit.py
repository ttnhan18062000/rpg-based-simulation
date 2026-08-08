from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from src.core.strategic import ObjectiveStatus, ProjectStatus
from src.core.updates import EntityUpdate, StrategicUpdate
from src.town.guild import GuildAction

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class GuildVisitPhase:
    """Detects entities that have arrived at their guild-visit target building and completes the
    visit via GuildAction.visit() (TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING).

    Runs as a dedicated authoritative-pipeline phase — NOT an ENTITY_ACT/ActionRouter dispatch —
    because GuildAction.visit() needs full state access (state.regions/state.resource_nodes for
    QuestPressureProfile/lead generation) that the concurrent-worker ENTITY_ACT path's
    WorkerPacket structurally cannot provide ("Law: A worker must receive a compact, bounded, and
    read-only context", src/core/worker_protocol.py:22). Mirrors QuestRewardPhase's own shape
    (resolve(state, update) -> StateUpdate) and _resolve_active_objective's own "detour"
    arrival-check pattern (src/systems/strategic_systems/intelligence.py:1017-1056) — an
    independent, phase-local arrival detection, not dependent on tactical.py's own per-tick
    dispatch (which is left untouched: for a "guild" project kind it correctly no-ops, since
    movement toward a real int-castable building ID already works via the existing
    _resolve_target_position, and this phase is what completes the visit once arrived).

    Gated behind ENABLE_GUILD_QUEST_GENERATION (checked directly via state.feature_flags,
    matching this session's own established observability-flag-read convention) as a second,
    independent gate alongside GuildNeedScorer's own internal check — belt-and-suspenders so a
    stale kind=="guild" project from before a flag flip can't silently complete.
    """

    @staticmethod
    def resolve(state: "AuthoritativeState", update: "StateUpdate") -> "StateUpdate":
        flags = getattr(state, "feature_flags", None) or {}
        if flags.get("ENABLE_GUILD_QUEST_GENERATION", "OFF") != "ON":
            return update

        refined_entity_updates = dict(update.entity_updates)

        for eid, entity in state.entities.items():
            if not entity.lifecycle.active or not entity.combat.alive:
                continue

            strat = entity.strategic
            proj_id = strat.current_project_id
            if not proj_id:
                continue

            project = strat.projects.get(proj_id)
            if not project or project.kind != "guild" or project.status != ProjectStatus.ACTIVE:
                continue

            obj = next((o for o in project.objectives if o.id == project.active_objective_id), None)
            if not obj or obj.status != ObjectiveStatus.ACTIVE or not obj.target:
                continue

            try:
                building_id = int(obj.target)
            except (TypeError, ValueError):
                continue

            building = state.buildings.get(building_id)
            if not building:
                continue

            dist = (
                abs(entity.navigation.position[0] - building.position[0])
                + abs(entity.navigation.position[1] - building.position[1])
            )
            if dist > 1.0:
                continue  # still en route — tactical.py's own movement handles this

            visit_update = GuildAction.visit(entity, state)

            resolved_obj = replace(obj, status=ObjectiveStatus.RESOLVED)
            completed_project = replace(
                project, objectives=[resolved_obj], status=ProjectStatus.COMPLETED,
            )
            completion_upd = EntityUpdate(
                entity_id=eid,
                strategic=StrategicUpdate(
                    projects_add_or_update=[completed_project],
                    current_project_id_set="",
                    current_objective_id_set="",
                ),
            )

            merged = completion_upd
            if visit_update and eid in visit_update.entity_updates:
                merged = merged.merge(visit_update.entity_updates[eid])

            existing = refined_entity_updates.get(eid)
            refined_entity_updates[eid] = existing.merge(merged) if existing else merged

        return replace(update, entity_updates=refined_entity_updates)
