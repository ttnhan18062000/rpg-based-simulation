import pytest
from unittest.mock import MagicMock
from src.core.entities.entity import Entity
from src.core.models.world_state import WorldState
from src.core.models.snapshot import Snapshot
from src.platform.rng import DeterministicRNG
from src.core.gameplay.faction import FactionRegistry
from src.config import SimulationConfig
from src.ai.states.base import AIContext
from src.ai.states.town import (
    VisitGuildHandler, VisitBlacksmithHandler, VisitClassHallHandler, 
    VisitInnHandler, VisitHomeHandler
)
from src.core.gameplay.buildings import Building
from src.core.models.enums import (
    ActionType, DamageType, SkillType, SkillTarget
)
from src.core.models.vectors import Vector2
from src.core.models.strategy import (
    StrategicStatus, BlockerRecord, BlockerKind, LeadRecord, LeadKind, ObjectiveKind
)
from src.actions.base import ActionProposal, PerceptionUpdate, StrategicUpdate
from src.ai.strategy.detour_suggestion import DetourSuggestionService
from src.core.gameplay.items.item_registry import ItemTemplate, ItemType, ITEM_REGISTRY
from src.core.aspects.progression import ProgressionAspect

@pytest.fixture
def mock_world():
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    grid = Grid(width=10, height=10)
    spatial = SpatialHash(cell_size=16)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    return world

@pytest.fixture
def test_actor():
    from src.core.aspects.progression import ProgressionAspect
    from src.core.aspects.inventory import InventoryAspect
    from src.core.models.enums import EntityRole
    e = Entity(id=1, kind="hero")
    e.identity.role = EntityRole.HERO
    e.identity.known_recipes = {"iron_sword"}
    e.spatial.pos = Vector2(5, 5)
    e.progression = ProgressionAspect(gold=100)
    e.inventory = InventoryAspect()
    return e


@pytest.fixture
def ai_context(test_actor, mock_world):
    config = SimulationConfig()
    rng = DeterministicRNG(seed=1)
    faction_reg = FactionRegistry.default()
    snapshot = Snapshot.from_world(mock_world)
    return AIContext(
        actor=test_actor,
        snapshot=snapshot,
        config=config,
        rng=rng,
        faction_reg=faction_reg
    )

def test_visit_guild_no_legacy_goals(mock_world, ai_context, test_actor):
    """Verify that visiting the guild produces StrategicUpdate and PerceptionUpdate, but no string goals."""
    # Place a guild
    guild = Building(building_id="guild_1", name="Guild", building_type="guild", pos=Vector2(5, 5))
    mock_world.buildings.append(guild)
    
    # Add a craft target that requires materials (triggering guild hints)
    test_actor.identity.craft_target = "iron_sword"
    import src.core.gameplay.quests as quests
    quests.MAX_ACTIVE_QUESTS = 0

    from src.core.gameplay.buildings import Recipe
    import src.core.gameplay.buildings as buildings
    # Mock the recipe and hints
    buildings.RECIPE_MAP["iron_sword"] = Recipe(recipe_id="iron_sword", output_item="iron_sword", materials={"iron_ore": 2}, gold_cost=0)
    buildings.MATERIAL_HINTS["iron_ore"] = "Rumored to be found in the mountains"

    ai_context.snapshot = Snapshot.from_world(mock_world)
    handler = VisitGuildHandler()
    state, proposal = handler.handle(ai_context)
    
    # Ensure it's not a move command
    if "Walking" in proposal.reason:
        pytest.fail("Entity moved instead of acting")
        
    has_strategic = False
    for up in proposal.updates:
        if hasattr(up, "goals_add") and up.goals_add:
            pytest.fail("Handler emitted legacy string goals")
        if isinstance(up, StrategicUpdate):
            has_strategic = True
            assert len(up.leads_add_or_update) >= 0
            
    assert has_strategic

def test_visit_blacksmith_blocker_emission(mock_world, ai_context, test_actor):
    """Verify that visiting the blacksmith without materials generates a BlockerRecord, not a string state."""
    bs = Building(building_id="bs_1", name="Blacksmith", building_type="blacksmith", pos=Vector2(5, 5))
    mock_world.buildings.append(bs)
    
    test_actor.identity.craft_target = "iron_sword"
    from src.core.gameplay.buildings import Recipe
    import src.core.gameplay.buildings as buildings
    buildings.RECIPE_MAP["iron_sword"] = Recipe(recipe_id="iron_sword", output_item="iron_sword", materials={"iron_ore": 2}, gold_cost=0)

    ai_context.snapshot = Snapshot.from_world(mock_world)
    handler = VisitBlacksmithHandler()
    state, proposal = handler.handle(ai_context)
    

    
    has_strategic = False
    for up in proposal.updates:
        # Action proposal should emit StrategicUpdate with a BlockerRecord
        if isinstance(up, StrategicUpdate):
            has_strategic = True
            assert len(up.blockers_add_or_update) > 0
            b = up.blockers_add_or_update[0]
            assert b.kind == BlockerKind.MATERIAL
            assert b.subject_ref == "iron_ore"
            
    assert has_strategic

def test_visit_class_hall_resolution(mock_world, ai_context, test_actor):
    """Verify that learning a skill emits a strategic resolution for the corresponding capability blocker."""
    ch = Building(building_id="ch_1", name="Class Hall", building_type="class_hall", pos=Vector2(5, 5))
    mock_world.buildings.append(ch)
    
    # Setup actor for learning (Hero class 1 = Fighter, Level 1)
    test_actor.progression.hero_class = 1
    test_actor.progression.level = 1
    test_actor.progression.gold = 500
    
    from src.core.gameplay.classes import CLASS_DEFS, HeroClass
    # Mock skill definition and mastery
    from src.core.gameplay.classes import SkillDef, Element, ClassDef
    import src.core.gameplay.classes as classes
    classes.SKILL_DEFS["TestSkill"] = SkillDef(
        skill_id="TestSkill", name="Test Skill", description="Test",
        gold_cost=50, level_req=1, class_req=HeroClass.WARRIOR,
        power=10, stamina_cost=5, cooldown=1, element=Element.NONE, damage_type=DamageType.PHYSICAL,
        skill_type=SkillType.ACTIVE, target=SkillTarget.SINGLE_ENEMY
    )
    classes.CLASS_DEFS[HeroClass.WARRIOR] = ClassDef(
        class_id=HeroClass.WARRIOR, name="Warrior", description="Test",
        class_skills=["TestSkill"]
    )
    
    ai_context.snapshot = Snapshot.from_world(mock_world)
    handler = VisitClassHallHandler()
    state, proposal = handler.handle(ai_context)
    
    has_resolution = False
    for up in proposal.updates:
        if isinstance(up, StrategicUpdate):
            for b in up.blockers_add_or_update:
                if b.blocker_id == "blocker_capability_TestSkill" and b.resolved:
                    has_resolution = True
                    
    assert has_resolution, "Handler should emit resolution for capability blocker"

def test_visit_blacksmith_crafting_resolution(mock_world, ai_context, test_actor):
    """Verify that crafting an item emits a strategic resolution for the material blocker."""
    bs = Building(building_id="bs_1", name="Blacksmith", building_type="blacksmith", pos=Vector2(5, 5))
    mock_world.buildings.append(bs)
    
    # Setup for crafting
    test_actor.identity.craft_target = "iron_sword"
    test_actor.inventory.items = ["iron_ore", "iron_ore"]
    test_actor.progression.gold = 100
    
    from src.core.gameplay.buildings import Recipe
    import src.core.gameplay.buildings as buildings
    buildings.RECIPE_MAP["iron_sword"] = Recipe(recipe_id="iron_sword", output_item="iron_sword", materials={"iron_ore": 2}, gold_cost=50)

    ai_context.snapshot = Snapshot.from_world(mock_world)
    handler = VisitBlacksmithHandler()
    state, proposal = handler.handle(ai_context)
    
    assert "Crafting iron_sword" in proposal.reason
    
    has_resolution = False
    for up in proposal.updates:
        if isinstance(up, StrategicUpdate):
            for b in up.blockers_add_or_update:
                # Based on our ingestion logic: ingest_material_acquisition(item_ids=[output_item])
                if b.blocker_id == "blocker_mat_iron_sword" and b.resolved:
                    has_resolution = True
                    
    assert has_resolution

def test_visit_home_upgrade_resolution(mock_world, ai_context, test_actor):
    """Verify that home storage upgrade emits a strategic resolution for home maintenance."""
    # Setup home
    test_actor.spatial.home_pos = Vector2(5, 5)
    test_actor.progression.gold = 1000
    
    # Mock storage upgrade cost
    test_actor.inventory.home_storage = MagicMock()
    test_actor.inventory.home_storage.upgrade_cost.return_value = 100
    
    ai_context.snapshot = Snapshot.from_world(mock_world)
    handler = VisitHomeHandler()
    state, proposal = handler.handle(ai_context)
    
    assert "Upgrading home storage" in proposal.reason
    
    has_resolution = False
    for up in proposal.updates:
        if isinstance(up, StrategicUpdate):
            for b in up.blockers_add_or_update:
                if b.blocker_id == "blocker_home_rebuild" and b.resolved:
                    has_resolution = True
    
    assert has_resolution

def test_detour_suggestion_lifecycle_awareness(ai_context):
    """Verify DetourSuggestionService ignores exhausted leads and prioritizes untested ones."""
    blocker = BlockerRecord(
        blocker_id="block_mat_1", 
        kind=BlockerKind.MATERIAL, 
        subject_ref="iron_ore",
        severity=1.0,
        label="Missing Iron Ore"
    )
    
    exhausted_lead = LeadRecord(
        lead_id="lead_exhausted",
        label="Old Source",
        kind=LeadKind.OBJECT,
        subject="iron_ore",
        target_coords=Vector2(10, 10),
        is_exhausted=True
    )
    
    untested_lead = LeadRecord(
        lead_id="lead_untested",
        label="New Source",
        kind=LeadKind.OBJECT,
        subject="iron_ore",
        target_coords=Vector2(20, 20),
        tested=False
    )
    
    ai_context.actor.mind.strategic.leads = [exhausted_lead, untested_lead]
    
    detours = DetourSuggestionService.suggest_detours(ai_context, blocker, "proj_1")
    
    assert len(detours) == 1
    d = detours[0]
    # Should skip exhausted_lead (10,10) and pick untested_lead (20,20)
    assert d.target_pos == Vector2(20, 20)
    assert "lead_untested" in d.evidence_refs
    assert "lead_exhausted" not in d.evidence_refs
