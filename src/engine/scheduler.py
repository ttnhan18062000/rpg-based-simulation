# Compliance IDs: INFRA-116
from __future__ import annotations

from typing import List, Dict, Any, Sequence, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from src.core.state import AuthoritativeState
from src.core.work import WorkItem, WorkClass
from src.engine.candidate_selector import MovementCandidateSelector

# Ticks between the brain wakes of an entity beside an unengaged hostile (decision 32); the decision comes within this bound.
ADJACENCY_WAKE_COOLDOWN = 2

if TYPE_CHECKING:
    from src.core.state import EntityState
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

        policy = policy or GovernorPolicy()
        
        # M7 Law: Adaptive Level of Detail (LOD)
        # Focus points can be expanded in the future (e.g. from active regions or players)
        focus_points = [state.town_center]
        
        work_sequence: List[WorkItem] = []
        dropped_count = 0

        # Decision 32 ("notice and decide"): an entity beside a perceived hostile it is not engaged with is woken for the brain ahead of its
        # cadence, every ADJACENCY_WAKE_COOLDOWN ticks while that holds. Stateless: the wake needs only this tick's positions.
        wake_index = MovementCandidateSelector.position_index(state.entities)

        critical_items: List[WorkItem] = []
        for ent in state.entities.values():
            item = self._critical_item(ent, state, policy, focus_points, wake_index)
            if item is not None:
                critical_items.append(item)

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

    @staticmethod
    def _is_woken(ent: "EntityState", state: AuthoritativeState, work_kind: str, wake_index: Dict[Any, List[int]]) -> bool:
        """Decision 32: True when an entity that holds no action has a perceived hostile it is not engaged with orthogonally adjacent and
        this is one of its wake ticks (every ADJACENCY_WAKE_COOLDOWN ticks, staggered by id). An action holder is not interrupted."""
        return (
            (state.tick + ent.id) % ADJACENCY_WAKE_COOLDOWN == 0
            and not (work_kind == "ENTITY_ACT" and ent.task.payload)
            and MovementCandidateSelector.unengaged_adjacent_hostile(ent, state.entities, wake_index)
        )

    @staticmethod
    def _throttled(ent: "EntityState", state: AuthoritativeState, policy: "GovernorPolicy", focus_points: List[Tuple[float, float]], is_brain: bool) -> bool:
        """True when level of detail or the brain cadence keeps the entity out of this tick (a decision-32 wake is never asked: it is an event,
        not background work)."""
        from src.engine.cadence import should_run
        from src.engine.lod import LODService

        if policy.lod_enabled and not LODService.should_execute(state.tick, ent, focus_points):
            return True
        return is_brain and not should_run(state.tick, ent.id, policy.system_cadence.strategic_intelligence)

    def _critical_item(
        self, ent: "EntityState", state: AuthoritativeState, policy: "GovernorPolicy", focus_points: List[Tuple[float, float]], wake_index: Dict[Any, List[int]]
    ) -> Optional[WorkItem]:
        """The CRITICAL work item for one entity this tick, or None when it is not scheduled (inactive, readiness, LOD, brain cadence)."""
        if not ent.lifecycle.active:
            return None

        # Milestone 2: Hardened TaskComponent intent
        work_kind = ent.task.work_kind
        if work_kind not in ("ENTITY_ACT", "ENTITY_MOVE"):
            work_kind = "ENTITY_BRAIN"

        # Milestone 3: Staggered Entity Execution
        # Gating non-critical work items based on strategic cadence.
        is_idle_act = (work_kind == "ENTITY_ACT" and not ent.task.payload)
        woken = self._is_woken(ent, state, work_kind, wake_index)
        is_brain = woken or work_kind == "ENTITY_BRAIN" or is_idle_act

        # Readiness gate: thinking (brain) is free; only actual actions/movement
        # require 100.0 readiness (Action Readiness Law, COMB-266).
        if not is_brain and ent.combat.readiness < 100.0:
            return None
        if not woken and self._throttled(ent, state, policy, focus_points, is_brain):
            return None
        if is_brain:
            work_kind = "ENTITY_BRAIN"  # an idle ENTITY_ACT or a woken held move runs the brain, not a no-op action

        return WorkItem(
            owner_id=ent.id,
            work_id=f"{state.tick}:{work_kind.lower()}:{ent.id}",
            work_class=WorkClass.CRITICAL,
            work_kind=work_kind,
            payload=ent.task.payload,
            readiness=ent.combat.readiness
        )
