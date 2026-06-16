# Compliance IDs: WORLD-ASM-TEST
"""
Unit tests for quest_definitions wiring into WorldModuleSpec and assembly merge.
TCK-20260614-WORLDMOD-QUEST-MOD
"""
import pytest

from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldmodules.schema import WorldModuleSpec
from src.worldassembly.schema import WorldCompositionSpec, ModuleRefSpec
from src.worldassembly.resolver import WorldAssemblyResolver, AssemblyCollisionError
from src.worldbuilding.schema import QuestDefinition

pytestmark = pytest.mark.worldassembly


@pytest.fixture
def repos():
    cat = CatalogRepository("data/content")
    cat.load_all()
    mod = WorldModuleRepository("data/world_modules")
    mod.load_all()
    return cat, mod


def _make_module_with_quests(module_id: str, quest_defs: list[QuestDefinition]) -> WorldModuleSpec:
    """Build a minimal WorldModuleSpec stub with quest_definitions. No regions or populations."""
    return WorldModuleSpec(
        module_id=module_id,
        module_type="economy",
        display_name=f"Test Module {module_id}",
        quest_definitions=quest_defs,
    )


def _register(mod_repo: WorldModuleRepository, spec: WorldModuleSpec) -> None:
    mod_repo.modules[spec.module_id] = spec
    mod_repo.raw_data[spec.module_id] = spec.model_dump()


def _make_composition(*module_ids: str) -> WorldCompositionSpec:
    return WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="quest_merge_test",
        name="Quest Merge Test",
        module_refs=[
            ModuleRefSpec(module_id=m_id, enabled=True, order=idx)
            for idx, m_id in enumerate(module_ids)
        ],
    )


# ---------------------------------------------------------------------------
# Test 1: single module with quest_definitions → compiled WorldSpec has them
# with source_module set correctly
# ---------------------------------------------------------------------------

def test_single_module_quest_definitions(repos):
    """A module with one QuestDefinition produces a WorldSpec.quest_definitions entry
    with source_module stamped to the contributing module's module_id."""
    cat, mod = repos

    qd = QuestDefinition(
        id="mine_fetch_ore",
        type="fetch",
        required_participant_tags=["worker"],
        required_location_tags=["mine"],
        reward_budget=150,
    )
    spec = _make_module_with_quests("quest_module_a", [qd])
    _register(mod, spec)

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(_make_composition("quest_module_a"))

    world_spec = bundle.world_spec
    assert len(world_spec.quest_definitions) == 1
    assembled_qd = world_spec.quest_definitions[0]
    assert assembled_qd.id == "mine_fetch_ore"
    assert assembled_qd.type == "fetch"
    assert assembled_qd.source_module == "quest_module_a"


# ---------------------------------------------------------------------------
# Test 2: two modules with same quest id → AssemblyCollisionError naming both
# ---------------------------------------------------------------------------

def test_collision_raises_assembly_error(repos):
    """Two modules contributing a quest with the same id raise AssemblyCollisionError
    naming both contributing module IDs in the error message."""
    cat, mod = repos

    qd = QuestDefinition(id="shared_quest", type="hunt")
    spec_a = _make_module_with_quests("quest_module_b1", [qd])
    spec_b = _make_module_with_quests("quest_module_b2", [qd])
    _register(mod, spec_a)
    _register(mod, spec_b)

    resolver = WorldAssemblyResolver(cat, mod)
    with pytest.raises(AssemblyCollisionError) as exc_info:
        resolver.assemble(_make_composition("quest_module_b1", "quest_module_b2"))

    msg = str(exc_info.value)
    assert "shared_quest" in msg
    assert "quest_module_b1" in msg
    assert "quest_module_b2" in msg


# ---------------------------------------------------------------------------
# Test 3: module with no quest_definitions (empty list default) → no error,
# empty quest list in output
# ---------------------------------------------------------------------------

def test_empty_quest_definitions_no_error(repos):
    """A module with no quest_definitions (default empty list) assembles without error
    and the output WorldSpec has an empty quest_definitions list."""
    cat, mod = repos

    spec = WorldModuleSpec(
        module_id="quest_module_c",
        module_type="terrain",
        display_name="No Quests Module",
        # quest_definitions omitted — defaults to []
    )
    _register(mod, spec)

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(_make_composition("quest_module_c"))

    assert bundle.world_spec.quest_definitions == []


# ---------------------------------------------------------------------------
# Test 4: source_module matches the contributing module's module_id exactly
# ---------------------------------------------------------------------------

def test_source_module_matches_contributing_module(repos):
    """source_module on each assembled QuestDefinition exactly matches
    the module_id of the module that contributed it."""
    cat, mod = repos

    qd1 = QuestDefinition(id="escort_caravan", type="escort", reward_budget=200)
    qd2 = QuestDefinition(id="explore_ruins", type="explore", reward_budget=300)

    spec_a = _make_module_with_quests("quest_module_d1", [qd1])
    spec_b = _make_module_with_quests("quest_module_d2", [qd2])
    _register(mod, spec_a)
    _register(mod, spec_b)

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(_make_composition("quest_module_d1", "quest_module_d2"))

    by_id = {qd.id: qd for qd in bundle.world_spec.quest_definitions}
    assert len(by_id) == 2
    assert by_id["escort_caravan"].source_module == "quest_module_d1"
    assert by_id["explore_ruins"].source_module == "quest_module_d2"
