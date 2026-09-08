import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.core.cognition import CognitionModel, CommitmentModel, CommitmentEntry, PublicReputationProfile, RelationshipModel, MotivationModel
from src.domains.commitment.pressure import CommitmentPressureService
from src.domains.commitment.abandonment import AbandonmentEvaluator
from src.domains.commitment.reputation import ReputationUpdateService
from src.domains.commitment.impact import CommitmentReputationRouteImpact

def test_accepted_escort_prevents_minor_loot_switch():
    # Setup entity with active escort commitment
    entry = CommitmentEntry(
        id="escort_1",
        kind="escort",
        target_id="villager_1",
        strength=0.8,
        deadline_tick=100,
        created_tick=10
    )
    commitment = CommitmentModel(active_commitments={"escort_1": entry})
    cognition = CognitionModel(commitment=commitment)
    entity = replace(EntityState(id=1, kind="HERO"), cognition=cognition)

    # Base score of route options
    base_escort_score = 1.0
    base_loot_score = 1.2 # loot option is slightly higher initially

    # Apply route bias
    escort_score = CommitmentReputationRouteImpact.apply_route_bias(entity, ["escort"], base_escort_score)
    loot_score = CommitmentReputationRouteImpact.apply_route_bias(entity, ["loot"], base_loot_score)

    # Commitment should boost escort route higher than the slight loot advantage
    assert escort_score > loot_score

def test_abandoning_party_changes_future_partner_selection():
    # Evaluate a bad abandonment
    eval_res = AbandonmentEvaluator.evaluate_abandonment(
        hp=90, max_hp=100, is_party_in_combat=True, is_greed_driven=True
    )
    assert eval_res.is_betrayal is True
    
    # Process betrayal event to update public reputation
    profile = PublicReputationProfile(labels={"reliable": 0.6})
    updated_profile = ReputationUpdateService.process_witnessed_event(profile, "betrayal")
    assert updated_profile.labels.get("betrayer", 0.0) == 0.4
    assert updated_profile.labels.get("reliable", 0.0) == 0.3

    # Fit score calculation for a third party
    fit_score = CommitmentReputationRouteImpact.apply_partner_fit_bias(
        entity=EntityState(id=2, kind="HERO"),
        candidate_reputation=updated_profile.labels,
        base_fit=1.0
    )
    # Fit score is significantly penalized due to the candidate's betrayer label
    assert fit_score < 0.5


# ---------------------------------------------------------------------------
# TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING
# ---------------------------------------------------------------------------

def test_successful_escort_completion_updates_reputation():
    """
    A QuestKind.ESCORT quest transitioning ACTIVE->COMPLETED via
    QuestResolutionSystem.enforce() is a real witnessed event: it must call
    ReputationUpdateService.process_witnessed_event(..., "successful_escort")
    and stage the result via EntityUpdate.cognition_bundle_set.
    """
    from src.core.builder import V2EntityBuilder
    from src.core.state import AuthoritativeState
    from src.core.strategic import StrategicComponent
    from src.core.quests import QuestState, QuestKind, QuestStatus as QS, RewardState
    from src.core.updates import StateUpdate, QuestUpdate, EntityUpdate
    from src.engine.quests import QuestResolutionSystem

    entity_id = 1
    quest = QuestState(
        id="q-escort-1",
        kind="quest",
        quest_kind=QuestKind.ESCORT,
        quest_status=QS.ACTIVE,
        goal_value=1.0,
        current_value=0.0,
        reward=RewardState(xp=10, gold=5),
    )
    entity = (
        V2EntityBuilder(entity_id)
        .kind("HERO")
        .strategic(projects={quest.id: quest})
        .build()
    )
    pre_tick_profile = entity.cognition.relationships.public_reputation
    expected_profile = ReputationUpdateService.process_witnessed_event(
        pre_tick_profile, "successful_escort"
    )

    state = AuthoritativeState(tick=10, seed=42, entities={entity_id: entity})
    update = StateUpdate(
        entity_updates={
            entity_id: EntityUpdate(
                entity_id=entity_id,
                quest=QuestUpdate(quest_id=quest.id, progress_delta=1.0, status_set=QS.COMPLETED),
            )
        }
    )

    refined = QuestResolutionSystem.enforce(state, update)
    ent_upd = refined.entity_updates[entity_id]

    assert ent_upd.cognition_bundle_set is not None
    new_profile = ent_upd.cognition_bundle_set.relationships.public_reputation
    assert new_profile.labels["reliable"] == expected_profile.labels["reliable"]
    assert new_profile.labels["reliable"] == pytest.approx(pre_tick_profile.labels.get("reliable", 0.5) + 0.1)


def test_quest_reward_phase_preserves_memory_update_cognition_writes():
    """
    Regression guard for the merge-safety hazard: MemoryUpdatePhase runs before
    quest_rewards and unconditionally stages cognition_bundle_set. The ESCORT
    reputation write in QuestResolutionSystem.enforce() must layer onto that
    staged value (via ent_upd.cognition_bundle_set as its base), never discard it.
    """
    from dataclasses import replace as _replace
    from src.core.builder import V2EntityBuilder
    from src.core.state import AuthoritativeState
    from src.core.cognition import CausalMemory, CausalMemoryEntry, MemoryModel
    from src.core.quests import QuestState, QuestKind, QuestStatus as QS, RewardState
    from src.core.updates import StateUpdate, QuestUpdate, EntityUpdate
    from src.engine.quests import QuestResolutionSystem

    entity_id = 1
    quest = QuestState(
        id="q-escort-2",
        kind="quest",
        quest_kind=QuestKind.ESCORT,
        quest_status=QS.ACTIVE,
        goal_value=1.0,
        current_value=0.0,
        reward=RewardState(xp=10, gold=5),
    )
    entity = (
        V2EntityBuilder(entity_id)
        .kind("HERO")
        .strategic(projects={quest.id: quest})
        .build()
    )
    state = AuthoritativeState(tick=10, seed=42, entities={entity_id: entity})

    causal_entry = CausalMemoryEntry(
        event_id="evt-1",
        event_kind="witnessed_ambush",
        interpreted_causes=("bandit_raid",),
        confidence=0.7,
        future_advice=("avoid_road",),
        tick=10,
    )
    staged_cognition = _replace(
        entity.cognition,
        memory=MemoryModel(causal=CausalMemory(entries=(causal_entry,))),
    )

    update = StateUpdate(
        entity_updates={
            entity_id: EntityUpdate(
                entity_id=entity_id,
                cognition_bundle_set=staged_cognition,
                quest=QuestUpdate(quest_id=quest.id, progress_delta=1.0, status_set=QS.COMPLETED),
            )
        }
    )

    refined = QuestResolutionSystem.enforce(state, update)
    ent_upd = refined.entity_updates[entity_id]

    assert ent_upd.cognition_bundle_set is not None
    assert ent_upd.cognition_bundle_set.memory.causal.entries == (causal_entry,)
    assert ent_upd.cognition_bundle_set.relationships.public_reputation.labels["reliable"] == pytest.approx(0.6)
