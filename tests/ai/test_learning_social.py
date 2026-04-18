import pytest
from src.testing.headless_regression_runner import HeadlessRunner
from src.core.entities.entity import Entity
from src.core.models.strategy import LeadRecord, LeadKind, ProjectRecord, ObjectiveRecord, ObjectiveKind, StrategicStatus
from src.config import SimulationConfig
from src.api.engine_manager import EngineManager
from src.core.gameplay.attributes import Attributes, AttributeCaps
from src.core.models.vectors import Vector2
from src.core.models.enums import AIState, InterpretedLifeEventKind

def test_intel_confirmation_by_sight():
    """Verify that seeing a person mentioned in a lead confirms it and boosts trust."""
    from src.core.models.strategy import ProjectKind
    config = SimulationConfig(world_seed=222, max_ticks=5, grid_width=10, grid_height=10)
    mgr = EngineManager(config)
    loop = mgr._loop
    
    # 1. Setup Hero and a Source
    hero = Entity(id=101, kind="hero")
    hero.progression.attributes = Attributes(int_=10, wis=10, per=10, cha=10)
    hero.progression.attribute_caps = AttributeCaps()
    hero.spatial.pos = Vector2(x=1, y=1)
    loop.world.add_entity(hero)
    
    source_id = "999"
    hero.mind.strategic.source_trust[source_id] = 0.5
    
    # 2. Setup a Target Person
    target_person = Entity(id=202, kind="hero")
    target_person.spatial.pos = Vector2(x=2, y=2) # Within vision
    loop.world.add_entity(target_person)
    
    # 3. Setup Lead and Objective
    lead = LeadRecord(
        lead_id="l1",
        kind=LeadKind.PERSON,
        subject="202",
        target_coords=Vector2(x=2, y=2),
        source_id=source_id,
        label="Target Person Lead",
        priority=1.0,
        certainty=0.5
    )
    hero.mind.strategic.leads.append(lead)
    
    obj = ObjectiveRecord(
        objective_id="o1",
        project_id="p1",
        kind=ObjectiveKind.INVESTIGATE,
        label="Investigate Person",
        target_pos=Vector2(x=2, y=2),
        leads=[lead]
    )
    proj = ProjectRecord(
        project_id="p1",
        kind=ProjectKind.INVESTIGATION,
        label="Main Investigation",
        objectives=[obj],
        active_objective_id="o1"
    )
    hero.mind.strategic.projects.append(proj)
    hero.mind.strategic.current_project_id = "p1"
    hero.mind.strategic.current_objective_id = "o1"
    hero.mind.decision.ai_state = AIState.INVESTIGATING
    
    # 4. Step simulation
    loop.tick_once()
    
    # 5. Assertions
    # Trust should have increased from 0.5
    assert hero.mind.strategic.source_trust[source_id] > 0.5
    
    # Lead should be tested and exhausted
    updated_lead = next(l for l in hero.mind.strategic.leads if l.lead_id == "l1")
    assert updated_lead.tested is True
    assert updated_lead.is_exhausted is True
    assert updated_lead.certainty > 0.5
    
    # Investigation should be cleared (WANDER state)
    assert hero.mind.decision.ai_state == AIState.WANDER
    
    # Social Event should be in memory log
    social_events = [e for e in hero.mind.narrative.memory_log if e.life_event_kind == InterpretedLifeEventKind.INTEL_CONFIRMED]
    assert len(social_events) > 0
    assert str(social_events[0].details["source_id"]) == str(source_id)
    
    mgr.stop()

def test_intel_refutation_by_exhaustion():
    """Verify that failing to find a target refutes the lead and drops trust."""
    from src.core.models.strategy import ProjectKind
    config = SimulationConfig(world_seed=333, max_ticks=5, grid_width=10, grid_height=10)
    mgr = EngineManager(config)
    loop = mgr._loop
    
    # 1. Setup Hero at candidate location
    hero = Entity(id=102, kind="hero")
    hero.progression.attributes = Attributes(int_=10, wis=10, per=10, cha=10)
    hero.progression.attribute_caps = AttributeCaps()
    hero.spatial.pos = Vector2(x=5, y=5)
    loop.world.add_entity(hero)
    
    source_id = "888"
    hero.mind.strategic.source_trust[source_id] = 0.5
    
    # 2. Setup Lead and Objective (Searching for someone NOT there)
    lead = LeadRecord(
        lead_id="l2",
        kind=LeadKind.PERSON,
        subject="303", # Non-existent ID
        target_coords=Vector2(x=5, y=5),
        source_id=source_id,
        label="Fake Person Lead",
        priority=1.0,
        certainty=0.5
    )
    hero.mind.strategic.leads.append(lead)
    
    obj = ObjectiveRecord(
        objective_id="o2",
        project_id="p2",
        kind=ObjectiveKind.INVESTIGATE,
        label="Investigate Fake Person",
        target_pos=Vector2(x=5, y=5),
        leads=[lead]
    )
    proj = ProjectRecord(
        project_id="p2",
        kind=ProjectKind.INVESTIGATION,
        label="Fake Investigation",
        objectives=[obj],
        active_objective_id="o2"
    )
    hero.mind.strategic.projects.append(proj)
    hero.mind.strategic.current_project_id = "p2"
    hero.mind.strategic.current_objective_id = "o2"
    hero.mind.decision.ai_state = AIState.INVESTIGATING
    
    # No search tiles left (SearchNarrowingService will return None)
    
    # 3. Step simulation
    loop.tick_once()
    
    # 4. Assertions
    # Trust should have decreased from 0.5
    assert hero.mind.strategic.source_trust[source_id] < 0.5
    
    # Lead should be tested and exhausted
    updated_lead = next(l for l in hero.mind.strategic.leads if l.lead_id == "l2")
    print(f"\nDEBUG_LEAD: {updated_lead.model_dump()}")
    assert updated_lead.tested is True
    assert updated_lead.is_exhausted is True
    assert updated_lead.certainty < 0.5
    
    # Social Event should be in memory log
    social_events = [e for e in hero.mind.narrative.memory_log if e.life_event_kind == InterpretedLifeEventKind.INTEL_REFUTED]
    assert len(social_events) > 0
    assert str(social_events[0].details["source_id"]) == source_id
    
    mgr.stop()
