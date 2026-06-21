from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate
    from src.observability.events import LeadershipChangedEvent


class GroupPhase:
    """
    Pipeline phase responsible for coordinating group formation, updates, and removals.

    Also runs PartyLifecycleService leadership elections each tick (E41B).
    """

    # Accumulated leadership events from the most recent resolve() call.
    # Cleared at the start of every resolve() call. Used by tests and by the
    # kernel's _event_listeners dispatch chain.
    last_tick_events: List["LeadershipChangedEvent"] = []

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src.systems.world_systems.groups import GroupSystem
        from src.systems.social_systems.party_lifecycle import PartyLifecycleService
        from src.core.updates import EntityUpdate

        # Clear per-tick event buffer
        GroupPhase.last_tick_events = []

        # Optimization: Pass state and update directly, let GroupSystem handle sliding positions
        group_update = GroupSystem.update_groups(state, update)

        # Merge group additions/updates
        new_groups_add = list(update.groups_add_or_update)
        group_ids = {g.id for g in new_groups_add}

        for g in group_update.groups_add_or_update:
            if g.id in group_ids:
                new_groups_add = [
                    existing if existing.id != g.id else g
                    for existing in new_groups_add
                ]
            else:
                new_groups_add.append(g)

        # Merge group removals
        new_groups_remove = list(
            set(list(update.groups_remove) + list(group_update.groups_remove))
        )

        # --- E41B: Leadership election pass ---
        # Run over all surviving groups (those not being removed this tick).
        removed_ids = set(new_groups_remove)
        tick = state.tick

        # Build a combined view: groups already in state PLUS groups being added/updated
        groups_being_updated = {g.id: g for g in new_groups_add}
        all_relevant_group_ids = (
            set(state.groups.keys()) | set(groups_being_updated.keys())
        ) - removed_ids

        for g_id in sorted(all_relevant_group_ids):
            group = groups_being_updated.get(g_id) or state.groups.get(g_id)
            if group is None:
                continue

            # Collect live members from state.entities for sociability scoring
            members = [
                state.entities[m_id]
                for m_id in group.member_ids
                if m_id in state.entities
            ]

            updated_group, event = PartyLifecycleService.check_leadership(
                group, members, tick
            )

            if updated_group is not None:
                # Replace (or insert) the group in the accumulated list
                replaced = False
                for i, existing in enumerate(new_groups_add):
                    if existing.id == g_id:
                        new_groups_add[i] = updated_group
                        replaced = True
                        break
                if not replaced:
                    new_groups_add.append(updated_group)

            if event is not None:
                GroupPhase.last_tick_events.append(event)

        # Merge side-effect entity updates from group logic (e.g. leadership changes)
        refined_entity_updates = dict(update.entity_updates)
        for eid, eupd in group_update.entity_updates.items():
            existing = refined_entity_updates.get(eid, EntityUpdate(entity_id=eid))
            refined_entity_updates[eid] = existing.merge(eupd)

        return replace(
            update,
            groups_add_or_update=new_groups_add,
            groups_remove=new_groups_remove,
            entity_updates=refined_entity_updates,
        )
