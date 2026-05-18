# Compliance IDs: PERF-001, PERF-017
from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Dict, Any, TYPE_CHECKING, Tuple
from src.engine.policy import GovernorPolicy

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate, EntityUpdate


@dataclass(slots=True)
class CompactionMetrics:
    raw_entity_updates: int = 0
    compacted_entity_updates: int = 0
    dropped_noop_updates: int = 0
    property_prunings: int = 0
    subcomponent_prunings: int = 0


class StateUpdateCompactor:
    """
    Filters out no-op and redundant entity updates before state application.
    Reduces memory churn and dataclass replacement overhead in ApplyPath.
    Milestone 17 Law: Supports aggressive pruning under compute pressure.
    """

    @staticmethod
    def compact(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Standard compaction entry point returning the optimized StateUpdate.
        """
        compacted, _ = StateUpdateCompactor.compact_with_metrics(state, update)
        return compacted

    @staticmethod
    def compact_with_metrics(
        state: AuthoritativeState, update: StateUpdate
    ) -> tuple[StateUpdate, CompactionMetrics]:
        """
        Compacts the StateUpdate and returns both the optimized update and detailed reduction metrics.
        """
        if not update.entity_updates:
            return update, CompactionMetrics()

        metrics = CompactionMetrics(raw_entity_updates=len(update.entity_updates))
        new_updates: Dict[int, EntityUpdate] = {}

        policy = getattr(update, "current_policy_set", None) or GovernorPolicy()
        aggressive = (policy.compaction_level == "AGGRESSIVE")

        subcomponent_names = (
            "interaction",
            "identity",
            "attributes",
            "inventory",
            "strategic",
            "biological",
            "social",
            "quest",
            "reward",
            "lifecycle",
            "combat",
            "equipment",
            "navigation",
            "task",
            "stamina_update",
            "wound_update",
        )

        for e_id, e_upd in update.entity_updates.items():
            ent = state.entities.get(e_id)
            if ent is None:
                # Entity doesn't exist in current state (e.g. newly added or invalid ID)
                if e_upd.is_noop():
                    metrics.dropped_noop_updates += 1
                else:
                    new_updates[e_id] = e_upd
                continue

            changes: Dict[str, Any] = {}

            # 1. Prune redundant top-level properties
            if e_upd.kind_set is not None and e_upd.kind_set == ent.kind:
                changes["kind_set"] = None
                metrics.property_prunings += 1

            if e_upd.active is not None and e_upd.active == ent.lifecycle.active:
                changes["active"] = None
                metrics.property_prunings += 1

            if (
                e_upd.new_position is not None
                and e_upd.new_position == ent.navigation.position
            ):
                changes["new_position"] = None
                changes["moved_this_tick"] = False
                metrics.property_prunings += 1

            # 2. Prune redundant property_updates
            if e_upd.property_updates:
                new_props = {}
                missing_sentinel = object()
                for k, v in e_upd.property_updates.items():
                    # Check getattr on entity OR properties dict on identity
                    curr_val = getattr(ent, k, missing_sentinel)
                    if curr_val is missing_sentinel:
                        if hasattr(ent, "identity") and ent.identity:
                            curr_val = ent.identity.properties.get(k, missing_sentinel)
                    if curr_val == v:
                        metrics.property_prunings += 1
                    else:
                        new_props[k] = v
                if len(new_props) != len(e_upd.property_updates):
                    changes["property_updates"] = new_props

            # Milestone 17 Aggressive Compaction Pruning
            if aggressive:
                props_dict = changes.get("property_updates", e_upd.property_updates)
                if props_dict:
                    pruned_props = {k: v for k, v in props_dict.items() if k not in ("cosmetic_fx", "chat_bubble", "last_animation")}
                    if len(pruned_props) != len(props_dict):
                        changes["property_updates"] = pruned_props
                        metrics.property_prunings += (len(props_dict) - len(pruned_props))

                if e_upd.stamina_update and abs(e_upd.stamina_update.current_delta) < 0.1 and e_upd.stamina_update.current_set is None and e_upd.stamina_update.max_stamina_set is None:
                    changes["stamina_update"] = None
                    metrics.subcomponent_prunings += 1

            # 3. Prune no-op subcomponents
            for sub_name in subcomponent_names:
                sub_val = changes.get(sub_name, getattr(e_upd, sub_name, None))
                if sub_val is not None and hasattr(sub_val, "is_noop"):
                    if sub_val.is_noop():
                        changes[sub_name] = None
                        metrics.subcomponent_prunings += 1

            # Apply changes if any
            modified_upd = replace(e_upd, **changes) if changes else e_upd

            # 4. Final check if entity update is entirely empty
            if modified_upd.is_noop():
                metrics.dropped_noop_updates += 1
            else:
                new_updates[e_id] = modified_upd

        metrics.compacted_entity_updates = len(new_updates)
        if len(new_updates) == len(update.entity_updates) and not any(
            u is not update.entity_updates[k] for k, u in new_updates.items()
        ):
            return update, metrics

        compacted_update = replace(update, entity_updates=new_updates)
        return compacted_update, metrics
