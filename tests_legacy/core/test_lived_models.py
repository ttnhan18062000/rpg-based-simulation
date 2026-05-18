import pytest
from src_legacy.core.models.lived_structure import RoutineProfile, PlaceAttachment, GroupRecord
from src_legacy.core.models.enums import GoalType, GroupKind, AttachmentKind, LifeRole
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.entities.entity_builder import EntityBuilder
from src_legacy.platform.rng import DeterministicRNG

def test_routine_profile_instantiation():
    """Verify RoutineProfile can be instantiated with hybrid scheduling."""
    routine = RoutineProfile(
        routine_id="test_sleep",
        routine_type="sleeping",
        anchor_type="home",
        schedule_window=(22, 6),
        event_triggers=["stamina_low", "night_time"],
        priority=2.0,
        ideal_goal=GoalType.SLEEP
    )
    assert routine.routine_id == "test_sleep"
    assert routine.schedule_window == (22, 6)
    assert "stamina_low" in routine.event_triggers

def test_place_attachment_instantiation():
    """Verify PlaceAttachment can be instantiated and supports sentiment."""
    attachment = PlaceAttachment(
        location_pos=Vector2(10, 10),
        kind=AttachmentKind.HOME,
        importance=0.8
    )
    assert attachment.location_pos.x == 10
    assert attachment.importance == 0.8
    assert attachment.kind == AttachmentKind.HOME

def test_group_record_instantiation():
    """Verify GroupRecord supports shared tactical intent."""
    group = GroupRecord(
        group_id="patrol_alpha",
        kind=GroupKind.PATROL,
        shared_goal=GoalType.GUARD,
        member_ids={1, 2, 3},
        bonuses={"bravery": 0.5}
    )
    assert group.group_id == "patrol_alpha"
    assert 1 in group.member_ids
    assert group.bonuses["bravery"] == 0.5

def test_entity_integration():
    """Verify Entity and IdentityAspect absorb new Phase 3 fields."""
    rng = DeterministicRNG(123)
    builder = EntityBuilder(rng, 1)
    
    entity = (builder
              .kind("hero")
              .world_role(LifeRole.GUARD)
              .clique("ironfang")
              .household("hh_01")
              .home_building(101)
              .build())
    
    assert entity.identity.world_role == LifeRole.GUARD
    assert entity.identity.cluster_id == "ironfang"
    assert entity.identity.household_id == "hh_01"
    assert entity.identity.home_building_id == 101
    
    # Verify MindAspect extension
    # Builder already seeded default routines (3 for GUARD) and attachments (2 for GUARD)
    entity.mind.routine_profiles.append(RoutineProfile(
        routine_id="work_manual", routine_type="patrol", anchor_type="work"
    ))
    entity.mind.place_attachments.append(PlaceAttachment(
        location_pos=Vector2(5, 5), kind=AttachmentKind.FAVORITE_SPOT
    ))
    
    # GUARD seeded: sleep_cycle, guard_patrol, guard_rest + 1 manual = 4
    assert len(entity.mind.routine_profiles) == 4
    # GUARD seeded: HOME, TRAINING_GROUND + 1 manual = 3
    assert len(entity.mind.place_attachments) == 3

def test_world_state_registry():
    """Verify GroupRegistry integration in WorldState."""
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.core.world.grid import Grid
    from src_legacy.platform.spatial_hash import SpatialHash
    
    grid = Grid(10, 10)
    sh = SpatialHash(cell_size=5)
    ws = WorldState(seed=1, grid=grid, spatial_index=sh)
    
    group = GroupRecord(group_id="g1", kind=GroupKind.RAID_PACK)
    ws.group_registry["g1"] = group
    
    assert "g1" in ws.group_registry
    assert ws.group_registry["g1"].kind == GroupKind.RAID_PACK
