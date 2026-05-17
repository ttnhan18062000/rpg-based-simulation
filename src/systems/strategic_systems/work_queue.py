# Compliance IDs: PERF-006, STRAT-PERF-001
from __future__ import annotations
from typing import Tuple, List, Set, Optional, TYPE_CHECKING
from src.core.strategic import ProjectStatus, ObjectiveStatus, ContractStatus

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate
    from src.core.dirty import DirtySet


class StrategicWorkQueue:
    """
    Decides which entities require strategic intelligence work this tick based on urgency.
    Logic ID: STRAT-PERF-001 (Consolidated O(N) pass for strategic state)
    """

    @staticmethod
    def build(
        state: AuthoritativeState,
        update: StateUpdate,
        dirty: Optional[DirtySet],
        budget: int = 50,
    ) -> Tuple[int, ...]:
        eligible_ids: List[int] = []
        for e_id in sorted(state.entities.keys()):
            entity = state.entities[e_id]
            if not entity.lifecycle.active or not entity.combat.alive:
                continue
            if entity.identity.properties.get("status_frozen") or entity.identity.properties.get("status_stunned"):
                continue
            eligible_ids.append(e_id)

        if update.force_full_scan or dirty is None:
            return tuple(eligible_ids)

        tier1: List[int] = []  # failed action/path
        tier2: List[int] = []  # unresolved blockers
        tier3: List[int] = []  # active project transition
        tier4: List[int] = []  # biological emergency
        tier5: List[int] = []  # contract expiration
        tier6: List[int] = []  # dirty strategic entities
        tier7: List[int] = []  # background sweep sample

        dirty_strat = dirty.strategic_entities if dirty else set()

        for e_id in eligible_ids:
            entity = state.entities[e_id]
            added = False

            # 1. Failed action / path
            nav_fail = entity.navigation.wait_count >= 5 or entity.navigation.oscillation_count >= 3
            intent_fail = any(not r.accepted for r in entity.identity.latest_intent_results)
            if nav_fail or intent_fail:
                tier1.append(e_id)
                added = True

            # 2. Unresolved blockers
            if not added and any(not b.resolved for b in entity.strategic.blockers.values()):
                tier2.append(e_id)
                added = True

            # 3. Active project transition
            if not added:
                curr_id = entity.strategic.current_project_id
                if curr_id:
                    proj = entity.strategic.projects.get(curr_id)
                    if proj is None or proj.status in (ProjectStatus.COMPLETED, ProjectStatus.ABANDONED):
                        tier3.append(e_id)
                        added = True
                    elif proj.status == ProjectStatus.ACTIVE:
                        obj = next((o for o in proj.objectives if o.id == proj.active_objective_id), None)
                        if obj is None or obj.status in (ObjectiveStatus.RESOLVED, ObjectiveStatus.FAILED):
                            tier3.append(e_id)
                            added = True

            # 4. Biological emergency
            if not added:
                bio = entity.biological
                stam = getattr(entity, "stamina", None)
                stam_curr = stam.current if stam else 100.0
                if bio.hunger > 80.0 or bio.sleep_debt > 80.0 or bio.rest_pressure > 80.0 or stam_curr < 20.0:
                    tier4.append(e_id)
                    added = True

            # 5. Contract expiration
            if not added and entity.strategic.contracts:
                if any(c.expiry_tick != -1 and 0 <= c.expiry_tick - state.tick <= 100 and c.status == ContractStatus.ACCEPTED for c in entity.strategic.contracts.values()):
                    tier5.append(e_id)
                    added = True

            # 6. Dirty strategic entities
            if not added and e_id in dirty_strat:
                tier6.append(e_id)
                added = True

            # 7. Background sweep
            if not added:
                tier7.append(e_id)

        # Deterministic round-robin rotation for starvation prevention in tier 7
        if tier7:
            shift = state.tick % len(tier7)
            tier7 = tier7[shift:] + tier7[:shift]

        combined: List[int] = []
        seen: Set[int] = set()

        for cur_id in (tier1 + tier2 + tier3 + tier4 + tier5 + tier6 + tier7):
            if cur_id not in seen:
                seen.add(cur_id)
                combined.append(cur_id)
                if len(combined) >= budget:
                    break

        return tuple(combined)
