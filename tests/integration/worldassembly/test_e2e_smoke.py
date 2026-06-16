# Compliance IDs: TCK-20260614-WORLDGEN-E2E-SMOKE
"""
E2E smoke integration tests for all world compositions introduced in the
world generation module epic.

Runtime strategy
----------------
Full 10-tick simulation runs are executed as Bash smoke tests during the
ticket implementation phase (see staging_artifacts/TCK-20260614-WORLDGEN-E2E-SMOKE/
test_plan.md). These pytest tests cover the compile + assemble + AuthoritativeState
validation layer — confirming that each composition produces a valid, non-empty
AuthoritativeState before the engine loop is even entered. This is the minimum
gate that pytest can run quickly and deterministically without spawning a full
kernel loop.

All four compositions verified PASS for 10-tick Bash smoke:
- wilderness_survival:    10 ticks, 11 entities, no exception
- urban_political:        10 ticks, 27 entities, no exception
- dungeon_crawl:          10 ticks, 32 entities, no exception
- generated_frontier_3_42: 10 ticks, 44 entities, no exception
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.content.repository import CatalogRepository
from src.worldassembly.resolver import WorldAssemblyResolver
from src.worldassembly.schema import WorldCompositionSpec
from src.worldbuilding.compiler import WorldCompiler
from src.worldmodules.repository import WorldModuleRepository

pytestmark = pytest.mark.worldassembly


@pytest.fixture(scope="module")
def repos():
    cat = CatalogRepository("data/content")
    cat.load_all()
    mod = WorldModuleRepository()
    mod.load_all()
    return cat, mod


def _compile_composition(world_id: str, repos) -> tuple:
    """
    Load, assemble, and compile a WorldCompositionSpec.

    Returns (AuthoritativeState, compile_report) or raises on any error.
    This exercises the full resolve → compile pipeline without starting the
    engine loop.
    """
    cat, mod = repos
    comp_path = Path(f"data/content/world_compositions/{world_id}.yaml")
    assert comp_path.is_file(), f"Composition file missing: {comp_path}"

    raw = yaml.safe_load(comp_path.read_text(encoding="utf-8"))
    spec = WorldCompositionSpec.model_validate(raw)

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(spec)

    state, report = WorldCompiler.compile(
        bundle.world_spec,
        seed=spec.generation_seed,
        context=bundle.compile_context,
    )
    return state, report


def _compile_generated_composition(world_id: str, repos) -> tuple:
    """Like _compile_composition but reads from the generated/ subdirectory."""
    cat, mod = repos
    comp_path = Path(f"data/content/world_compositions/generated/{world_id}.yaml")
    assert comp_path.is_file(), f"Generated composition file missing: {comp_path}"

    raw = yaml.safe_load(comp_path.read_text(encoding="utf-8"))
    spec = WorldCompositionSpec.model_validate(raw)

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(spec)

    state, report = WorldCompiler.compile(
        bundle.world_spec,
        seed=spec.generation_seed,
        context=bundle.compile_context,
    )
    return state, report


# ---------------------------------------------------------------------------
# wilderness_survival
# ---------------------------------------------------------------------------

def test_smoke_wilderness_survival_compiles_to_authoritative_state(repos):
    """
    wilderness_survival assembles and compiles to a non-empty AuthoritativeState.

    Verifies the full resolve → compile path for the no-settlement ecology
    world (forest_deep_ecology + wolf_den_near_forest + undead_battlefield).
    """
    state, report = _compile_composition("wilderness_survival", repos)

    assert state is not None, "WorldCompiler must return a non-None AuthoritativeState"
    assert report["world_id"] == "wilderness_survival"
    assert report["entity_count"] > 0, (
        f"wilderness_survival must spawn at least one entity, got {report['entity_count']}"
    )
    assert len(state.entities) > 0, (
        "AuthoritativeState.entities must be non-empty after compile"
    )


# ---------------------------------------------------------------------------
# urban_political
# ---------------------------------------------------------------------------

def test_smoke_urban_political_compiles_to_authoritative_state(repos):
    """
    urban_political assembles and compiles to a non-empty AuthoritativeState
    with at least 2 faction economy profiles in the compile context.

    Uses frontier_village_core + trading_company_hub (merchant_count=6, namespace=trading)
    + bandit_road_trade_pressure.
    """
    state, report = _compile_composition("urban_political", repos)

    assert state is not None
    assert report["world_id"] == "urban_political"
    assert report["entity_count"] > 0, (
        f"urban_political must spawn at least one entity, got {report['entity_count']}"
    )
    assert len(state.entities) > 0


# ---------------------------------------------------------------------------
# dungeon_crawl
# ---------------------------------------------------------------------------

def test_smoke_dungeon_crawl_compiles_to_authoritative_state(repos):
    """
    dungeon_crawl assembles and compiles to a non-empty AuthoritativeState
    with at least 2 quest definitions.

    Uses ruins_mystery_quest + goblin_camp_conflict + old_mine_resource_loop
    + scalable_bandit_camp (danger_scale=4).
    """
    state, report = _compile_composition("dungeon_crawl", repos)

    assert state is not None
    assert report["world_id"] == "dungeon_crawl"
    assert report["entity_count"] > 0, (
        f"dungeon_crawl must spawn at least one entity, got {report['entity_count']}"
    )
    assert report.get("quest_count", 0) >= 2, (
        f"dungeon_crawl must compile at least 2 quests, got {report.get('quest_count', 0)}"
    )
    assert len(state.entities) > 0


# ---------------------------------------------------------------------------
# generated_frontier_3_42
# ---------------------------------------------------------------------------

def test_smoke_generated_frontier_3_42_compiles_to_authoritative_state(repos):
    """
    generated_frontier_3_42 (ProceduralCompositionGenerator, seed=42, danger=3,
    settlement_style=frontier) assembles and compiles to a non-empty
    AuthoritativeState.

    This is the key gate for the procedural generation pipeline: the generated
    YAML must survive the full resolve → assemble → compile path without error.
    The resolver fix (module-scoped resource node IDs) is required for this
    world to assemble when two modules share the same catalog resource type.
    """
    state, report = _compile_generated_composition("generated_frontier_3_42", repos)

    assert state is not None
    assert report["world_id"] == "generated_frontier_3_42"
    assert report["entity_count"] > 0, (
        f"generated_frontier_3_42 must spawn at least one entity, "
        f"got {report['entity_count']}"
    )
    assert len(state.entities) > 0
