# Compliance IDs: DATA-100, DATA-101, DATA-102, STRAT-046, STRAT-077, STRAT-078, STRAT-081, STRAT-082, STRAT-083, STRAT-084, STRAT-085, STRAT-086, STRAT-087, STRAT-088, STRAT-089, STRAT-100, STRAT-122, STRAT-123, STRAT-124, STRAT-125, STRAT-126, STRAT-127, STRAT-128, STRAT-129, STRAT-130, STRAT-131, STRAT-132, STRAT-133, STRAT-134, STRAT-135, STRAT-144, STRAT-147, STRAT-148
# src/engine/quests.py
from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Optional

from src.core.quests import QuestState, QuestKind, QuestStatus
from src.core.updates import QuestUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState

class QuestResolutionSystem:
    """
    Authoritative logic for quest progression and completion.
    Emits QuestUpdates that are processed by ApplyPath.
    """

    @staticmethod
    def evaluate_explore(state: AuthoritativeState, entity: EntityState) -> List[QuestUpdate]:
        """Check EXPLORE quests for proximity to target."""
        updates = []
        
        # In V2, active quests are stored as ProjectState inside entity.strategic.projects
        for q_id in sorted(entity.strategic.projects.keys()):
            project = entity.strategic.projects[q_id]
            if not isinstance(project, QuestState):
                continue
                
            if project.quest_status != QuestStatus.ACTIVE:
                continue
                
            if project.quest_kind != QuestKind.EXPLORE:
                continue
                
            target_pos = project.metadata.get("target_pos")
            if target_pos:
                dist = abs(entity.navigation.position[0] - target_pos[0]) + abs(entity.navigation.position[1] - target_pos[1])
                
                # If within 2 manhattan distance, quest completes
                if dist <= 2.0:
                    # Setting progress_delta to goal_value ensures it finishes
                    delta = max(0.0, project.goal_value - project.current_value)
                    updates.append(QuestUpdate(
                        quest_id=q_id,
                        progress_delta=delta
                    ))
                    
        return updates

    @staticmethod
    def evaluate_combat_victory(
        attacker: EntityState,
        victim_kind: str,
        victim_entity: Optional[EntityState] = None,
    ) -> List[QuestUpdate]:
        """Advance HUNT quests when an enemy is defeated."""
        import logging as _log
        _logger = _log.getLogger(__name__)

        updates = []

        # Pre-resolve clean identity fields once (before the project loop).
        _victim_archetype_id: Optional[str] = None
        _victim_faction_id: Optional[str] = None
        _attacker_faction_id: Optional[str] = None
        _proj_service = None
        _perspective_id: Optional[str] = None

        if victim_entity is not None:
            from src.entities.identity_resolver import EntityIdentityResolver, IdentityResolutionError
            _resolver = EntityIdentityResolver()
            try:
                _v = _resolver.resolve(victim_entity)
                _victim_archetype_id = _v.archetype_id
                _victim_faction_id = _v.faction_id
            except IdentityResolutionError:
                _logger.debug("Quest resolution: could not resolve victim identity for entity %s", victim_entity.id)
            try:
                _a = _resolver.resolve(attacker)
                _attacker_faction_id = _a.faction_id
            except IdentityResolutionError:
                _logger.debug("Quest resolution: could not resolve attacker identity for entity %s", attacker.id)

        # Phase 9 Fix: Sort projects by ID for deterministic progress evaluation
        for q_id, project in sorted(attacker.strategic.projects.items()):
            if not isinstance(project, QuestState):
                continue
            if project.quest_status != QuestStatus.ACTIVE:
                continue
            if project.quest_kind != QuestKind.HUNT:
                continue

            matched = False

            # Path 1: clean archetype_id match
            if not matched and _victim_archetype_id is not None:
                t_arch = project.metadata.get("target_archetype_id")
                if t_arch:
                    if t_arch == _victim_archetype_id:
                        matched = True
                    else:
                        _logger.debug(
                            "Quest %s: target_archetype_id=%s did not match victim archetype=%s",
                            q_id, t_arch, _victim_archetype_id,
                        )

            # Path 2: clean faction_id match
            if not matched and _victim_faction_id is not None:
                t_fac = project.metadata.get("target_faction_id")
                if t_fac:
                    if t_fac == _victim_faction_id:
                        matched = True
                    else:
                        _logger.debug(
                            "Quest %s: target_faction_id=%s did not match victim faction=%s",
                            q_id, t_fac, _victim_faction_id,
                        )

            # Path 3: projected relation label match
            if not matched and _victim_faction_id and _attacker_faction_id:
                t_label = project.metadata.get("target_projected_label")
                if t_label:
                    if _proj_service is None:
                        from src.content_semantics.faction import get_faction_semantics_service
                        from src.content_semantics.relation import RelationProjectionService
                        _svc = get_faction_semantics_service()
                        _proj_service = RelationProjectionService(_svc.repo)
                        _perspective_id = _attacker_faction_id
                        for _p in _svc.repo.perspectives.values():
                            if _p.chosen_faction == _attacker_faction_id:
                                _perspective_id = _p.id
                                break
                    proj = _proj_service.project_relation(
                        _perspective_id, _attacker_faction_id, _victim_faction_id, None
                    )
                    if proj.label == t_label:
                        matched = True
                    else:
                        _logger.debug(
                            "Quest %s: target_projected_label=%s did not match projected label=%s",
                            q_id, t_label, proj.label,
                        )

            # Path 4: legacy target_kind fallback (existing behavior, unchanged)
            if not matched:
                if project.metadata.get("target_kind") == victim_kind:
                    matched = True

            if matched:
                updates.append(QuestUpdate(quest_id=q_id, progress_delta=1.0))

        return updates

    @staticmethod
    def enforce(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Enforces quest completion rules and emits authoritative reward intents.
        Ensures that quest rewards are capacity-aware.
        """
        from src.core.updates import ResourceTransferIntent, EntityUpdate
        from dataclasses import replace
        from src.core.quests import QuestStatus
        from src.quests.service import QuestService
        from src.domains.commitment.reputation import ReputationUpdateService
        from src.domains.information.accumulation import InformationAccumulationService

        refined_entity_updates = dict(update.entity_updates)
        providers_update = dict(update.information_providers_update)
        
        # Phase 9 Fix: Sort by entity ID for deterministic reward intent emission
        for e_id in sorted(list(update.entity_updates.keys())):
            ent_upd = update.entity_updates[e_id]
            if not ent_upd.quest:
                continue
                
            entity = state.entities.get(e_id)
            if not entity: continue
            
            q_updates = ent_upd.quest.multi_updates if ent_upd.quest.multi_updates else [ent_upd.quest]
            
            current_quest_updates = []
            current_resource_transfers = list(ent_upd.resource_transfers)
            reputation_cognition_update = None

            for qu in q_updates:
                q_id = qu.quest_id
                project = entity.strategic.projects.get(q_id)
                if not project or not isinstance(project, QuestState):
                    current_quest_updates.append(qu)
                    continue
                    
                # Simulate what the new state will be
                updated_quest = QuestService.add_progress(project, qu.progress_delta)
                if qu.status_set is not None:
                    updated_quest = replace(updated_quest, quest_status=qu.status_set)
                    
                # 1. If transition to COMPLETED is happening OR quest is already REWARD_PENDING
                # we emit an authoritative reward intent.
                is_newly_completed = (updated_quest.quest_status == QuestStatus.COMPLETED and project.quest_status == QuestStatus.ACTIVE)
                is_retry_pending = (project.quest_status == QuestStatus.REWARD_PENDING)
                
                if is_newly_completed or is_retry_pending:
                    from src.core.state import ItemStack
                    items = [ItemStack(item_id=tid, quantity=1) for tid in updated_quest.reward.items]
                    
                    from src.core.updates import RewardUpdate
                    reward_intent = ResourceTransferIntent(
                        source_id=q_id,
                        source_kind="QUEST",
                        items_add=items,
                        gold_delta=updated_quest.reward.gold,
                        reward_upd=RewardUpdate(xp_gain=updated_quest.reward.xp),
                        transfer_kind="QUEST_REWARD",
                        transaction_id=f"quest:{q_id}:reward",
                        group_id=f"quest:{q_id}:reward",
                        is_group_required=True
                    )
                    
                    # Transition to REWARD_PENDING (if not already)
                    current_resource_transfers.append(reward_intent)
                    current_quest_updates.append(replace(qu, status_set=QuestStatus.REWARD_PENDING))

                    if is_newly_completed and project.quest_kind == QuestKind.ESCORT:
                        base_cognition = (
                            reputation_cognition_update
                            if reputation_cognition_update is not None
                            else (
                                ent_upd.cognition_bundle_set
                                if ent_upd.cognition_bundle_set is not None
                                else entity.cognition
                            )
                        )
                        new_profile = ReputationUpdateService.process_witnessed_event(
                            base_cognition.relationships.public_reputation, "successful_escort"
                        )
                        new_relationships = replace(base_cognition.relationships, public_reputation=new_profile)
                        reputation_cognition_update = replace(base_cognition, relationships=new_relationships)

                    if is_newly_completed:
                        flags = getattr(state, "feature_flags", None) or {}
                        if flags.get("ENABLE_INFORMATION_HUB_ACCUMULATION", "OFF") == "ON" and project.source_entity_id is not None:
                            provider = providers_update.get(
                                project.source_entity_id,
                                state.information_providers.get(project.source_entity_id),
                            )
                            if provider is not None:
                                providers_update[project.source_entity_id] = InformationAccumulationService.record_quest_reported_back(provider)
                else:
                    current_quest_updates.append(qu)

            # Reconstruct the merged quest update if we have multiple
            new_q_upd = current_quest_updates[0]
            for i in range(1, len(current_quest_updates)):
                new_q_upd = new_q_upd.merge(current_quest_updates[i])
                
            replace_kwargs = dict(
                resource_transfers=current_resource_transfers,
                quest=new_q_upd,
            )
            if reputation_cognition_update is not None:
                replace_kwargs["cognition_bundle_set"] = reputation_cognition_update

            refined_entity_updates[e_id] = replace(ent_upd, **replace_kwargs)
                
        return replace(update, entity_updates=refined_entity_updates, information_providers_update=providers_update)
