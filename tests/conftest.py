import pytest
from src.ai.flow_fields import FlowFieldManager

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all simulation singletons before each test to ensure total isolation."""
    FlowFieldManager.reset_instance()
    yield
