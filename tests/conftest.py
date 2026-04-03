import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path

import pytest

# Ensure the src directory is in the python path

# Disable external infrastructure for tests by default
os.environ["DISABLE_KAFKA"] = "1"
os.environ["DISABLE_RABBITMQ"] = "1"
os.environ["NUM_WORKERS"] = "1"

from src.core.registry.registry_loader import load_all_registries

@pytest.fixture(scope="session", autouse=True)
def load_registries():
    """Load all game data registries before running any tests."""
    load_all_registries()
