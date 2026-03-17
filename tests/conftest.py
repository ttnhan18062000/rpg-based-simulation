import os
import sys
from pathlib import Path

import pytest

# Ensure the src directory is in the python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.registry_loader import load_all_registries

@pytest.fixture(scope="session", autouse=True)
def load_registries():
    """Load all game data registries before running any tests."""
    load_all_registries()
