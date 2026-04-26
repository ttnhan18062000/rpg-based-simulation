import pytest
from unittest.mock import MagicMock
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.world_state import WorldState
from src_legacy.systems.gameplay.action_system import ActionSystem
from src_legacy.actions.base import StrategicUpdate, ActionProposal
from src_legacy.core.models.enums import ActionType
from src_legacy.core.models.strategy import DirectiveRecord, DirectiveKind, ProjectRecord, ProjectKind

# Ensure models are rebuilt for the test environment
StrategicUpdate.model_rebuild()

@pytest.mark.integration
class TestActionSystemStrategy:
    """Regression tests for StrategicUpdate integration in ActionSystem."""

    def test_apply_strategic_update_directives(self):
        # 1. Setup
        hero = Entity(id=1, kind="hero")
        world = MagicMock(spec=WorldState)
        world.tick = 50
        world.entities = {1: hero}
        # Mock get_entity
        world.get_entity.side_effect = lambda eid: world.entities.get(eid)
        
        # 2. Add directives
        d1 = DirectiveRecord(directive_id="dir_1", kind=DirectiveKind.PERSONAL, label="First")
        update = StrategicUpdate(directives_add=[d1])
        proposal = ActionProposal(actor_id=1, verb=ActionType.REST, updates=[update])
        
        ActionSystem._apply_updates(world, hero, [update], proposal)
        
        assert len(hero.mind.strategic.directives) == 1
        assert hero.mind.strategic.directives[0].directive_id == "dir_1"
        assert hero.mind.strategic.last_strategic_tick == 50
        
        # 3. Update existing directive (Merge by ID)
        d1_updated = DirectiveRecord(directive_id="dir_1", kind=DirectiveKind.PERSONAL, label="Updated")
        update2 = StrategicUpdate(directives_add=[d1_updated])
        ActionSystem._apply_updates(world, hero, [update2], proposal)
        
        assert len(hero.mind.strategic.directives) == 1
        assert hero.mind.strategic.directives[0].label == "Updated"
        
        # 4. Remove directive
        update3 = StrategicUpdate(directives_remove=["dir_1"])
        ActionSystem._apply_updates(world, hero, [update3], proposal)
        assert len(hero.mind.strategic.directives) == 0

    def test_apply_strategic_update_projects(self):
        hero = Entity(id=1, kind="hero")
        world = MagicMock(spec=WorldState)
        world.tick = 60
        world.entities = {1: hero}
        world.get_entity.side_effect = lambda eid: world.entities.get(eid)
        
        prj = ProjectRecord(project_id="prj_1", kind=ProjectKind.QUEST, label="Infiltration")
        update = StrategicUpdate(
            projects_add_or_update=[prj],
            current_project_id="prj_1"
        )
        ActionSystem._apply_updates(world, hero, [update], MagicMock())
        
        assert len(hero.mind.strategic.projects) == 1
        assert hero.mind.strategic.current_project_id == "prj_1"
        assert hero.mind.strategic.last_strategic_tick == 60
        
        # Update project status
        from src_legacy.core.models.strategy import StrategicStatus
        prj_done = ProjectRecord(project_id="prj_1", kind=ProjectKind.QUEST, label="Infiltration", status=StrategicStatus.RESOLVED)
        update2 = StrategicUpdate(projects_add_or_update=[prj_done])
        ActionSystem._apply_updates(world, hero, [update2], MagicMock())
        assert hero.mind.strategic.projects[0].status == StrategicStatus.RESOLVED
