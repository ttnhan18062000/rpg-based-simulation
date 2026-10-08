# Compliance IDs: COMB-028, PERF-009, PERF-017
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Mapping, Optional
from src.core.movement_modes import MovementMode
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate
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
        if (tracked_id is None or MovementCandidateSelector.holds_action_task(entity)
                or MovementCandidateSelector._tracked_move_kind(entity) is None):
            # Only an entity-tracking move (pursuit, intercept, bracketing, kiting, guard) follows its target live; any other
            # task that merely names a target_id (an ATTACK or SKILL action, seeking cover) keeps the destination it was given.
            return fallback_target
        tracked_entity = entities.get(tracked_id)
        if tracked_entity is not None and tracked_entity.lifecycle.active and tracked_entity.combat.alive:
            return tracked_entity.navigation.position
        return fallback_target

    @staticmethod
    def holds_action_task(entity: "EntityState") -> bool:
        """True when ``entity`` is holding an action task (``ENTITY_ACT`` with a payload: ATTACK, SKILL, INTERACT, HOLD, ...).

        An entity under an action does not move because of a navigation target left behind by an earlier decision: it moves
        only on a tick that sets a target of its own. Without this an ATTACK holder kept walking onto its target's tile, and
        sidestepped off adjacency (and took an opportunity attack) every time the step was refused
        (TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP)."""
        return entity.task.work_kind == "ENTITY_ACT" and bool(entity.task.payload)

    @staticmethod
    def tracked_move_complete(entity: "EntityState", entities: Mapping[int, "EntityState"]) -> bool:
        """True when ``entity`` is on an entity-tracking move that has done its job or lost its target.

        An entity-tracking move is created by the tactical pass once and re-scheduled as movement every tick
        without re-entering the decision (docs/engine/kernel.md, the Sticky-Task Law), and arriving does not end
        it (the movement phase just stops moving), so it needs a completion condition of its own. Keyed on the
        target ENTITY's current state (``payload["target_id"]``), never on the navigation destination, which is a
        snapshot:

        * the target is dead, inactive or gone, so there is nothing left to track: left in place a live mover held
          the move for 16 to 986 ticks (measured; see the investigation of
          TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION);
        * combat positioning only (pursuit, intercept, bracketing, not kiting, which intends to hold range): the
          live target is already within the entity's attack reach, so the entity can choose ATTACK
          (TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK);
        * a group guard-obligation move only: the mover no longer shares the leader's group, so the obligation that
          created the move is gone (TCK-20261006-GROUP-GUARD-OBLIGATION-MOVE-OUTLIVES-ITS-LEADER). A leader merely
          pausing between interactions does not end it: INTERACT runs have gaps of up to 11 ticks, so that would flap.

        Which moves qualify is decided by ``_tracked_move_kind``. Other moves also carry a ``target_id`` (seeking
        cover) and keep their own lifecycle. Reach mirrors the distance part of
        ``LegalityServiceV2.verify_attack_legality`` (Manhattan, melee needs distance 1) without its weather
        multiplier; legality still arbitrates the actual attack when the brain re-decides.
        """
        kind = MovementCandidateSelector._tracked_move_kind(entity)
        tracked_id = entity.task.payload.get("target_id")
        if kind is None or tracked_id is None:
            return False
        target = entities.get(tracked_id)
        if target is None or not target.lifecycle.active or not target.combat.alive:
            return True
        if kind == "guard_obligation":
            return entity.identity.group_id is None or entity.identity.group_id != target.identity.group_id
        if kind in ("kiting", "guard_ally"):
            return False
        return MovementCandidateSelector._target_in_attack_reach(entity, target)

    @staticmethod
    def _target_in_attack_reach(entity: "EntityState", target: "EntityState") -> bool:
        ex, ey = entity.navigation.position
        tx, ty = target.navigation.position
        dist = abs(ex - tx) + abs(ey - ty)
        reach = entity.combat.range
        if dist > reach:
            return False
        return not (reach <= 1.5 and dist > 1)

    @staticmethod
    def _tracked_move_kind(entity: "EntityState") -> Optional[str]:
        """The entity-tracking kind of ``entity``'s current move, or None when it is not one.

        Keyed on (movement mode, payload reason) because the tactical pass encodes bracketing as
        ``REPOSITION`` + reason ``BRACKETING``, kiting as ``RETREAT`` + reason ``KITING``, the group guard
        obligation as ``GUARD`` + reason ``CONTRACT_OBLIGATION_GUARD`` and guarding a wounded ally as ``GUARD`` +
        reason ``GUARDING_ALLY``: the mode alone also covers cover-seeking (``REPOSITION``) and plain retreats
        (``RETREAT``), which must keep their own lifecycle."""
        mode = entity.navigation.movement_mode
        reason = entity.task.payload.get("reason")
        if mode == MovementMode.PURSUE:
            return "pursuit"
        if mode == MovementMode.INTERCEPT:
            return "intercept"
        if mode == MovementMode.REPOSITION and reason == "BRACKETING":
            return "bracketing"
        if mode == MovementMode.RETREAT and reason == "KITING":
            return "kiting"
        if mode == MovementMode.GUARD and reason == "CONTRACT_OBLIGATION_GUARD":
            return "guard_obligation"
        if mode == MovementMode.GUARD and reason == "GUARDING_ALLY":
            return "guard_ally"
        return None

    @staticmethod
    def tracked_move_completion_update(entity: "EntityState") -> EntityUpdate:
        """The update that ends a tracked combat move: back to the idle task so the brain decides next, and no
        navigation target, because movement is driven by ``navigation.target`` and would otherwise keep
        walking the entity onto its target's tile. An empty payload on ``ENTITY_ACT`` is the existing
        idle-task encoding (scheduler.py ``is_idle_act``; pipeline_phases/actions.py)."""
        return EntityUpdate(
            entity_id=entity.id,
            navigation=NavigationUpdate(target_clear=True),
            task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={}),
        )

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

            if nav_target is None and MovementCandidateSelector.holds_action_task(entity):
                continue  # an action task moves only on a tick that sets a target

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
