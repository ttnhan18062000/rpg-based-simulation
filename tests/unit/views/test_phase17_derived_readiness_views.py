import pytest
from src.core.state import EntityState
from src.views.readiness import derived_views

def test_derived_readiness_views():
    entity = EntityState(id=1, kind="HERO")
    
    # 1. Combat readiness view
    combat_view = derived_views.build_combat_readiness(entity)
    assert combat_view.score == 1.0
    assert "combat" in combat_view.source_aspects_used

    # 2. Adventure readiness view
    adventure_view = derived_views.build_adventure_readiness(entity)
    assert adventure_view.score == 1.0
    assert "strategic" in adventure_view.source_aspects_used
