# Compliance IDs: COMB-028, PERF-009, PERF-017
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Optional
from src.core.movement_modes import MovementMode
from src.engine.phase_governor import ScanPolicy

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate


class MovementCandidateSelector:
    """
    Authoritatively selects candidate entity IDs eligible for movement routing and spatial resolution.
    Logic ID: PERF-009 (Movement Candidate Selection)
    Milestone 17 Law: Enforces candidate budget and adaptive scan policy under pressure.
    """

    @staticmethod
    def select(
        state: AuthoritativeState,
        update: StateUpdate,
        candidates: Iterable[int],
        budget: int = 1000,
        scan_policy: ScanPolicy = ScanPolicy.FULL,
    ) -> tuple[int, ...]:
        urgent_selected: set[int] = set()
        normal_selected: list[int] = []

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

            # In force_full_scan, include all movable entities that have target != position as urgent
            if update and update.force_full_scan:
                urgent_selected.add(e_id)
                continue

            # Explicit inclusion bypasses (Urgent / Dirty work):
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
                urgent_selected.add(e_id)
                continue

            # Non-urgent candidate evaluation:
            if scan_policy == ScanPolicy.EXACT_DIRTY:
                # Under heavy degraded mode, skip non-urgent moves entirely
                continue

            # Otherwise, evaluate readiness gating and movement mode cadence
            move_cost = entity.combat.move_cost if entity.combat.move_cost > 0 else 10.0
            if entity.combat.readiness < move_cost:
                continue

            if mode == MovementMode.WANDER:
                modulo = 6 if scan_policy == ScanPolicy.THROTTLED else 3
                if (state.tick + e_id) % modulo != 0:
                    continue

            normal_selected.append(e_id)

        # Enforce budget while protecting urgent candidates
        if len(urgent_selected) + len(normal_selected) <= budget:
            final_set = urgent_selected.union(normal_selected)
        else:
            rem = max(0, budget - len(urgent_selected))
            final_set = urgent_selected.union(normal_selected[:rem])

        return tuple(sorted(final_set))

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
