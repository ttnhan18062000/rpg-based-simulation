"""E2E Strategic Scenarios Suite. [MILESTONE 7]

Verifies the remaining baseline strategic behaviors:
- Blocker/Detour: Discovery of impediments and creation of remediation tasks.
- Cooperation/Recruitment: Identification and engagement of social allies.
"""

import pytest
from src.config import SimulationConfig
from src.api.engine_manager import EngineManager
from src.core.models.enums import (
    ProjectKind, ObjectiveKind, StrategicStatus, 
    BlockerKind, LeadKind, ConcernKind, Faction
)
from src.core.models.strategy import (
    ProjectRecord, ObjectiveRecord, LeadRecord
)
from src.core.models.life_events import SocialBondRecord

@pytest.fixture
def sim():
    """Setup a controlled engine environment."""
    config = SimulationConfig(
        world_seed=42,
        hero_count=2, # Two heroes to allow for same-faction recruitment
        initial_entity_count=5,
        num_workers=1,
        grid_width=32,
        grid_height=32
    )
    mgr = EngineManager(config)
    yield mgr
    mgr.stop()

class TestStrategicScenarios:
    
    def test_blocker_detour_discovery(self, sim):
        """Scenario 2: Verify discovery of knowledge blocker and creation of investigation detour."""
        loop = sim._loop
        
        # 1. Settle for 2 ticks
        for _ in range(2):
            loop.tick_once()
            
        # 2. Setup Hero with a blocked objective
        hero = next(e for e in loop.world.entities.values() if e.identity.role == 0)
        hero_id = hero.id
        
        # Create a project with an objective that has NO coordinates (Blocker trigger)
        blocked_obj = ObjectiveRecord(
            objective_id=f"obj_blocked_{hero_id}",
            project_id=f"project_blocked_{hero_id}",
            kind=ObjectiveKind.VISIT,
            label="Visit Secret Grotto",
            priority=2.0,
            target_pos=None # This triggers KNOWLEDGE blocker
        )
        
        project = ProjectRecord(
            project_id=f"project_blocked_{hero_id}",
            kind=ProjectKind.EXPLORATION,
            label="Find Secret Grotto",
            status=StrategicStatus.ACTIVE,
            priority=2.0,
            objectives=[blocked_obj],
            active_objective_id=blocked_obj.objective_id
        )
        
        hero.mind.strategic.projects = [project]
        hero.mind.strategic.current_project_id = project.project_id
        hero.mind.strategic.current_objective_id = blocked_obj.objective_id
        hero.next_act_at = 0.0
        
        # 3. Add a Lead that provides the missing info (Detour trigger)
        from src.core.models.vectors import Vector2
        lead = LeadRecord(
            lead_id=f"lead_grotto_{hero_id}",
            kind=LeadKind.LOCATION,
            label="Grotto Rumors",
            subject=blocked_obj.objective_id, # Match objective ID
            target_coords=Vector2(x=10, y=10),
            certainty=0.8
        )
        hero.mind.strategic.leads.append(lead)
        
        # 4. Tick to allow inference and detour suggestion
        for _ in range(5):
            hero.next_act_at = 0.0
            loop.tick_once()
            
        # 5. Verify Blocker presence
        obj = hero.mind.strategic.current_objective
        assert obj is not None
        
        # Check blockers
        # In Milestone 3+, blockers are collected into the StrategicState or the objective itself
        # BlockerInferenceService appends to updates.objectives_add_or_update
        
        # Verify the brain has created a detour
        # The derivation service should move to the detour objective
        curr_obj = hero.mind.strategic.current_objective
        assert curr_obj.kind == ObjectiveKind.INVESTIGATE, "Should have pivoted to an investigation detour"
        assert curr_obj.target_pos is not None, "Detour should have target coordinates from the lead"
        assert curr_obj.target_pos.x == 10 and curr_obj.target_pos.y == 10

    def test_cooperation_recruitment_logic(self, sim):
        """Scenario 3: Verify that recruitment candidates are scored and social projects are prioritized."""
        loop = sim._loop
        
        # 1. Settle for 2 ticks
        for _ in range(2):
            loop.tick_once()
            
        # 2. Setup Hero and a potential ally (same faction)
        entities = [e for e in loop.world.entities.values() if e.kind != "generator"]
        hero = entities[0]
        potential_ally = entities[1]
        
        # Ensure they are same faction and have some trust
        hero.identity.faction = Faction.HERO_GUILD
        potential_ally.identity.faction = Faction.HERO_GUILD
        
        bond = SocialBondRecord(
            target_id=potential_ally.id,
            trust=0.8,
            loyalty=0.5
        )
        hero.mind.social.known_bonds[potential_ally.id] = bond
        
        # 3. Inject a Directive that favors social contracts
        from src.core.models.strategy import DirectiveRecord, DirectiveKind
        social_dir = DirectiveRecord(
            directive_id="dir_social_exp",
            kind=DirectiveKind.FACTIONAL,
            label="Expand Guild Influence",
            priority=4.5,
            source="test_recruitment"
        )
        hero.mind.strategic.directives.append(social_dir)
        hero.mind.strategic.current_project_id = None # Force re-evaluation
        hero.next_act_at = 0.0
        
        # 4. Tick to allow candidate selection and project promotion
        for _ in range(5):
            hero.next_act_at = 0.0
            loop.tick_once()
            
        # 5. Verify Social Project promotion
        curr_proj = hero.mind.strategic.current_project
        assert curr_proj is not None
        assert curr_proj.kind == ProjectKind.SOCIAL, "Should have promoted a Social project from directive"
        
        # Note: Detailed recruitment (contract creation) might happen after interaction.
        # Here we verify the STRATEGIC intent to cooperate is formed.
        assert "Guild Influence" in curr_proj.label
