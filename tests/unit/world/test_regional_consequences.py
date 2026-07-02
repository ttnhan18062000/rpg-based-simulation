import pytest
from src.core.state import (
    EntityState, RegionState, AuthoritativeState, CombatComponent,
    NavigationComponent, LifecycleComponent, IdentityComponent,
    BiologicalComponent, StrategicComponent, SocialComponent
)
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate
from src.core.enums import ReasonCode
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.legality import LegalityServiceV2
from src.core.builder import V2EntityBuilder
from src.world.environment import EnvironmentService

def make_hero(eid: int, pos=(5.0, 5.0), hp=100):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(eid)
        .kind("HERO")
        .location(pos[0], pos[1])
        .combat(hp=hp, max_hp=100)
        .combat(alive=True)
        .combat(readiness=100.0)
        .build())


def make_entity_with_faction(eid: int, faction_id: str) -> EntityState:
    return (V2EntityBuilder(eid)
        .kind("HERO")
        .location(5.0, 5.0)
        .identity(properties={"faction_id": faction_id})
        .build())

def test_regional_hazard_drain():
    """Verify that entities in high hazard regions take passive HP damage."""
    # Region from (0,0) to (10,10) with hazard 0.5
    region = RegionState(id="volcano", name="Volcano", bounds=(0, 0, 10, 10), hazard_level=0.5)
    
    # Entity at (5,5) with 100 HP
    hero = make_hero(1, pos=(5.0, 5.0), hp=100)
    
    state = AuthoritativeState(tick=100, seed=42, 
                               regions={"volcano": region},
                               entities={1: hero})
    
    update = StateUpdate()
    refined = AuthoritativeApplyPipeline.refine(state, update)
    # Apply one tick
    next_state = ApplyPath.apply_generation(state, refined, 101, 101)
    
    # damage = hazard(0.5) * 10 * (1 + calamity(0.0)) = 5
    assert next_state.entities[1].combat.hp == 95

def test_regional_suppression_blocks_sabotage_directly():
    """
    Law:
        SABOTAGE is illegal inside a suppressed region.

    This tests the real legality rule directly, without assuming the pipeline
    rewrites TaskUpdate.payload_set.
    """
    region = RegionState(
        id="holy_city",
        name="Holy City",
        bounds=(0, 0, 10, 10),
        suppression_active=True,
    )

    hero = make_hero(1, pos=(5.0, 5.0))

    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"holy_city": region},
        entities={1: hero},
    )

    legal, reason = LegalityServiceV2.verify_action_legality(
        hero,
        "SABOTAGE",
        state,
    )

    assert legal is False
    assert reason == ReasonCode.REGIONAL_SUPPRESSION or reason == "REGIONAL_SUPPRESSION"
    
def test_regional_suppression_blocks_sabotage_pipeline_integration():
    """
    Pipeline integration law:
        A suppressed SABOTAGE action should be rejected/audited by the
        authoritative pipeline.

    Important:
        The pipeline should not need to mutate TaskUpdate.payload_set to prove
        failure. RejectionEvent is the cleaner authoritative audit surface.
    """
    region = RegionState(
        id="holy_city",
        name="Holy City",
        bounds=(0, 0, 10, 10),
        suppression_active=True,
    )

    hero = make_hero(1, pos=(5.0, 5.0))

    state = AuthoritativeState(
        tick=100,
        seed=42,
        regions={"holy_city": region},
        entities={1: hero},
    )

    task_upd = TaskUpdate(
        work_kind_set="ENTITY_ACT",
        payload_set={
            "action": "SABOTAGE",
            "target_id": 99,
        },
    )

    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                task=task_upd,
            )
        }
    )

    refined = AuthoritativeApplyPipeline.refine(state, update)

    assert any(
        ev.actor_id == 1
        and ev.action_kind == "SABOTAGE"
        and ev.reason in (ReasonCode.REGIONAL_SUPPRESSION, "REGIONAL_SUPPRESSION")
        for ev in refined.rejection_events
    )

def test_regional_suppression_allows_attack():
    """Verify that ATTACK is NOT blocked (only strategic actions like SABOTAGE/RECRUIT)."""
    region = RegionState(id="holy_city", name="Holy City", bounds=(0, 0, 10, 10), suppression_active=True)
    
    hero = make_hero(1, pos=(5.0, 5.0))
    state = AuthoritativeState(tick=100, seed=42, 
                               regions={"holy_city": region},
                               entities={1: hero})
    
    # Try to ATTACK
    task_upd = TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 2})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=task_upd)})
    
    refined = AuthoritativeApplyPipeline.refine(state, update)
    
    # Should NOT be blocked by verify_action_legality (it might fail later for target=None, but not suppression)
    ent_upd = refined.entity_updates[1]
    assert ent_upd.task.payload_set.get("reason") != "REGIONAL_SUPPRESSION"


# --- TCK-20260701-HAZARD-NATIVE-IMMUNITY: hazard_kind / faction hazard_immunities ---

def test_hazard_drain_faction_endures_matching_hazard_kind():
    """A faction with authored endurance for a region's hazard_kind takes zero drain."""
    region = RegionState(
        id="wolf_den", name="Wolf Den", bounds=(0, 0, 10, 10),
        hazard_level=2.0, hazard_kind="NATURAL_TERRAIN",
    )
    wolf = make_entity_with_faction(1, "wild_beast_pack")

    drain = EnvironmentService.calculate_hazard_drain(region, wolf)
    assert drain == 0


def test_hazard_drain_different_faction_same_hazard_kind_full_drain():
    """A faction with no authored endurance for the hazard_kind takes the full, unchanged drain."""
    region = RegionState(
        id="wolf_den", name="Wolf Den", bounds=(0, 0, 10, 10),
        hazard_level=2.0, hazard_kind="NATURAL_TERRAIN",
    )
    hero = make_entity_with_faction(1, "hero_guild")

    drain = EnvironmentService.calculate_hazard_drain(region, hero)
    # 2.0 * (1 + 0.0) * 10 = 20, unchanged base formula
    assert drain == 20


def test_hazard_drain_shared_hazard_kind_hurts_mutually_hostile_factions_equally():
    """A hazard_kind nobody is flagged as enduring hurts every faction present, including
    two factions that are actually hostile to one another."""
    from src.content_semantics.faction import get_faction_semantics_service

    semantics = get_faction_semantics_service()
    # goblin_warband (invader) vs hero_guild (defender) are genuinely mutually hostile
    # per FactionSemanticsService.is_hostile (not just contextually, unlike wild_beast_pack).
    assert semantics.is_hostile("hero_guild", "goblin_warband") is True

    region = RegionState(
        id="toxic_swamp", name="Toxic Swamp", bounds=(0, 0, 10, 10),
        hazard_level=1.0, hazard_kind="TOXIC_GAS",
    )
    hero = make_entity_with_faction(1, "hero_guild")
    goblin = make_entity_with_faction(2, "goblin_warband")

    hero_drain = EnvironmentService.calculate_hazard_drain(region, hero)
    goblin_drain = EnvironmentService.calculate_hazard_drain(region, goblin)

    # 1.0 * (1 + 0.0) * 10 = 10, unchanged base formula, for both sides
    assert hero_drain == 10
    assert goblin_drain == 10


def test_hazard_drain_synthetic_faction_endures_named_hazard_kind():
    """Endurance is per hazard_kind, not a blanket pass — a synthetic faction that endures
    CHAOS_CORRUPTION is not thereby immune to a different, unrelated hazard_kind, and other
    factions are not incidentally granted its endurance."""
    from src.content.repository import CatalogRepository
    from src.content.schema import FactionDefinition
    from src.content_semantics.faction import (
        configure_faction_semantics_service,
        reset_faction_semantics_service,
    )

    repo = CatalogRepository("data/content")
    repo.load_all()
    repo.factions["fiend_lords"] = FactionDefinition(
        id="fiend_lords",
        alignment_bucket="invader",
        influence_role="challenger",
        legacy_engine_bucket="MONSTER_HORDE",
        hazard_immunities=["CHAOS_CORRUPTION"],
    )

    try:
        configure_faction_semantics_service(repo)

        region = RegionState(
            id="corrupted_rift", name="Corrupted Rift", bounds=(0, 0, 10, 10),
            hazard_level=3.0, hazard_kind="CHAOS_CORRUPTION",
        )
        fiend = make_entity_with_faction(1, "fiend_lords")
        wolf = make_entity_with_faction(2, "wild_beast_pack")

        assert EnvironmentService.calculate_hazard_drain(region, fiend) == 0
        # wild_beast_pack only endures NATURAL_TERRAIN, not CHAOS_CORRUPTION.
        assert EnvironmentService.calculate_hazard_drain(region, wolf) != 0
    finally:
        reset_faction_semantics_service()


def test_hazard_drain_zero_hazard_region_unaffected():
    """A zero-hazard region deals zero drain regardless of faction endurance."""
    region = RegionState(
        id="safe_glade", name="Safe Glade", bounds=(0, 0, 10, 10),
        hazard_level=0.0, hazard_kind="NATURAL_TERRAIN",
    )
    wolf = make_entity_with_faction(1, "wild_beast_pack")
    hero = make_entity_with_faction(2, "hero_guild")

    assert EnvironmentService.calculate_hazard_drain(region, wolf) == 0
    assert EnvironmentService.calculate_hazard_drain(region, hero) == 0


def test_hazard_drain_endurance_survives_miasma_and_calamity():
    """Endurance is unconditional: it applies regardless of calamity_intensity/active_modifiers."""
    region = RegionState(
        id="wolf_den", name="Wolf Den", bounds=(0, 0, 10, 10),
        hazard_level=2.0, hazard_kind="NATURAL_TERRAIN",
        calamity_intensity=1.0, active_modifiers=["MIASMA"],
    )
    wolf = make_entity_with_faction(1, "wild_beast_pack")

    assert EnvironmentService.calculate_hazard_drain(region, wolf) == 0


def test_hazard_drain_default_hazard_kind_no_regression():
    """A region with no explicit hazard_kind defaults to PHYSICAL, which no faction lists in
    hazard_immunities today — the new field must not grant accidental universal immunity."""
    region = RegionState(
        id="plains", name="Plains", bounds=(0, 0, 10, 10),
        hazard_level=2.0,
    )
    assert region.hazard_kind == "PHYSICAL"

    wolf = make_entity_with_faction(1, "wild_beast_pack")
    drain = EnvironmentService.calculate_hazard_drain(region, wolf)
    # 2.0 * (1 + 0.0) * 10 = 20, unchanged base formula
    assert drain == 20
