import sys
import os
import logging
from unittest.mock import MagicMock

# Add project root to path
sys.path.append(os.path.abspath("."))

from src.core.entities.entity import Entity
from src.core.models.strategy import StrategicState, ProjectRecord, ProjectKind, StrategicStatus
from src.ui.cli.inspector import EntityInspector

# Setup mock registry
registry = MagicMock()
registry._current_tick = 50

# Setup entity with strategic state
entity = Entity(id=1, kind="hero")
entity.identity.display_name = "Test Hero"
entity.mind.strategic = StrategicState(
    current_project_id="test_proj",
    current_objective_id="test_obj",
    engaged_ticks=15,
    project_lock_until=100,
    projects=[
        ProjectRecord(
            project_id="test_proj",
            kind=ProjectKind.EXPLORATION,
            label="Test Exploration Project",
            status=StrategicStatus.ACTIVE,
            committed_at=20
        )
    ]
)

print("--- TESTING INSPECTOR ---")
try:
    EntityInspector.render_strategic_domain(entity, 50)
    print("\n--- TEST SUCCESSFUL ---")
except Exception as e:
    print(f"\n--- TEST FAILED: {e} ---")
    sys.exit(1)
