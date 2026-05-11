from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate

class GroupPhase:
    """
    Pipeline phase responsible for coordinating group formation, updates, and removals.
    """
    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src.engine.apply import ApplyPath
        from src.systems.world_systems.groups import GroupSystem
        from src.core.updates import EntityUpdate

        # Calculate group updates based on the current tick's generation (sliding state)
        working_state = ApplyPath.apply_generation(state, update)
        group_update = GroupSystem.update_groups(working_state, update)

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
