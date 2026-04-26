import pytest
import io
from contextlib import redirect_stdout
from src_legacy.core.entities.entity import Entity
from src_legacy.ui.cli.inspector import EntityInspector
from src_legacy.core.models.strategy import DirectiveRecord, ProjectRecord, ConcernRecord, LeadRecord, ObjectiveRecord
from src_legacy.core.models.enums import DirectiveKind, ProjectKind, StrategicStatus, ConcernKind, LeadKind, ObjectiveKind

@pytest.fixture
def clean_entity():
    """Create a minimal entity for inspection."""
    return Entity(id=1, kind="hero")

def test_render_strategic_domain_empty(clean_entity):
    """Smoke test: Render empty strategic domain."""
    f = io.StringIO()
    with redirect_stdout(f):
        EntityInspector.render_strategic_domain(clean_entity, current_tick=10)
    
    output = f.getvalue()
    assert "STRATEGIC DOMAIN" in output
    assert "No active projects" in output
    assert "No active directives" in output

def test_render_strategic_domain_populated(clean_entity):
    """Smoke test: Render populated strategic domain."""
    strat = clean_entity.mind.strategic
    strat.directives.append(DirectiveRecord(directive_id="d1", kind=DirectiveKind.PERSONAL, label="Survival First"))
    
    p1 = ProjectRecord(
        project_id="p1", 
        kind=ProjectKind.EXPLORATION, 
        label="Explore Ruins", 
        status=StrategicStatus.ACTIVE,
        committed_at=5
    )
    p1.objectives.append(ObjectiveRecord(objective_id="obj_reach", project_id="p1", kind=ObjectiveKind.VISIT, label="Reach Entrance"))
    strat.projects.append(p1)
    strat.current_project_id = "p1"
    strat.current_objective_id = "obj_reach"
    
    strat.concerns.append(ConcernRecord(concern_id="c1", kind=ConcernKind.THREAT, label="Nearby Goblins", priority=4.5))
    
    f = io.StringIO()
    with redirect_stdout(f):
        EntityInspector.render_strategic_domain(clean_entity, current_tick=10)
    
    output = f.getvalue()
    assert "STRATEGIC DOMAIN" in output
    assert "Survival First" in output
    assert "Explore Ruins" in output
    assert "Nearby Goblins" in output
    assert "LOCKED" not in output # Not locked yet

def test_render_uncertainty_layer_smoke(clean_entity):
    """Smoke test: Render uncertainty (leads, zones)."""
    strat = clean_entity.mind.strategic
    strat.leads.append(LeadRecord(lead_id="l1", kind=LeadKind.LOCATION, label="Hidden Cave", certainty=0.6, subject="TREASURE"))
    
    f = io.StringIO()
    with redirect_stdout(f):
        EntityInspector.render_uncertainty_layer(clean_entity)
    
    output = f.getvalue()
    assert "STRATEGIC UNCERTAINTY" in output
    assert "Hidden Cave" in output
    assert "cert: 0.60" in output

def test_inspector_full_render_smoke(clean_entity):
    """Smoke test: Run full inspection on an entity."""
    from unittest.mock import MagicMock
    registry = MagicMock()
    registry._current_tick = 42
    
    f = io.StringIO()
    with redirect_stdout(f):
        EntityInspector.inspect_full(clean_entity, registry)
    
    output = f.getvalue()
    assert "ENTITY INSPECTION" in output
    assert "STRATEGIC DOMAIN" in output
    assert "GENERAL INFO" in output
