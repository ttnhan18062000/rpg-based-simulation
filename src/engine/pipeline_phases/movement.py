# Compliance IDs: COMB-028, COMB-046, COMB-047, COMB-048
from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from src.core.enums import ReasonCode
from src.core.movement_modes import MovementMode
from src.core.strategic import ContractKind, ContractStatus
from src.core.updates import (
    EntityUpdate,
    NavigationUpdate,
    StrategicUpdate,
    StaminaUpdate,
)
from src.engine.movement import MovementSystem
from src.engine.policy import GovernorPolicy

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate


class MovementPhase:
    """
    Resolves position swap and movement routing.
    """

    @staticmethod
    def resolve_position_swaps(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        """
        Resolve adjacent position swaps before normal movement routing.

        LAW:
            Two adjacent entities may exchange positions atomically when either:

                1. Mutual same-tick intent exists:
                    A's next step is B's current tile, and
                    B's next step is A's current tile.

                2. A valid accepted/active POSITION_SWAP contract exists:
                    One side wants the other side's tile, and the other side has
                    accepted a short-lived swap contract.
        """
        refined_entity_updates = dict(update.entity_updates)
        consumed_entities: set[int] = set()

        from src.engine.spatial_query import SpatialQueryService
        occ_map = SpatialQueryService.get_occupancy_map(state)

        next_step_cache = {}
        def get_next_step(ent):
            if ent.id not in next_step_cache:
                next_step_cache[ent.id] = MovementPhase._desired_next_step_for_swap(state, update, ent)
            return next_step_cache[ent.id]

        for a_id, a in state.entities.items():
            if a_id in consumed_entities:
                continue

            # Performance Optimization: Skip entities that are definitely not moving
            # (No target in state AND no navigation update this tick)
            ent_upd = refined_entity_updates.get(a_id)
            has_nav_upd = ent_upd and ent_upd.navigation and (ent_upd.navigation.target_set or ent_upd.navigation.path_set)
            if not a.navigation.target and not has_nav_upd:
                continue
            
            # Skip inactive/dead entities
            if not a.lifecycle.active or not a.combat.alive:
                continue

            a_next = get_next_step(a)
            if a_next is None:
                continue

            # Performance Optimization: The only entity 'a' could swap with is whoever currently occupies a_next
            b_id = occ_map.get((int(a_next[0]), int(a_next[1])))
            if b_id is None or b_id == a_id or b_id in consumed_entities:
                continue

            b = state.entities.get(b_id)
            if b is None:
                continue
                
            # Double check adjacency (Manhattan distance 1)
            a_pos = a.navigation.position
            b_pos = b.navigation.position
            dist = abs(a_pos[0] - b_pos[0]) + abs(a_pos[1] - b_pos[1])
            if dist != 1:
                continue

            if not MovementPhase._can_attempt_position_swap_pair(
                state,
                a,
                b,
            ):
                continue

            a_old = a.navigation.position
            b_old = b.navigation.position

            b_next = get_next_step(b)

            mutual_swap = (
                a_next == b_old
                and b_next == a_old
            )

            active_contract = None

            if not mutual_swap:
                if a_next == b_old:
                    active_contract = MovementPhase._find_valid_position_swap_contract(
                        state=state,
                        requester_id=a_id,
                        responder_id=b_id,
                    )
                elif b_next == a_old:
                    active_contract = MovementPhase._find_valid_position_swap_contract(
                        state=state,
                        requester_id=b_id,
                        responder_id=a_id,
                    )

            if not mutual_swap and active_contract is None:
                continue

            if not MovementPhase._position_swap_destinations_are_safe(
                state,
                a_old,
                b_old,
            ):
                continue

            # Apply atomic swap.
            a_existing = refined_entity_updates.get(
                a_id,
                EntityUpdate(entity_id=a_id),
            )
            b_existing = refined_entity_updates.get(
                b_id,
                EntityUpdate(entity_id=b_id),
            )

            a_swap = MovementPhase._build_position_swap_entity_update(
                entity=a,
                new_position=b_old,
                reason=ReasonCode.POSITION_SWAP,
            )

            b_swap = MovementPhase._build_position_swap_entity_update(
                entity=b,
                new_position=a_old,
                reason=ReasonCode.POSITION_SWAP,
            )

            refined_entity_updates[a_id] = a_existing.merge(a_swap)
            refined_entity_updates[b_id] = b_existing.merge(b_swap)

            if active_contract is not None:
                MovementPhase._mark_position_swap_contract_fulfilled(
                    refined_entity_updates,
                    active_contract,
                )

            consumed_entities.add(a_id)
            consumed_entities.add(b_id)

        return replace(
            update,
            entity_updates=refined_entity_updates,
        )

    @staticmethod
    def route_movement_intent(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        """
        Route normal navigation intent via MovementSystem.
        Optimized v3: reduced dictionary copies and avoided sorted() overhead.
        """
        # Start with entity_updates already present in the update
        refined_entity_updates = dict(update.entity_updates)
        new_rejections_delta = dict(update.rejections_delta)
        
        from src.engine.spatial_query import SpatialQueryService
        live_occ_map = dict(SpatialQueryService.get_occupancy_map(state))
        live_claims = set()
        
        # Populate live claims with already updated positions from prior phases or Pass 0
        for ent_upd in refined_entity_updates.values():
            if ent_upd.new_position is not None:
                u_ent = state.entities.get(ent_upd.entity_id)
                if u_ent:
                    old_pos = (int(u_ent.navigation.position[0]), int(u_ent.navigation.position[1]))
                    if old_pos in live_occ_map and live_occ_map[old_pos] == ent_upd.entity_id:
                        del live_occ_map[old_pos]
                new_pos = (int(ent_upd.new_position[0]), int(ent_upd.new_position[1]))
                live_claims.add(new_pos)
                live_occ_map[new_pos] = ent_upd.entity_id

        object.__setattr__(state, "_occupancy_map_cache", live_occ_map)
        object.__setattr__(state, "transient_claims", live_claims)
        
        from src.engine.candidate_selector import MovementCandidateSelector
        policy = getattr(update, "current_policy_set", None) or GovernorPolicy()
        selected_ids = MovementCandidateSelector.select(
            state, update, state.entities.keys(), 
            budget=policy.movement_budget, 
            scan_policy=policy.scan_policy
        )
        
        # Record candidate count for observability
        sub_costs = dict(update.sub_phase_costs) if getattr(update, "sub_phase_costs", None) is not None else {}
        metric_counters = dict(update.metric_counters) if getattr(update, "metric_counters", None) is not None else {}
        metric_counters["movement_candidates"] = len(selected_ids)
        
        # Unified Pass over selected candidate IDs
        for e_id in selected_ids:
            ent_upd = refined_entity_updates.get(e_id)
            entity = state.entities.get(e_id)
            if not entity or not entity.lifecycle.active:
                continue
            
            # Already moved by a prior phase or position swap?
            if ent_upd and ent_upd.moved_this_tick:
                continue
                
            # Determine target and mode (prefer update if present)
            has_fresh_decision = bool(ent_upd and ent_upd.navigation and ent_upd.navigation.target_set is not None)
            nav_target = ent_upd.navigation.target_set if has_fresh_decision else entity.navigation.target

            # Live-refresh a stale entity-tracking target (TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE):
            # when this tick has no fresh brain decision, nav_target is a static snapshot from
            # whichever prior tick's decision last set it -- correct for a fixed-point errand
            # (WANDER/RETREAT/objective pursuit, none of which set task.payload["target_id"]) but
            # stale for a real entity-tracking mode (PURSUE/INTERCEPT/KITING/BRACKETING/
            # GUARDING_ALLY), all of which do set target_id. Tactical decisions are cadence-gated
            # to once per ~10 ticks (scheduler.py's own strategic_intelligence cadence) while
            # movement itself runs every tick, so a pursuer previously walked straight to a
            # snapshot of where its target *was*, arrived, and then idled until its next cadence
            # tick while the real target kept moving -- confirmed via live per-tick trace to be
            # the real, precise reason chase convergence was rare rather than reliable.
            #
            # Shared with MovementCandidateSelector.select's own, separately-computed nav_target
            # (TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS) -- that function
            # runs BEFORE this loop to decide which entities are even offered a chance to move,
            # and its own un-refreshed staleness check was silently excluding an "arrived at a
            # stale snapshot" entity from candidacy entirely, before this already-correct live
            # retarget ever got a chance to run for it.
            if not has_fresh_decision:
                nav_target = MovementCandidateSelector.resolve_live_tracking_target(
                    entity, state.entities, nav_target
                )

            if not nav_target or entity.navigation.position == nav_target:
                continue

            mode = ent_upd.navigation.movement_mode_set if (ent_upd and ent_upd.navigation and ent_upd.navigation.movement_mode_set is not None) else entity.navigation.movement_mode
            
            move_updates = MovementSystem.resolve_move(state, entity, nav_target, mode=mode)
            for u_id, u_upd in move_updates.items():
                existing = refined_entity_updates.get(u_id)
                if existing is not None and existing.new_position is not None and u_upd.new_position is not None:
                    prev_new_pos = (int(existing.new_position[0]), int(existing.new_position[1]))
                    next_new_pos = (int(u_upd.new_position[0]), int(u_upd.new_position[1]))
                    if prev_new_pos != next_new_pos:
                        if prev_new_pos in live_occ_map and live_occ_map[prev_new_pos] == u_id:
                            del live_occ_map[prev_new_pos]
                        if prev_new_pos in live_claims:
                            live_claims.discard(prev_new_pos)

                if existing is not None:
                    refined_entity_updates[u_id] = existing.merge(u_upd)
                else:
                    refined_entity_updates[u_id] = u_upd
                    
                if u_upd.new_position is not None:
                    u_ent = state.entities.get(u_id)
                    if u_ent:
                        old_pos = (int(u_ent.navigation.position[0]), int(u_ent.navigation.position[1]))
                        if old_pos in live_occ_map and live_occ_map[old_pos] == u_id:
                            del live_occ_map[old_pos]
                    new_pos = (int(u_upd.new_position[0]), int(u_upd.new_position[1]))
                    live_occ_map[new_pos] = u_id
                    live_claims.add(new_pos)
                
                # Record rejections
                if u_upd.navigation and u_upd.navigation.failure_reason:
                    reason_key = u_upd.navigation.failure_reason.value if hasattr(u_upd.navigation.failure_reason, "value") else str(u_upd.navigation.failure_reason)
                    new_rejections_delta[reason_key] = new_rejections_delta.get(reason_key, 0) + 1

        try:
            object.__setattr__(state, "_occupancy_map_cache", live_occ_map)
            object.__setattr__(state, "transient_claims", live_claims)
        except AttributeError:
            pass
            
        return replace(update, entity_updates=refined_entity_updates, rejections_delta=new_rejections_delta, sub_phase_costs=sub_costs, metric_counters=metric_counters)

    # --- Helpers ---

    @staticmethod
    def _can_attempt_position_swap_pair(
        state: AuthoritativeState,
        a: EntityState,
        b: EntityState,
    ) -> bool:
        if not a.lifecycle.active or not b.lifecycle.active:
            return False
        if not a.combat.alive or not b.combat.alive:
            return False
        if a.navigation.movement_mode == MovementMode.HOLD:
            return False
        if b.navigation.movement_mode == MovementMode.HOLD:
            return False
        a_pos = a.navigation.position
        b_pos = b.navigation.position
        dist = abs(a_pos[0] - b_pos[0]) + abs(a_pos[1] - b_pos[1])
        return dist == 1

    @staticmethod
    def _desired_next_step_for_swap(
        state: AuthoritativeState,
        update: StateUpdate,
        entity: EntityState,
    ) -> tuple[float, float] | None:
        ent_upd = update.entity_updates.get(entity.id)
        if ent_upd and ent_upd.new_position is not None:
            return tuple(ent_upd.new_position)
        target_pos = None
        if ent_upd and ent_upd.navigation and ent_upd.navigation.target_set is not None:
            target_pos = ent_upd.navigation.target_set
        if target_pos is None and ent_upd and ent_upd.task and ent_upd.task.payload_set:
            payload = ent_upd.task.payload_set
            if "target_position" in payload:
                target_pos = payload["target_position"]
        if target_pos is None:
            target_pos = entity.navigation.target
        if target_pos is None:
            return None
        return MovementPhase._next_manhattan_step(
            entity.navigation.position,
            tuple(target_pos),
        )

    @staticmethod
    def _next_manhattan_step(
        current_pos: tuple[float, float],
        target_pos: tuple[float, float],
    ) -> tuple[float, float] | None:
        if current_pos == target_pos:
            return None
        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]
        if abs(dx) + abs(dy) <= 1:
            return target_pos
        if abs(dx) > abs(dy):
            return (
                current_pos[0] + (1.0 if dx > 0 else -1.0),
                current_pos[1],
            )
        return (
            current_pos[0],
            current_pos[1] + (1.0 if dy > 0 else -1.0),
        )

    @staticmethod
    def _find_valid_position_swap_contract(
        state: AuthoritativeState,
        requester_id: int,
        responder_id: int,
    ):
        requester = state.entities.get(requester_id)
        responder = state.entities.get(responder_id)
        if requester is None or responder is None:
            return None
        candidates = []
        for owner in (requester, responder):
            candidates.extend(owner.strategic.contracts.values())
        for contract in candidates:
            if contract.kind != ContractKind.POSITION_SWAP:
                continue
            if contract.status not in (ContractStatus.ACCEPTED, ContractStatus.ACTIVE):
                continue
            if contract.expiry_tick != -1 and state.tick > contract.expiry_tick:
                continue
            contract_pair = {contract.source_id, contract.target_id}
            if contract_pair != {requester_id, responder_id}:
                continue
            if not MovementPhase._position_swap_contract_terms_match(state, contract):
                continue
            return contract
        return None

    @staticmethod
    def _position_swap_contract_terms_match(state: AuthoritativeState, contract) -> bool:
        source = state.entities.get(contract.source_id)
        target = state.entities.get(contract.target_id)
        if source is None or target is None:
            return False
        expected = {
            "source_from": source.navigation.position,
            "source_to": target.navigation.position,
            "target_from": target.navigation.position,
            "target_to": source.navigation.position,
        }
        for key, expected_pos in expected.items():
            if key not in contract.terms:
                continue
            actual_pos = tuple(contract.terms[key])
            if actual_pos != expected_pos:
                return False
        return True

    @staticmethod
    def _position_swap_destinations_are_safe(
        state: AuthoritativeState,
        a_old: tuple[float, float],
        b_old: tuple[float, float],
    ) -> bool:
        return (
            not MovementPhase._is_static_position_blocked(state, a_old)
            and not MovementPhase._is_static_position_blocked(state, b_old)
        )

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

    @staticmethod
    def _build_position_swap_entity_update(
        entity: EntityState,
        new_position: tuple[float, float],
        reason,
    ) -> EntityUpdate:
        # Movement no longer costs readiness -- see the matching note in
        # MovementSystem.resolve_move (src/engine/movement.py)
        # (TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE). Stamina (below) already
        # covers movement fatigue.
        return EntityUpdate(
            entity_id=entity.id,
            new_position=new_position,
            moved_this_tick=True,
            navigation=NavigationUpdate(
                moved_recently_set=True,
                failure_reason=reason,
                wait_count_delta=-entity.navigation.wait_count,
                oscillation_count_delta=-entity.navigation.oscillation_count,
                last_position_set=entity.navigation.position,
                clear_path=True,
            ),
            stamina_update=StaminaUpdate(
                current_delta=-entity.stamina.MOVE_COST,
            ),
            property_updates={
                "movement_resolution": "POSITION_SWAP",
            },
        )

    @staticmethod
    def _mark_position_swap_contract_fulfilled(
        refined_entity_updates: dict[int, EntityUpdate],
        contract,
    ) -> None:
        fulfilled_contract = replace(
            contract,
            status=ContractStatus.FULFILLED,
        )
        for entity_id in (contract.source_id, contract.target_id):
            existing = refined_entity_updates.get(
                entity_id,
                EntityUpdate(entity_id=entity_id),
            )
            current_strategic = existing.strategic or StrategicUpdate()
            contract_update = StrategicUpdate(
                contracts_add_or_update=[fulfilled_contract],
            )
            refined_entity_updates[entity_id] = replace(
                existing,
                strategic=current_strategic.merge(contract_update),
            )
