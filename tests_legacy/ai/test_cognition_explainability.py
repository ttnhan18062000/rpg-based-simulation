import pytest
from src_legacy.testing.headless_regression_runner import HeadlessRunner
from src_legacy.testing.assertions import load_json, assert_graph_integrity
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.strategy import ConcernRecord, ConcernKind
from src_legacy.config import SimulationConfig
from src_legacy.api.engine_manager import EngineManager
from src_legacy.utils.replay import ReplayRecorder
from src_legacy.core.gameplay.attributes import Attributes, AttributeCaps

def test_overload_metadata_population():
    """Verify that primary_overload_source and last_overload_tick are correctly populated in replay."""
    config = SimulationConfig(world_seed=111, max_ticks=5, grid_width=10, grid_height=10)
    mgr = EngineManager(config)
    loop = mgr._loop
    
    # 1. Setup a low-intel entity to force overload
    hero = Entity(id=505, kind="hero")
    hero.progression.attributes = Attributes(int_=1, wis=1, per=1, cha=1)
    hero.progression.attribute_caps = AttributeCaps()
    loop.world.add_entity(hero)
    
    # 2. Inject concerns to trigger overload (limit is small)
    for i in range(8):
        hero.mind.strategic.concerns.append(
            ConcernRecord(concern_id=f"ov_c_{i}", kind=ConcernKind.THREAT, label=f"Overload {i}", priority=5.0)
        )
    
    recorder = ReplayRecorder("logs/regression/explainability/replay.json", 111)
    
    # 3. Step simulation
    loop.tick_once()
    # Corrected arguments: loop.world.tick (int) and loop.last_applied (list)
    recorder.record_tick(loop.world.tick - 1, loop.last_applied, loop.world)
    recorder.flush()
    
    replay_data = load_json("logs/regression/explainability/replay.json")
    hero_snap = next(e for e in replay_data["ticks"][0]["entities"] if e["id"] == 505)
    strat = hero_snap["strategy"]
    
    # 4. Assert populations (ReplayRecorder flat structure)
    assert strat["is_overloaded"] is True
    assert strat["primary_overload_source"] == "complexity" 
    assert strat["last_overload_tick"] == 0 
    
    mgr.stop()

def test_personality_formula_impact():
    """Verify that personality archetypes and traits impact the capacity profile."""
    from src_legacy.ai.cognition_capacity import CognitionCapacityBuilder
    from src_legacy.core.aspects.mind import PersonalityProfile
    
    # Balanced Hero
    e1 = Entity(id=1, kind="hero")
    e1.progression.attributes = Attributes(int_=5, wis=5, per=5, cha=5)
    e1.progression.attribute_caps = AttributeCaps()
    e1.mind.decision.personality.archetype = "balanced"
    
    # Scholar Hero (more ambitious, higher int/wis cap)
    e2 = Entity(id=2, kind="hero")
    e2.progression.attributes = Attributes(int_=15, wis=15, per=15, cha=15)
    e2.progression.attribute_caps = AttributeCaps(int_cap=15, wis_cap=15, per_cap=15, cha_cap=15)
    e2.mind.decision.personality.archetype = "scholar"
    e2.mind.decision.personality.ambition = 1.0
    
    profile1 = CognitionCapacityBuilder.build(e1)
    profile2 = CognitionCapacityBuilder.build(e2)
    
    # Scholar should have significantly higher budget and detour depth
    assert profile2.planning_budget > profile1.planning_budget
    assert profile2.detour_depth_limit > profile1.detour_depth_limit

def test_inspector_smoke_coverage():
    """Smoke test to ensure EntityInspector (AIPresenter) doesn't crash with new fields."""
    from src_legacy.api.presenters.ai_presenter import AIPresenter
    from src_legacy.core.entities.entity import Entity
    from src_legacy.ai.cognition_capacity import CognitionCapacityBuilder
    
    hero = Entity(id=707, kind="hero")
    hero.progression.attributes = Attributes()
    hero.progression.attribute_caps = AttributeCaps()
    # Need to build a profile so schema fields are populated
    hero.mind.strategic.last_capacity_profile = CognitionCapacityBuilder.build(hero)
    
    # Force some state
    hero.mind.strategic.is_overloaded = True
    hero.mind.strategic.primary_overload_source = "leads"
    hero.mind.strategic.last_overload_tick = 42
    
    # This should not raise any Pydantic validation errors or AttributeErrors
    output = AIPresenter.get_explanation(hero)
    
    assert output.strategy.overload.is_overloaded is True
    assert output.strategy.overload.primary_overload_source == "leads"
    assert output.strategy.overload.last_overload_tick == 42
