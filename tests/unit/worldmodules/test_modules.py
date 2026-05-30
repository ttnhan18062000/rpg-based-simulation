# Compliance IDs: WORLD-MOD-TEST
import pytest
from src.worldmodules.repository import WorldModuleRepository
from src.worldmodules.schema import WorldModuleSpec
from src.worldmodules.utils import topological_sort_modules


@pytest.fixture
def base_repo():
    repo = WorldModuleRepository("data/world_modules")
    repo.load_all()
    return repo


def test_reusable_module_loading(base_repo):
    """Verify that the module repository discovers and parses standard baseline module configs."""
    assert "plains_layout" in base_repo.modules
    assert "standard_villagers" in base_repo.modules

    m_layout = base_repo.get_module("plains_layout")
    assert m_layout is not None
    assert m_layout.module_type == "terrain"
    assert m_layout.provides == ["baseline_layout"]
    assert len(m_layout.regions) == 1
    assert m_layout.regions[0].id == "town_center"

    m_pop = base_repo.get_module("standard_villagers")
    assert m_pop is not None
    assert m_pop.module_type == "population"
    assert m_pop.requires == ["plains_layout"]
    assert len(m_pop.population_recipes) == 2

    # Check fingerprint hash is available
    assert base_repo.module_fingerprint("plains_layout") is not None


def test_topological_sort():
    """Verify Kahn's topological sort and determinism."""
    # Define three specifications with sequential dependencies: C requires B, B requires A
    # We pass mock specs (simple namespace dictionaries simulating pydantic class interfaces)
    class MockSpec:
        def __init__(self, requires):
            self.requires = requires

    graph = {
        "C": MockSpec(requires=["B"]),
        "B": MockSpec(requires=["A"]),
        "A": MockSpec(requires=[]),
    }

    order = topological_sort_modules(graph)
    assert order == ["A", "B", "C"]


def test_circular_dependency_checks():
    """Verify circular references raise structural error."""
    class MockSpec:
        def __init__(self, requires):
            self.requires = requires

    circular_graph = {
        "A": MockSpec(requires=["B"]),
        "B": MockSpec(requires=["A"]),
    }

    with pytest.raises(ValueError) as exc_info:
        topological_sort_modules(circular_graph)
    assert "Circular dependency detected" in str(exc_info.value)
