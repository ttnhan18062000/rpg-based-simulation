# Compliance IDs: COMB-028, PERF-009, PERF-017
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Optional
from src.core.movement_modes import MovementMode
from src.engine.phase_governor import ScanPolicy

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate


class MovementCandidateSelector:
    """
    Authoritatively selects candidate entity IDs eligible for movement routing and spatial resolution.
    Logic ID: PERF-009 (Movement Candidate Selection)
    Milestone 17 Law: Enforces candidate budget and adaptive scan policy under pressure.
    """

    # Under ScanPolicy.EXACT_DIRTY, an entity with a real, unreached navigation.target but none
    # of the 5 urgency conditions (target_changed/is_dirty/tile_blocked/interaction_req/
    # strategic_req) is admitted on this cadence rather than never at all -- see the EXACT_DIRTY
    # branch in select() (TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION). Every
    # urgency condition is change-driven; an entity that never changes never re-qualifies, which
    # without this is permanent starvation, not degraded movement. Deliberately much sparser than
    # WANDER's own cadence (3/6, see below) -- EXACT_DIRTY exists specifically because compute is
    # already over budget, so this must guarantee eventual movement while adding only a small,
    # bounded number of extra candidates per tick, not re-admit most entities and defeat the
    # policy's own work-shedding purpose.
    EXACT_DIRTY_STARVED_CADENCE_MODULO = 20

    @staticmethod
    def resolve_live_tracking_target(
        entity: "EntityState",
        entities,
        fallback_target,
    ):
        """
        Given a stale fallback nav target (typically `entity.navigation.target`, a one-time
        snapshot from whichever prior tick last issued a fresh decision), return the pursued
        entity's own CURRENT position if `entity.task.payload["target_id"]` names a still-alive
        target -- otherwise return `fallback_target` unchanged.

        `entities` is a plain `{entity_id: EntityState}` mapping (accepts `AuthoritativeState.
        entities`, `WorkerPacket.all_entities`, or any equivalent) -- deliberately NOT a full
        state/packet object, since this is the only piece either caller actually needs and it
        keeps this helper usable from both the authoritative-state call sites (movement.py,
        this file's own `select`) and the bounded, read-only `WorkerPacket` context
        (worker_logic.py) without threading a wider dependency through.

        Shared by `route_movement_intent` (movement.py), `MovementCandidateSelector.select`
        (this file), and both real `ENTITY_MOVE` work-item dispatchers
        (`executor.py`'s `LocalSequentialExecutor`/`ConcurrentExecutionAdapter`,
        `worker_logic.py`'s `default_simulation_worker`) -- all four independently computed a
        "what should this entity be moving toward" target from the same
        `entity.task.payload["target_id"]` signal. Only `route_movement_intent` was originally
        fixed to live-track it (TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE); the other three kept
        their own separate, stale-target logic, which meant (a) `select`'s own separate
        staleness check permanently excluded an "arrived at a stale snapshot" entity from
        movement candidacy before route_movement_intent's own fix ever got a chance to run for
        it, and (b) the `ENTITY_MOVE` dispatchers re-emit `NavigationUpdate(target_set=...)`
        every tick from the same frozen payload snapshot, which route_movement_intent's own
        `has_fresh_decision` check reads as "this tick has a genuine new decision" -- silently
        defeating its own live-retarget fallback, since `target_set` is always non-None even
        though its VALUE never changes (TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-
        RETARGETS). Extracted here so all four call sites can never drift out of sync again.
        """
        tracked_id = entity.task.payload.get("target_id")
        if tracked_id is None:
            return fallback_target
        tracked_entity = entities.get(tracked_id)
        if tracked_entity is not None and tracked_entity.lifecycle.active and tracked_entity.combat.alive:
            return tracked_entity.navigation.position
        return fallback_target

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
                # Live-refresh a stale entity-tracking target (see
                # resolve_live_tracking_target's own docstring) -- without this, an entity
                # that already "arrived" at a stale snapshot of its pursuit target's old
                # position gets permanently excluded from candidacy below, even though its
                # target has since moved and a fresh route_movement_intent pass would find a
                # real, legal step toward it.
                nav_target = MovementCandidateSelector.resolve_live_tracking_target(
                    entity, state.entities, entity.navigation.target
                )

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

            # Non-urgent candidate evaluation. Readiness/move-cost is a real gameplay
            # constraint, not a policy-tuning knob -- applies uniformly regardless of scan
            # policy.
            move_cost = entity.combat.move_cost if entity.combat.move_cost > 0 else 10.0
            if entity.combat.readiness < move_cost:
                continue

            if scan_policy == ScanPolicy.EXACT_DIRTY:
                # Under heavy degraded mode, most non-urgent moves are skipped to shed work --
                # but this entity is known (from the check above) to have a real, unreached
                # target, so admit it on a sparse, bounded cadence instead of never (see
                # EXACT_DIRTY_STARVED_CADENCE_MODULO's own docstring).
                if (state.tick + e_id) % MovementCandidateSelector.EXACT_DIRTY_STARVED_CADENCE_MODULO != 0:
                    continue
                normal_selected.append(e_id)
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
