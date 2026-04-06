import os
import pytest
from src.ai.flow_fields import FlowFieldManager
from src.core.gameplay.items.item_registry import ITEM_REGISTRY

@pytest.fixture(autouse=True)
def test_env_setup():
    """Configure unit test environment for total isolation and speed."""
    os.environ["DISABLE_KAFKA"] = "1"
    os.environ["DISABLE_REDIS"] = "1"
    yield

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all simulation singletons before each test to ensure total isolation."""
    FlowFieldManager.reset_instance()
    ITEM_REGISTRY.clear()
    from src.core.registry.registry_loader import load_all_registries
    # Auto-load registries for tests if they expect items/classes to exist
    try:
        load_all_registries()
    except Exception:
        pass
    yield
