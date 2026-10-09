# Compliance IDs: INFRA-116
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from src.core.state import AuthoritativeState
from src.core.work import WorkItem, WorkClass
from src.engine.appraisal import HUNT_HUNGER, can_eat_item
from src.engine.candidate_selector import MovementCandidateSelector
from src.engine.cadence import SystemCadence, should_run
from src.engine.need_pull import need_is_pressing
from src.engine.tactical_rest import CARCASS_NEAR

# Ticks between the brain wakes of an entity beside an unengaged hostile (decision 32); the decision comes within this bound.
ADJACENCY_WAKE_COOLDOWN = 2

# Ticks between the brain wakes of a holder of a move while a need is pressing: the strategic cadence, the rate at which an idle
# entity already decides, so a held mover is no slower to decide than an idle one.
NEED_WAKE_CADENCE: int = SystemCadence.model_fields["strategic_intelligence"].default

if TYPE_CHECKING:
    from src.core.state import EntityState
    from src.engine.policy import GovernorPolicy


class DeterministicScheduler:
    """
    Authoritative orchestrator for deterministic work selection.
    """

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

        # Nothing in this scheduler sheds work, so the dropped count is always 0 (kept so the kernel's accounting reads one place).
        return work_sequence, 0

    @staticmethod
    def _is_need_woken(ent: "EntityState", state: AuthoritativeState, work_kind: str) -> bool:
        """SURV-07 / decision 32 for a need: an entity holding a move while a biological need is pressing is woken for the brain on
        the strategic cadence (staggered by id), so the hunger or sleep goal it already ranks first can displace the held move.
        Waking is only a re-decision: a present threat to life (the only thing that outranks a pressing need, SURV-07) is seen again by
        that decision and re-issues the flight, so a held flight is woken too; one whose threat is gone (a retreat that never completes)
        is no longer held."""
        return (
            work_kind == "ENTITY_MOVE"
            and need_is_pressing(ent.biological.hunger, ent.biological.sleep_debt)
            and should_run(state.tick, ent.id, NEED_WAKE_CADENCE)
        )

    @staticmethod
    def _is_woken(ent: "EntityState", state: AuthoritativeState, work_kind: str, wake_index: Dict[Any, List[int]]) -> bool:
        """Decision 32: True when an entity that holds no action has a perceived hostile it is not engaged with orthogonally adjacent and
        this is one of its wake ticks (every ADJACENCY_WAKE_COOLDOWN ticks, staggered by id). An action holder is not interrupted."""
        return (
            (state.tick + ent.id) % ADJACENCY_WAKE_COOLDOWN == 0
            and not (work_kind == "ENTITY_ACT" and ent.task.payload)
            and (MovementCandidateSelector.unengaged_adjacent_hostile(ent, state.entities, wake_index)
                 or DeterministicScheduler._hungry_beside_edible_carcass(ent, state))
        )

    @staticmethod
    def _hungry_beside_edible_carcass(ent: "EntityState", state: AuthoritativeState) -> bool:
        """Decision 44: a hungry entity that holds no action and stands within CARCASS_NEAR of a carcass its diet can eat is woken for the brain, so
        a kill leads to the meal (the held swing at a dead target ends several ticks after the kill, and the body may have drifted a tile since)."""
        if not state.corpses or ent.biological.hunger < HUNT_HUNGER:
            return False
        px, py = ent.navigation.position
        return any(abs(px - c.position[0]) + abs(py - c.position[1]) <= CARCASS_NEAR
                   and any(i.quantity > 0 and can_eat_item(ent, i.item_id) for i in c.items) for c in state.corpses.values())

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
        woken = self._is_woken(ent, state, work_kind, wake_index) or self._is_need_woken(ent, state, work_kind)
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
