import pytest
import uuid
from src.core.models.world_state import WorldState
from src.core.models.vectors import Vector2
from src.core.models.enums import GoalType, Faction, OfferStatus, ContractKind, GroupKind
from src.core.models.strategy import StrategicStatus, RecruitmentOfferRecord, SocialContractRecord
from src.actions.base import StrategicUpdate
from src.core.world.grid import Grid
from src.systems.spatial_hash import SpatialHash
from src.core.entities.entity_builder import EntityBuilder
from src.platform.rng import DeterministicRNG
from src.config import SimulationConfig
from src.systems.infrastructure.base import SystemContext
from src.systems.social.group_system import GroupSystem
from src.core.models.snapshot import Snapshot
from src.ai.brain import AIBrain
from src.ai.states.base import AIContext
from src.ai.strategy.recruitment_negotiation import RecruitmentNegotiationService
from src.ai.strategy.social_candidate_selection import SocialCandidateSelectionService

@pytest.fixture
def social_setup():
    grid = Grid(100, 100)
    spatial = SpatialHash(10)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    config = SimulationConfig()
    rng = DeterministicRNG(42)
    
    from src.core.gameplay.faction import FactionRegistry
    faction_reg = FactionRegistry.default()
    
    context = SystemContext(
        config=config,
        world=world,
        rng=rng,
        generator=None,
        faction_reg=faction_reg,
        emit=lambda *args, **kwargs: None
    )
    
    return context

def test_full_contract_lifecycle(social_setup):
    """Verify the full E2E flow: Selection -> Offer -> Acceptance -> Group -> Role Coordination."""
    ctx = social_setup
    world = ctx.world
    rng = ctx.rng
    
    # 1. Setup entities
    founder = EntityBuilder(rng, 1).kind("hero").at(Vector2(10, 10)).build()
    founder.identity.display_name = "Founder"
    founder.identity.faction = Faction.HERO_GUILD
    founder.progression.level = 5
    founder.progression.gold = 500
    founder.mind.decision.personality.greed = 0.1 # Generous
    
    candidate = EntityBuilder(rng, 2).kind("hero").at(Vector2(11, 11)).build()
    candidate.identity.display_name = "Candidate"
    candidate.identity.faction = Faction.HERO_GUILD
    candidate.progression.level = 3
    candidate.mind.decision.personality.greed = 0.1 # Content
    
    world.entities[founder.id] = founder
    world.entities[candidate.id] = candidate
    
    # 2. SELECTION: Founder finds candidate
    ai_ctx = AIContext(
        actor=founder,
        snapshot=Snapshot.from_world(world),
        config=ctx.config,
        rng=rng,
        faction_reg=ctx.faction_reg
    )
    
    candidates = SocialCandidateSelectionService.find_candidates(ai_ctx)
    assert len(candidates) >= 1
    assert candidates[0].entity_id == candidate.id
    
    # 3. OFFER: Founder creates offer
    offer = RecruitmentNegotiationService.create_offer(ai_ctx, candidate.id, None, ContractKind.EXPEDITION)
    assert offer.candidate_id == candidate.id
    assert offer.status == OfferStatus.PENDING
    assert offer.recruiter_id == founder.id
    
    # 4. APPRAISAL: Candidate evaluates and accepts
    cand_ctx = AIContext(
        actor=candidate,
        snapshot=Snapshot.from_world(world),
        config=ctx.config,
        rng=rng,
        faction_reg=ctx.faction_reg
    )
    appraisal = RecruitmentNegotiationService.evaluate_offer(cand_ctx, offer)
    assert appraisal.status == OfferStatus.ACCEPTED # Should be true given default neutral bond
    
    # 5. ACTIVATION: (Simulated recruitment finalization)
    offer.status = OfferStatus.ACCEPTED
    contract_id = f"ct_{uuid.uuid4().hex[:4]}"
    contract = SocialContractRecord(
        contract_id=contract_id,
        founder_id=founder.id,
        kind=ContractKind.EXPEDITION,
        purpose="Exploring the northern wastes",
        member_ids=[founder.id, candidate.id],
        member_roles={founder.id: "vanguard", candidate.id: "support"},
        status=StrategicStatus.ACTIVE
    )
    
    # Add contract to both entities
    founder.mind.strategic.contracts.append(contract)
    candidate.mind.strategic.contracts.append(contract)
    
    # 6. GROUP FORMATION: GroupSystem creates the PARTY
    group_sys = GroupSystem(ctx.config, ctx.rng)
    group_sys.on_tick(ctx, 10)
    
    assert len(world.group_registry) == 1
    group = next(iter(world.group_registry.values()))
    assert group.kind == GroupKind.PARTY
    assert founder.id in group.member_ids
    assert candidate.id in group.member_ids
    assert founder.identity.group_id == group.group_id
    assert candidate.identity.group_id == group.group_id
    
    # 7. ROLE COORDINATION: Verify tactical hints
    brain = AIBrain(ctx.config, ctx.rng, ctx.faction_reg)
    
    # Candidate decision (Support role)
    cand_snapshot = Snapshot.from_world(world)
    cand_ai_ctx = AIContext(actor=candidate, snapshot=cand_snapshot, config=ctx.config, rng=rng, faction_reg=ctx.faction_reg)
    
    # Manually trigger hint population to verify
    brain._populate_role_tactical_hints(cand_ai_ctx)
    assert cand_ai_ctx.tactical_hints.get("skirmish") is True
    assert cand_ai_ctx.tactical_hints.get("follow_target_id") == founder.id
    
    # 8. RESOLUTION: Success consequences
    from src.ai.strategy.contract_outcome import ContractOutcomeService
    
    # ContractOutcomeService now returns IntentUpdates instead of mutating
    updates_batch = ContractOutcomeService.resolve_contract(contract, StrategicStatus.RESOLVED, tick=world.tick)
    
    # Apply updates authoritatively (GroupSystem or specific applicator)
    # In this test, we can manually apply them to verify logic
    for actor_id, updates in updates_batch.items():
        actor = world.entities[actor_id]
        for u in updates:
            from src.actions.base import SocialUpdate, ReputationUpdate
            from src.core.logic.relationship_service import RelationshipService
            from src.core.logic.reputation_service import ReputationService
            if isinstance(u, SocialUpdate):
                RelationshipService.apply_update(world.social_registry, u, world.tick)
            elif isinstance(u, ReputationUpdate):
                ReputationService.apply_update(actor, u)
    
    # Verify bond improvement in global registry
    bond = world.social_registry.get_bond_or_none(candidate.id, founder.id)
    assert bond is not None
    assert bond.trust > 0.5 # Default 0.0 + 0.6 delta
    
    # Verify reputation gain
    assert founder.identity.reputation.trustworthiness > 0.5
