from __future__ import annotations

from typing import List, Dict, Any, Sequence, Optional
from dataclasses import dataclass, field
from src_v2.core.state import AuthoritativeState
from src_v2.core.work import WorkItem, WorkClass


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
    Bucketizes work and applies class-local ordering rules.
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
        Law: Critical (Entities) -> Periodic -> Opportunistic.
        Returns: (WorkItems, DroppedCount)
        """
        from src_v2.engine.policy import GovernorPolicy
        
        policy = policy or GovernorPolicy()
        work_sequence: List[WorkItem] = []
        dropped_count = 0

        # 1. CRITICAL: Entity Actions (Non-degradable)
        critical_items: List[WorkItem] = []
        for ent in state.entities.values():
            if ent.readiness >= 100.0:
                critical_items.append(WorkItem(
                    owner_id=ent.id,
                    work_class=WorkClass.CRITICAL,
                    work_kind="ENTITY_ACT",
                    readiness=ent.readiness
                ))
        
        critical_items.sort(key=lambda x: (-x.readiness, x.owner_id))
        work_sequence.extend(critical_items)

        # 2. PERIODIC: Subsystem Upkeep
        periodic_items: List[WorkItem] = []
        for sid, pdef in self._periodic_defs.items():
            # M5 Law: Non-authoritative periodic work is shed in SURVIVAL
            if not pdef.is_authoritative and not policy.allow_non_authoritative_periodic:
                dropped_count += 1
                continue
                
            due_tick = state.periodic_due_ticks.get(sid, 0)
            if state.tick >= due_tick:
                periodic_items.append(WorkItem(
                    owner_id=sid,
                    work_class=WorkClass.PERIODIC,
                    work_kind=pdef.work_kind,
                    payload=pdef.payload,
                    due_tick=due_tick,
                    cadence=pdef.cadence
                ))
        
        periodic_items.sort(key=lambda x: (x.due_tick, x.owner_id))
        work_sequence.extend(periodic_items)

        # 3. DEFERRED: Drain postponed authoritative work (Non-degradable)
        deferred_items: List[WorkItem] = []
        for d_id, debt_count in state.work_debt.items():
            if debt_count > 0:
                deferred_items.append(WorkItem(
                    owner_id=d_id,
                    work_class=WorkClass.DEFERRED,
                    work_kind="DRAIN_DEBT",
                    due_tick=state.tick
                ))
        
        deferred_items.sort(key=lambda x: x.owner_id)
        work_sequence.extend(deferred_items)

        # 4. OPPORTUNISTIC: Optional Enrichment
        if policy.allow_opportunistic:
            # Placeholder for future opportunitistic work injection
            pass
        else:
            # If we had opportunistic work to inject, we would count it as dropped here.
            pass

        return work_sequence, dropped_count
