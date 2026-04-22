from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, Dict, List, Tuple

from src_v2.core.updates import StateUpdate, EntityUpdate, NavigationUpdate

if TYPE_CHECKING:
    from src_v2.core.state import AuthoritativeState

class AuthoritativeApplyPipeline:
    """
    Unified authoritative refinement pipeline for the V2 Engine.
    Enforces the "Proposal -> Refinement -> Apply" law.
    """

    @staticmethod
    def refine(state: AuthoritativeState, raw_update: StateUpdate) -> StateUpdate:
        """
        Refines a proposed StateUpdate through the authoritative law pipeline.
        Consolidates Town, Shop, Blacksmith, Interaction, and Movement rules.
        """
        from src_v2.engine.town_resolution import TownResolutionSystem
        from src_v2.engine.shop import ShopSystem
        from src_v2.engine.blacksmith import BlacksmithSystem
        from src_v2.engine.interaction import InteractionSystem
        from src_v2.systems.strategic import StrategicIntelligenceSystem
        from src_v2.systems.redirection import StrategicRedirectionSystem
        from src_v2.engine.movement import MovementSystem
        from src_v2.engine.world_dynamics import WorldDynamicsSystem
        from src_v2.engine.evolution import EvolutionSystem
        from src_v2.engine.sabotage import BuildingSabotageSystem
        from src_v2.engine.combat import CombatResolutionSystem
        from src_v2.engine.legality import LegalityServiceV2
        
        # 1. Territorial & Service Laws (Healing, Shopping, Crafting)
        # These operate on current position (or proposed new position)
        update = TownResolutionSystem.resolve(state, raw_update)
        update = ShopSystem.enforce(state, update)
        update = BlacksmithSystem.enforce(state, update)
        
        # 1.2 Combat Laws (Attack resolution)
        update = AuthoritativeApplyPipeline._route_combat_intent(state, update)
        
        # 1.5 World Dynamics (Regional Hazards, Calamities)
        update = WorldDynamicsSystem.resolve_dynamics(state, update)
        
        # 1.6 Building Sabotage
        update = BuildingSabotageSystem.resolve(state, update)
        
        # 2. Intent Routing (Interaction)
        # Identifies if entity is at a resource node and initiates progress
        update = AuthoritativeApplyPipeline._route_interaction_intent(state, update)
        
        # 3. Interaction Enforcement (Harvesting/Looting)
        # Validates channeling progress, item weights, and node depletion
        update = InteractionSystem.enforce(state, update)
        
        # 4. Strategic Logic
        update = StrategicIntelligenceSystem.resolve_blockers(state, update)
        update = StrategicRedirectionSystem.enforce(state, update)
        
        # 5. Intent Routing (Movement)
        # Resolves proposed navigation targets into step-wise moves
        update = AuthoritativeApplyPipeline._route_movement_intent(state, update)
        
        # 6. Conflict Resolution (Occupancy)
        # Tie-breaks multiple entities racing for the same tile
        update = AuthoritativeApplyPipeline._resolve_occupancy_conflicts(state, update)
        
        # 7. Evolution & Growth
        update = EvolutionSystem.evaluate(state, update)
        
        return update

    @staticmethod
    def _route_interaction_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        refined_entity_updates = dict(update.entity_updates)
        for e_id, entity in state.entities.items():
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            nav_target = entity.navigation.target
            if ent_upd.navigation and ent_upd.navigation.target_set is not None:
                nav_target = ent_upd.navigation.target_set
            
            if nav_target and (entity.position == nav_target):
                target_node = next((n for n in state.resource_nodes.values() if n.position == nav_target), None)
                if target_node and target_node.remaining_charges > 0:
                    from src_v2.core.updates import InteractionUpdate
                    current_int = ent_upd.interaction or InteractionUpdate()
                    if not current_int.reset:
                         refined_entity_updates[e_id] = replace(ent_upd,
                             interaction=replace(current_int, target_node_id=target_node.id, progress_delta=1)
                         )
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def _route_movement_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src_v2.engine.movement import MovementSystem
        refined_entity_updates = dict(update.entity_updates)
        for e_id, entity in state.entities.items():
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            nav_target = entity.navigation.target
            if ent_upd.navigation and ent_upd.navigation.target_set is not None:
                nav_target = ent_upd.navigation.target_set
            
            if nav_target and (entity.position != nav_target):
                # Only move if not already moved and not currently interacting (harvesting)
                # Note: ent_upd.interaction might have been added in _route_interaction_intent
                is_interacting = (ent_upd.interaction and ent_upd.interaction.progress_delta > 0)
                if not ent_upd.moved_this_tick and not is_interacting:
                    move_upd = MovementSystem.resolve_move(state, entity, nav_target)
                    
                    # Merge NavigationUpdate (Milestone 3 Law: No intent loss)
                    base_nav = ent_upd.navigation or NavigationUpdate()
                    move_nav = move_upd.navigation or NavigationUpdate()
                    merged_nav = replace(base_nav,
                        target_set=move_nav.target_set if move_nav.target_set is not None else base_nav.target_set,
                        path_set=move_nav.path_set if move_nav.path_set is not None else base_nav.path_set,
                        moved_recently_set=move_nav.moved_recently_set if move_nav.moved_recently_set is not None else base_nav.moved_recently_set,
                        failure_reason=move_nav.failure_reason if move_nav.failure_reason is not None else base_nav.failure_reason
                    )
                    
                    refined_entity_updates[e_id] = replace(ent_upd, 
                        new_position=move_upd.new_position,
                        moved_this_tick=move_upd.moved_this_tick,
                        readiness_delta=ent_upd.readiness_delta + move_upd.readiness_delta,
                        combat=move_upd.combat or ent_upd.combat,
                        navigation=merged_nav
                    )
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def _route_combat_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Processes ATTACK intents and resolves them through CombatResolutionSystem.
        Includes legality checks and position-sensitive bonuses (Milestone 4).
        """
        from src_v2.engine.combat import CombatResolutionSystem
        from src_v2.engine.legality import LegalityServiceV2
        from src_v2.core.updates import EntityUpdate
        
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id, entity in state.entities.items():
            ent_upd = refined_entity_updates.get(e_id)
            if not ent_upd or not ent_upd.task: continue
            
            task_upd = ent_upd.task
            if task_upd.work_kind_set == "ENTITY_ACT" and task_upd.payload_set.get("action") == "ATTACK":
                target_id = task_upd.payload_set.get("target_id")
                if target_id is None: continue
                
                target = state.entities.get(target_id)
                if not target: continue
                
                # 1. Legality Check (LoS, Range, Faction)
                is_legal, reason = LegalityServiceV2.verify_attack_legality(entity, target, state)
                if not is_legal:
                     # Mark failure in task payload (Milestone 3 logic)
                     refined_entity_updates[e_id] = replace(ent_upd,
                         task=replace(task_upd, payload_set={**task_upd.payload_set, "failure_reason": reason})
                     )
                     continue
                
                # 2. Position-Sensitive Bonuses (Milestone 4)
                # 2.1 High Ground
                attacker_terrain = state.terrain.get((int(entity.position[0]), int(entity.position[1])))
                atk_bonus = 0
                if attacker_terrain == "HILL":
                    atk_bonus += 5
                
                # 2.2 Bracketing (Flanking)
                # If target is between two hostiles on opposite sides
                engaged = LegalityServiceV2.get_engaged_hostiles(target, state)
                if len(engaged) >= 2:
                    # Check for opposite pairs
                    # (x+1, y) and (x-1, y) OR (x, y+1) and (x, y-1)
                    tx, ty = int(target.position[0]), int(target.position[1])
                    opposites = [
                        ((tx+1, ty), (tx-1, ty)),
                        ((tx, ty+1), (tx, ty-1))
                    ]
                    for pair_a, pair_b in opposites:
                        has_a = any(int(state.entities[eid].position[0]) == pair_a[0] and 
                                    int(state.entities[eid].position[1]) == pair_a[1] for eid in engaged)
                        has_b = any(int(state.entities[eid].position[0]) == pair_b[0] and 
                                    int(state.entities[eid].position[1]) == pair_b[1] for eid in engaged)
                        if has_a and has_b:
                            atk_bonus += 3 # Bracketing bonus
                            break

                # 3. Resolve Attack
                combat_upd = CombatResolutionSystem.resolve_attack(
                    entity, 
                    target, 
                    is_lethal=True
                )
                
                # Apply bonus to damage taken in update (Authoritative modification)
                if atk_bonus > 0:
                    combat_upd = replace(combat_upd, 
                        damage_taken=combat_upd.damage_taken + atk_bonus,
                        hp_delta=combat_upd.hp_delta - atk_bonus
                    )
                
                # 4. Emit Updates
                # Target gets the combat update (HP change)
                target_upd = refined_entity_updates.get(target_id, EntityUpdate(entity_id=target_id))
                refined_entity_updates[target_id] = replace(target_upd, combat=combat_upd)
                
                # Attacker is marked as having acted (readiness reset is handled by Kernel/Apply)
                # But we might want to record the action in the payload
                refined_entity_updates[e_id] = replace(ent_upd,
                    task=replace(task_upd, payload_set={**task_upd.payload_set, "outcome": "SUCCESS"})
                )

        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def _resolve_occupancy_conflicts(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Milestone 3 Law: Conflict resolution must be deterministic.
        Priority: Class Priority > Local Priority > Entity ID.
        """
        # 1. Collect all proposals for position changes
        proposals: Dict[tuple[int, int], List[int]] = {} # (x, y) -> List of EntityIDs
        
        # Include current positions of entities that are NOT moving to block tiles
        # (Actually, only entities that ARE active block tiles)
        current_occupied = { (int(e.position[0]), int(e.position[1])): e.id 
                             for e in state.entities.values() if e.active }
        
        # entities_moving tracks who is proposing a NEW position
        entities_moving = []
        for e_id, ent_upd in update.entity_updates.items():
            if ent_upd.new_position:
                entities_moving.append(e_id)
                target = (int(ent_upd.new_position[0]), int(ent_upd.new_position[1]))
                if target not in proposals: proposals[target] = []
                proposals[target].append(e_id)
        
        if not proposals:
            return update

        refined_entity_updates = dict(update.entity_updates)
        
        # 2. Sort targets and contenders for determinism
        sorted_targets = sorted(proposals.keys())
        
        for target in sorted_targets:
            contenders = proposals[target]
            
            # Tie-breaking logic
            # We need to look up priorities. For now we use EntityID (lower is better)
            # as a simple deterministic proxy for Class/Local priority.
            contenders.sort() # Lowest ID wins
            
            winner_id = contenders[0]
            losers = contenders[1:]
            
            # Check if target is already occupied by someone who ISN'T moving
            existing_occupant = current_occupied.get(target)
            if existing_occupant and existing_occupant not in entities_moving:
                # Winner also loses because the tile is blocked by a static entity
                winner_id = None
                losers = contenders
            
            if winner_id is not None:
                # Winner keeps their position
                pass
                
            for loser_id in losers:
                # Revert move for losers
                ent_upd = refined_entity_updates[loser_id]
                refined_entity_updates[loser_id] = replace(
                    ent_upd,
                    new_position=None,
                    moved_this_tick=False,
                    # We might want to refund readiness, but legacy says move "started" then failed
                    navigation=replace(ent_upd.navigation or NavigationUpdate(), 
                                      failure_reason="OCCUPANCY_CONFLICT")
                )
                
        return replace(update, entity_updates=refined_entity_updates)
