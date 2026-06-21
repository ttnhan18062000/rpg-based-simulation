"""
tests/unit/campaigns/test_campaign_orchestrator.py
────────────────────────────────────────────────────────────────────────────────
Unit tests for CampaignOrchestrator (TCK-20260619-E32C-ORCHESTRATOR).

All tests use mock ScenarioRuntimeService — no real Kernel ticks.
Architecture guard tests (TC-14, TC-15) live at the bottom of this file.
"""
from __future__ import annotations

import ast
import dataclasses
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.domains.campaigns.orchestrator import (
    CampaignManifest,
    CampaignOrchestrator,
    CarryForwardRules,
)
from src.domains.campaigns.state import (
    CampaignState,
    EntityCarryForward,
    EpisodeSummary,
    FactionCarryForward,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_manifest(n_episodes: int = 3, base_seed: int = 0) -> CampaignManifest:
    """Minimal manifest with n mocked episode specs."""
    episodes = [MagicMock() for _ in range(n_episodes)]
    return CampaignManifest(id="test_campaign", episodes=episodes, base_seed=base_seed)


def _make_mock_final_state(entities=None) -> MagicMock:
    """Build a mock AuthoritativeState with a controlled entities dict."""
    state = MagicMock()
    state.entities = entities or {}
    return state


def _make_mock_entity(
    entity_id: int = 1,
    level: int = 5,
    xp: int = 1200,
    faction: int = 1,
    lifecycle_active: bool = True,
    combat_alive: bool = True,
    reputation: float = 1.3,
    equip_slots: dict | None = None,
    equip_durability: dict | None = None,
) -> MagicMock:
    """Build a mock EntityState with controlled field values."""
    entity = MagicMock()
    entity.identity.evolution_level = level
    entity.identity.evolution_points = xp
    entity.identity.faction = faction
    entity.lifecycle.active = lifecycle_active
    entity.combat.alive = combat_alive
    entity.social.public_reputation = reputation
    entity.equipment.slots = equip_slots or {}
    entity.equipment.durability = equip_durability or {}
    return entity


def _run_episode_with_mock_svc(
    orchestrator: CampaignOrchestrator,
    final_state: MagicMock,
    tick: int = 50,
) -> EpisodeSummary:
    """Run one episode by patching ScenarioRuntimeService at its source module."""
    mock_svc = MagicMock()
    mock_svc.final_state = final_state
    mock_svc.tick = tick

    # Patch at the source module since ScenarioRuntimeService is imported
    # inside run_episode() (deferred import), not at orchestrator module level.
    with patch(
        "src.engine.scenario_runtime.ScenarioRuntimeService",
        return_value=mock_svc,
    ):
        return orchestrator.run_episode()


# ---------------------------------------------------------------------------
# TC-4: Construction with initial state
# ---------------------------------------------------------------------------

def test_orchestrator_constructs_with_initial_state():
    """TC-4: CampaignOrchestrator constructs correctly from a CampaignManifest."""
    manifest = _make_manifest(n_episodes=3)
    orch = CampaignOrchestrator(manifest)

    assert orch.state.campaign_id == "test_campaign"
    assert orch.state.episode_index == 0
    assert orch.state.episode_history == []
    assert orch.state.persistent_entities == {}
    assert orch.state.persistent_factions == {}


# ---------------------------------------------------------------------------
# TC-5: Entity carry-forward extraction
# ---------------------------------------------------------------------------

def test_advance_state_extracts_entity_carry_forward():
    """TC-5: _extract_entity_carry_forwards correctly maps all entity fields."""
    from src.core.models.inventory import EquipSlot

    manifest = _make_manifest()
    orch = CampaignOrchestrator(manifest)

    mock_entity = _make_mock_entity(
        entity_id=1,
        level=5,
        xp=1200,
        lifecycle_active=True,
        reputation=1.3,
        equip_slots={EquipSlot.MAIN_HAND: "sword_iron"},
        equip_durability={EquipSlot.MAIN_HAND: 0.9},
    )
    dead_entity = _make_mock_entity(entity_id=2, lifecycle_active=False)

    final_state = _make_mock_final_state(entities={1: mock_entity, 2: dead_entity})
    result = orch._extract_entity_carry_forwards(final_state)

    assert result[1].level == 5
    assert result[1].xp == 1200
    assert result[1].alive is True
    assert result[1].reputation == pytest.approx(1.3)
    assert result[1].equipment["slots"]["MAIN_HAND"] == "sword_iron"
    assert result[1].equipment["durability"]["MAIN_HAND"] == pytest.approx(0.9)
    assert result[2].alive is False


# ---------------------------------------------------------------------------
# TC-6: Faction carry-forward synthesis
# ---------------------------------------------------------------------------

def test_advance_state_synthesizes_faction_carry_forward():
    """TC-6: _extract_faction_carry_forwards synthesizes alive status correctly."""
    manifest = _make_manifest()
    orch = CampaignOrchestrator(manifest)

    # faction 1: one active, one inactive → alive
    entity_1a = _make_mock_entity(entity_id=1, faction=1, lifecycle_active=True)
    entity_1b = _make_mock_entity(entity_id=2, faction=1, lifecycle_active=False)
    # faction 2: all inactive → destroyed
    entity_2 = _make_mock_entity(entity_id=3, faction=2, lifecycle_active=False)

    final_state = _make_mock_final_state(
        entities={1: entity_1a, 2: entity_1b, 3: entity_2}
    )
    result = orch._extract_faction_carry_forwards(final_state)

    assert result["faction_1"].alive is True
    assert result["faction_2"].alive is False
    assert result["faction_1"].faction_id == "faction_1"
    assert result["faction_2"].faction_id == "faction_2"


# ---------------------------------------------------------------------------
# TC-7: run_episode appends to episode_history
# ---------------------------------------------------------------------------

def test_run_episode_appends_to_episode_history():
    """TC-7: run_episode() increments episode_index and appends EpisodeSummary."""
    manifest = _make_manifest(n_episodes=2)
    orch = CampaignOrchestrator(manifest)

    final_state = _make_mock_final_state(entities={})
    summary = _run_episode_with_mock_svc(orch, final_state, tick=50)

    assert len(orch.state.episode_history) == 1
    assert orch.state.episode_index == 1
    assert summary.episode_index == 0
    assert summary.completed_tick == 50
    assert orch.state.episode_history[0].episode_index == 0
    assert orch.state.episode_history[0].completed_tick == 50


# ---------------------------------------------------------------------------
# TC-8: run_episode raises when no episodes remain
# ---------------------------------------------------------------------------

def test_run_episode_raises_when_no_episodes_remain():
    """TC-8: run_episode() raises RuntimeError when episode_index >= len(episodes)."""
    manifest = _make_manifest(n_episodes=1)
    orch = CampaignOrchestrator(manifest)

    # Exhaust the single episode.
    final_state = _make_mock_final_state(entities={})
    _run_episode_with_mock_svc(orch, final_state)

    with pytest.raises(RuntimeError, match="No more episodes"):
        orch.run_episode()


# ---------------------------------------------------------------------------
# TC-9: Dead entity excluded from next episode spawn
# ---------------------------------------------------------------------------

def test_dead_entity_excluded_from_next_episode_spawn():
    """TC-9: _get_spawn_entities() excludes entities with alive=False."""
    manifest = _make_manifest()
    orch = CampaignOrchestrator(manifest)

    orch.state.persistent_entities[5] = EntityCarryForward(
        entity_id=5, level=3, xp=500, equipment={}, reputation=0.5, alive=False
    )
    orch.state.persistent_entities[6] = EntityCarryForward(
        entity_id=6, level=2, xp=200, equipment={}, reputation=0.3, alive=True
    )

    spawn = orch._get_spawn_entities()
    assert 5 not in spawn
    assert 6 in spawn


# ---------------------------------------------------------------------------
# TC-10: Destroyed faction excluded from next episode spawn
# ---------------------------------------------------------------------------

def test_destroyed_faction_excluded_from_next_episode_spawn():
    """TC-10: _get_spawn_factions() excludes factions with alive=False."""
    manifest = _make_manifest()
    orch = CampaignOrchestrator(manifest)

    orch.state.persistent_factions["faction_2"] = FactionCarryForward(
        faction_id="faction_2", alive=False, tension=0.0
    )
    orch.state.persistent_factions["faction_3"] = FactionCarryForward(
        faction_id="faction_3", alive=True, tension=0.2
    )

    spawn = orch._get_spawn_factions()
    assert "faction_2" not in spawn
    assert "faction_3" in spawn


# ---------------------------------------------------------------------------
# TC-11: Equipment keys are strings in carry-forward
# ---------------------------------------------------------------------------

def test_equipment_keys_are_strings_in_carry_forward():
    """TC-11: Equipment EquipSlot enum keys are stringified in EntityCarryForward."""
    from src.core.models.inventory import EquipSlot

    manifest = _make_manifest()
    orch = CampaignOrchestrator(manifest)

    mock_entity = _make_mock_entity(
        entity_id=1,
        equip_slots={EquipSlot.MAIN_HAND: "sword"},
        equip_durability={EquipSlot.MAIN_HAND: 0.8},
    )
    final_state = _make_mock_final_state(entities={1: mock_entity})
    result = orch._extract_entity_carry_forwards(final_state)

    slot_keys = list(result[1].equipment["slots"].keys())
    dur_keys = list(result[1].equipment["durability"].keys())

    # All keys must be strings, not EquipSlot enums.
    assert all(isinstance(k, str) for k in slot_keys), f"Non-string slot keys: {slot_keys}"
    assert all(isinstance(k, str) for k in dur_keys), f"Non-string durability keys: {dur_keys}"
    assert "MAIN_HAND" in result[1].equipment["slots"]
    assert result[1].equipment["slots"]["MAIN_HAND"] == "sword"


# ---------------------------------------------------------------------------
# TC-12: alive uses lifecycle.active, not combat.alive
# ---------------------------------------------------------------------------

def test_alive_uses_lifecycle_active_not_combat_alive():
    """TC-12: EntityCarryForward.alive maps to lifecycle.active, not combat.alive."""
    manifest = _make_manifest()
    orch = CampaignOrchestrator(manifest)

    # lifecycle.active=False, combat.alive=True (permadeath logic)
    permadead = _make_mock_entity(
        entity_id=1, lifecycle_active=False, combat_alive=True
    )
    # lifecycle.active=True, combat.alive=False (in-combat-dead, lifecycle active)
    in_combat_dead = _make_mock_entity(
        entity_id=2, lifecycle_active=True, combat_alive=False
    )

    final_state = _make_mock_final_state(
        entities={1: permadead, 2: in_combat_dead}
    )
    result = orch._extract_entity_carry_forwards(final_state)

    assert result[1].alive is False, "lifecycle.active=False must yield alive=False"
    assert result[2].alive is True, "lifecycle.active=True must yield alive=True"


# ---------------------------------------------------------------------------
# TC-13: EpisodeSummary has correct index and tick
# ---------------------------------------------------------------------------

def test_episode_summary_has_correct_index_and_tick():
    """TC-13: EpisodeSummary built from run_episode() has correct episode_index and completed_tick."""
    manifest = _make_manifest(n_episodes=2)
    orch = CampaignOrchestrator(manifest)

    final_state = _make_mock_final_state(entities={})
    summary = _run_episode_with_mock_svc(orch, final_state, tick=75)

    assert summary.episode_index == 0
    assert summary.completed_tick == 75


# ---------------------------------------------------------------------------
# TC-14: state.py has no engine imports (architecture guard)
# ---------------------------------------------------------------------------

def test_state_module_has_no_engine_imports():
    """TC-14: Guard-4 — state.py must not import from src.engine or src.core.state."""
    src_text = Path("src/domains/campaigns/state.py").read_text()
    tree = ast.parse(src_text)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", "") or ""
            assert not mod.startswith("src.engine"), (
                f"state.py must not import from src.engine, found: {mod}"
            )
            assert not mod.startswith("src.core.state"), (
                f"state.py must not import from src.core.state, found: {mod}"
            )


# ---------------------------------------------------------------------------
# TC-15: CampaignState and CampaignOrchestrator co-importable
# ---------------------------------------------------------------------------

def test_campaign_state_importable_alongside_orchestrator():
    """TC-15: state.py and orchestrator.py co-exist without ImportError."""
    from src.domains.campaigns.state import CampaignState
    from src.domains.campaigns.orchestrator import CampaignOrchestrator

    assert CampaignState is not None
    assert CampaignOrchestrator is not None
