# Compliance IDs: COMB-028, PERF-009
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Optional
from src.core.movement_modes import MovementMode

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class MovementCandidateSelector:
    """
    Authoritatively selects candidate entity IDs eligible for movement routing and spatial resolution.
    Logic ID: PERF-009 (Movement Candidate Selection)
    """

    @staticmethod
    def select(
        state: AuthoritativeState,
        update: StateUpdate,
        candidates: Iterable[int],
    ) -> tuple[int, ...]:
        selected: set[int] = set()

        dirty_movement_ids: set[int] = set()
        if update and update.dirty_set:
            dirty_movement_ids = update.dirty_set.movement_entities

        for e_id in candidates:
            entity = state.entities.get(e_id)
            if entity is None or not entity.lifecycle.active or not entity.combat.alive:
                continue

            ent_upd = update.entity_updates.get(e_id) if update else None
            if ent_upd and ent_upd.moved_this_tick:
                continue

            # Check effective target and movement mode
            nav_target = None
            mode = entity.navigation.movement_mode
            if ent_upd and ent_upd.navigation:
                if ent_upd.navigation.target_set is not None:
                    nav_target = ent_upd.navigation.target_set
                if ent_upd.navigation.movement_mode_set is not None:
                    mode = ent_upd.navigation.movement_mode_set

            if nav_target is None:
                nav_target = entity.navigation.target

            # If no target or already at target, skip unconditionally
            if nav_target is None or entity.navigation.position == nav_target:
                continue

            # In force_full_scan, include all movable entities that have target != position
            if update and update.force_full_scan:
                selected.add(e_id)
                continue

            # Explicit inclusion bypasses:
            # 1. Target changed in update
            target_changed = (ent_upd and ent_upd.navigation and ent_upd.navigation.target_set is not None)
            
            # 2. Movement dirty in dirty_set
            is_dirty = (e_id in dirty_movement_ids)

            # 3. Current tile is blocked
            tile_blocked = MovementCandidateSelector._is_static_position_blocked(state, entity.navigation.position)

            # 4. Interaction requires movement
            interaction_req = (ent_upd and ent_upd.interaction is not None) or (entity.interaction and entity.interaction.target_node_id is not None)

            # 5. Strategic project requires movement
            strategic_req = (ent_upd and ent_upd.strategic is not None) or (entity.strategic and entity.strategic.current_project_id is not None)

            if target_changed or is_dirty or tile_blocked or interaction_req or strategic_req:
                selected.add(e_id)
                continue

            # Otherwise, evaluate readiness gating and movement mode cadence
            move_cost = entity.combat.move_cost if entity.combat.move_cost > 0 else 10.0
            if entity.combat.readiness < move_cost:
                continue

            if mode == MovementMode.WANDER:
                if (state.tick + e_id) % 3 != 0:
                    continue

            selected.add(e_id)

        return tuple(sorted(selected))

    @staticmethod
    def _is_static_position_blocked(state: AuthoritativeState, pos: tuple[float, float]) -> bool:
        tile = (int(pos[0]), int(pos[1]))
        if getattr(state, "terrain", {}).get(tile) == "WALL":
            return True
        if tile in getattr(state, "blocked_tiles", set()):
            return True
        for building in getattr(state, "buildings", {}).values():
            if tuple(building.position) == tile:
                return True
        return False
