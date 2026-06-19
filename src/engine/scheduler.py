# Compliance IDs: INFRA-116
from __future__ import annotations

from typing import List, Dict, Any, Sequence, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
from src.core.state import AuthoritativeState
from src.core.work import WorkItem, WorkClass

if TYPE_CHECKING:
    from src.engine.policy import GovernorPolicy


@dataclass(frozen=True, slots=True)
class PeriodicDefinition:
    """
    Static definition for a periodic background task.
    """
    subsystem_id: str
    work_kind: str
    cadence: int
    is_authoritative: bool = True  # M5 Law: Non-auth tasks shed in SURVIVAL
    payload: Dict[str, Any] = field(default_factory=dict)


class DeterministicScheduler:
    """
    Authoritative orchestrator for deterministic work selection.
    """

    def __init__(self, periodic_defs: Sequence[PeriodicDefinition] = ()):
        self._periodic_defs = {pd.subsystem_id: pd for pd in periodic_defs}

    def select_work(
        self, 
        state: AuthoritativeState, 
        policy: Optional[GovernorPolicy] = None
    ) -> tuple[List[WorkItem], int]:
        """
        Produce a deterministic sequence of work items for the current tick.
        """
        from src.engine.policy import GovernorPolicy
        
        from src.engine.cadence import should_run
        from src.engine.lod import LODService
        
        policy = policy or GovernorPolicy()
        cadence = policy.system_cadence
        
        # M7 Law: Adaptive Level of Detail (LOD)
        # Focus points can be expanded in the future (e.g. from active regions or players)
        focus_points = [state.town_center]
        
        work_sequence: List[WorkItem] = []
        dropped_count = 0

        critical_items: List[WorkItem] = []
        for ent in state.entities.values():
            if not ent.lifecycle.active:
                continue

            # Milestone 2: Hardened TaskComponent intent
            work_kind = ent.task.work_kind
            if work_kind not in ("ENTITY_ACT", "ENTITY_MOVE"):
                work_kind = "ENTITY_BRAIN"

            # Milestone 3: Staggered Entity Execution
            # Gating non-critical work items based on strategic cadence.
            is_idle_act = (work_kind == "ENTITY_ACT" and not ent.task.payload)
            is_brain = (work_kind == "ENTITY_BRAIN" or is_idle_act)

            # Readiness gate: thinking (brain) is free; only actual actions/movement
            # require 100.0 readiness (Action Readiness Law, COMB-266).
            if not is_brain and ent.combat.readiness < 100.0:
                continue

            # Milestone 7: Level of Detail Gating
            if policy.lod_enabled:
                if not LODService.should_execute(state.tick, ent, focus_points):
                    continue

            if is_brain:
                if not should_run(state.tick, ent.id, cadence.strategic_intelligence):
                    continue
                # Idle ENTITY_ACT must run brain, not a no-op action.
                if is_idle_act:
                    work_kind = "ENTITY_BRAIN"

            critical_items.append(WorkItem(
                owner_id=ent.id,
                work_id=f"{state.tick}:{work_kind.lower()}:{ent.id}",
                work_class=WorkClass.CRITICAL,
                work_kind=work_kind,
                payload=ent.task.payload,
                readiness=ent.combat.readiness
            ))
        
        critical_items.sort(key=lambda x: (-x.readiness, x.owner_id))
        work_sequence.extend(critical_items)

        # 2. PERIODIC: Subsystem Upkeep
        periodic_items: List[WorkItem] = []
        for sid, pdef in self._periodic_defs.items():
            if not pdef.is_authoritative and not policy.allow_non_authoritative_periodic:
                dropped_count += 1
                continue
                
            due_tick = state.periodic_due_ticks.get(sid, 0)
            if state.tick >= due_tick:
                periodic_items.append(WorkItem(
                    owner_id=sid,
                    work_id=f"{state.tick}:periodic:{sid}",
                    work_class=WorkClass.PERIODIC,
                    work_kind=pdef.work_kind,
                    payload=pdef.payload,
                    due_tick=due_tick,
                    cadence=pdef.cadence
                ))
        
        periodic_items.sort(key=lambda x: (x.due_tick, x.owner_id))
        work_sequence.extend(periodic_items)

        # 3. DEFERRED: Drain postponed authoritative work
        deferred_items: List[WorkItem] = []
        for d_id, debt_count in state.work_debt.items():
            if debt_count > 0:
                deferred_items.append(WorkItem(
                    owner_id=d_id,
                    work_id=f"{state.tick}:deferred:{d_id}",
                    work_class=WorkClass.DEFERRED,
                    work_kind="DRAIN_DEBT",
                    due_tick=state.tick
                ))
        
        deferred_items.sort(key=lambda x: x.owner_id)
        work_sequence.extend(deferred_items)

        # 4. OPPORTUNISTIC: Optional Enrichment
        if policy.allow_opportunistic:
            pass
        
        return work_sequence, dropped_count
