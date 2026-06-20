"""
tests/integration/scenarios/test_content_foundation.py

Epic 1.3D — Content Foundation scenario integration tests.

Three tests from the E13 test plan:
  1. test_all_world_compositions_have_two_scenarios  (unit, fast — schema only)
  2. test_quest_starts_in_urban_political            (integration, slow)
  3. test_crafting_chain_completes                   (integration, slow — SKIPPED)

Ticket: TCK-20260619-E13D-SCENARIOS
"""
from __future__ import annotations

import glob
import os

import pytest
import yaml


# ---------------------------------------------------------------------------
# Test 1: Schema-only — every target composition has ≥2 scenarios
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_all_world_compositions_have_two_scenarios():
    """Schema-only: every named world_composition has ≥2 scenarios.

    Loads all YAML documents from data/content/simulation_scenarios/ and
    counts scenario entries per world_composition field.  Does not start a
    kernel — purely validates the authored content files.
    """
    # Resolve path relative to repo root regardless of cwd
    repo_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    scenario_dir = os.path.join(repo_root, "data", "content", "simulation_scenarios")
    scenario_files = glob.glob(os.path.join(scenario_dir, "*.yaml"))

    assert scenario_files, (
        f"No scenario YAML files found in {scenario_dir}. "
        "Run TCK-20260619-E13D-SCENARIOS to author scenario files."
    )

    world_counts: dict[str, int] = {}
    for f in scenario_files:
        with open(f) as fh:
            # Each file may contain multiple YAML documents or a YAML list
            raw = fh.read()
        docs = list(yaml.safe_load_all(raw))
        for doc in docs:
            if isinstance(doc, list):
                # Flat list of scenario dicts
                for item in doc:
                    if isinstance(item, dict):
                        wc = item.get("world_composition")
                        if wc:
                            world_counts[wc] = world_counts.get(wc, 0) + 1
            elif isinstance(doc, dict):
                wc = doc.get("world_composition")
                if wc:
                    world_counts[wc] = world_counts.get(wc, 0) + 1

    for world_id in ["dungeon_crawl", "urban_political", "wilderness_survival"]:
        count = world_counts.get(world_id, 0)
        assert count >= 2, (
            f"{world_id} has {count} scenario(s), need ≥2. "
            f"Scenario counts found: {world_counts}"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_kernel(world_id: str, seed: int):
    """Build and return a ready Kernel for the given world_id and seed.

    Follows the pattern from test_balance_regression.py.
    Always call kernel.shutdown() in a finally block.
    """
    from src.worldbuilding.repository import WorldRepository
    from src.worldbuilding.compiler import WorldCompiler
    from src.engine.kernel import Kernel
    from src.config.profiles import RuntimeProfile, HardwareClass
    from src.platform.rng import DeterministicRNG

    repo = WorldRepository("data/worlds")
    spec = repo.load_world(world_id)
    state, _ = WorldCompiler.compile(spec, seed=seed)

    profile = RuntimeProfile(
        name="content-foundation-test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=2048,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=2000,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=500.0,
    )
    return Kernel(profile=profile, state=state, rng=DeterministicRNG(seed))


# ---------------------------------------------------------------------------
# Test 2: Quest activation in urban_political (400 ticks)
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.slow
def test_quest_starts_in_urban_political():
    """Assert at least 1 quest is active or completed in a 400-tick urban_political run.

    urban_political modules (frontier_village_core, trading_company_hub,
    bandit_road_trade_pressure) all have quest_definitions after TCK-20260619-E13A-QUEST-DEFS.
    This test verifies the runtime quest engine activates at least one quest.

    E13A dependency: DONE (2026-06-20).
    """
    from src.core.quests import QuestState, QuestStatus

    WORLD_ID = "urban_political"
    SEED = 42
    TICKS = 400

    kernel = _build_kernel(WORLD_ID, SEED)
    try:
        for _ in range(TICKS):
            kernel.tick_once()
    finally:
        kernel.shutdown()

    # Count entities with any quest in ACTIVE or COMPLETED status
    quests_found = []
    for entity in kernel.state.entities.values():
        for project_id, project in entity.strategic.projects.items():
            if isinstance(project, QuestState) and project.quest_status in (
                QuestStatus.ACTIVE,
                QuestStatus.COMPLETED,
                QuestStatus.REWARD_PENDING,
                QuestStatus.REWARDED,
            ):
                quests_found.append((entity.id, project_id, project.quest_status))

    assert len(quests_found) >= 1, (
        f"Expected at least 1 quest to activate in a {TICKS}-tick urban_political run "
        f"(seed={SEED}), but found 0. "
        "Check that quest_definitions in frontier_village_core, trading_company_hub, "
        "and bandit_road_trade_pressure are wired into the quest runtime engine. "
        "E13A (TCK-20260619-E13A-QUEST-DEFS) added the quest_definitions — if the "
        "quest engine does not activate them, this may require runtime engine integration work."
    )


# ---------------------------------------------------------------------------
# Test 3: Crafting chain (SKIPPED — settled_quarter not in any composition)
# ---------------------------------------------------------------------------

@pytest.mark.skip(
    reason=(
        "settled_quarter module (which provides blacksmith_service enabling the "
        "iron_ore→steel→ember_axe chain from TCK-20260619-E13C-RECIPES) is not "
        "included in any named world composition. No kernel run on a named world "
        "can exercise the gather→craft chain. "
        "Revisit trigger: when settled_quarter is added to a world composition "
        "(planned for Epic 2.3+ or E23 content expansion). "
        "The chain itself is verified by tests/unit/content/test_recipe_catalog_expansion.py "
        "tests: test_gather_craft_chain_iron_to_steel, test_gather_craft_chain_steel_to_ember_axe, "
        "test_full_gather_craft_chain_connected."
    )
)
@pytest.mark.integration
@pytest.mark.slow
def test_crafting_chain_completes():
    """Assert gather→craft chain produces output in a world with blacksmith.

    SKIPPED: settled_quarter (blacksmith_service provider) is not in any named
    world composition. See skip reason above for revisit trigger.
    """
    pass
