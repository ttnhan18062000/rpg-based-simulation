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

        from src.engine.domain.view import DomainView
        grid = DomainView._get_cached_spatial_grid(state)

        for a_id, a in state.entities.items():
            if a_id in consumed_entities:
                continue

            # Performance Optimization: Skip entities that are definitely not moving
            # (No target in state AND no navigation update this tick)
            ent_upd = refined_entity_updates.get(a_id)
            has_nav_upd = ent_upd and ent_upd.navigation and (ent_upd.navigation.target_set or ent_upd.navigation.path_set)
            if not a.navigation.target and not has_nav_upd:
                continue

            # Only entities that MIGHT want to move or have a swap contract are relevant.
            # But simpler to just check neighbors within distance 1.0.
            neighbor_ids = grid.get_neighbors(a.navigation.position, 1.1)
            
            for b_id in neighbor_ids:
                if b_id == a_id or b_id in consumed_entities:
                    continue

                b = state.entities[b_id]
                
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

                a_next = MovementPhase._desired_next_step_for_swap(
                    state,
                    update,
                    a,
                )
                b_next = MovementPhase._desired_next_step_for_swap(
                    state,
                    update,
                    b,
                )

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
                # Break inner loop for entity 'a' since it has swapped.
                break

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
        Optimized v2: reduced overhead for stationary entities.
        """
        refined_entity_updates = dict(update.entity_updates)
        
        # Primary pass: entities with updates this tick.
        for e_id, ent_upd in list(refined_entity_updates.items()):
            entity = state.entities.get(e_id)
            if not entity: continue
            
            nav_target = ent_upd.navigation.target_set if (ent_upd.navigation and ent_upd.navigation.target_set is not None) else entity.navigation.target
            if not nav_target: continue
            
            # Already moved?
            if ent_upd.moved_this_tick:
                continue
                
            if entity.navigation.position != nav_target:
                mode = ent_upd.navigation.movement_mode_set if (ent_upd.navigation and ent_upd.navigation.movement_mode_set is not None) else entity.navigation.movement_mode
                move_updates = MovementSystem.resolve_move(state, entity, nav_target, mode=mode)
                for u_id, u_upd in move_updates.items():
                    if u_id == e_id:
                        refined_entity_updates[e_id] = ent_upd.merge(u_upd)
                    else:
                        neighbor_upd = refined_entity_updates.get(u_id, EntityUpdate(entity_id=u_id))
                        refined_entity_updates[u_id] = neighbor_upd.merge(u_upd)

        # Secondary pass: entities that didn't have updates this tick but HAVE a target in state.
        # This is rare but possible if they were already moving.
        # But in IDLE_1000, most have a target but are already at it.
        # To avoid O(N) over ALL entities, we could skip this if the target is already reached.
        # For now, let's just make it faster by checking position vs target early.
        
        for e_id in sorted(state.entities.keys()):
            entity = state.entities[e_id]
            if e_id in refined_entity_updates: continue
            if not entity.navigation.target: continue
            if entity.navigation.position == entity.navigation.target: continue
            
            # This entity wants to move but has no update this tick.
            move_updates = MovementSystem.resolve_move(state, entity, entity.navigation.target, mode=entity.navigation.movement_mode)
            for u_id, u_upd in move_updates.items():
                existing = refined_entity_updates.get(u_id, EntityUpdate(entity_id=u_id))
                refined_entity_updates[u_id] = existing.merge(u_upd)
                            
        return replace(update, entity_updates=refined_entity_updates)

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
        return EntityUpdate(
            entity_id=entity.id,
            new_position=new_position,
            moved_this_tick=True,
            readiness_delta=-entity.combat.move_cost,
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
