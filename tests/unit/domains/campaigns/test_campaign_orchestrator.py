"""
tests/unit/domains/campaigns/test_campaign_orchestrator.py
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
    """Minimal manifest with n mocked episode specs.

    TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY: `world_composition` is set to a
    real, tiny unit-tier corpus world (`unit_faction_tension`) rather than left
    as a bare MagicMock — `_build_initial_state()` now really calls
    `WorldRepository.load_world_with_context(spec.world_composition)`, which
    needs a real string world_id, not a MagicMock.

    TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING: `id`/`perspective`/
    `initial_conditions` are now also set to real values — `_build_initial_state()`'s
    episode-0 branch calls `CatalogScenarioStateBuilder.build()` (via
    `ScenarioSetupResolver.resolve()`), which builds a real, strictly-typed
    `ResolvedScenarioSetup` pydantic model from `scenario.id`/`.perspective` — a bare
    MagicMock for either now fails pydantic's `string_type` validation instead of
    silently working. `unit_faction_tension` has no `default_perspectives` declared
    (`_validate_perspective()` skips validation when that list is empty), so any real
    perspective string is accepted; `hero_guild_perspective` is used here purely for
    consistency with the other real-scenario tests in this file, not because this
    world requires it. Every existing entity/faction/carry-forward assertion in this
    file that does NOT touch the episode-0 branch is unaffected — confirmed by
    re-running the full file after this change; the one assertion that WAS
    (deliberately) written against an always-empty episode-0 world is updated
    separately, see `test_build_initial_state_episode_zero_carries_compiled_regions_and_places`.
    """
    episodes = []
    for i in range(n_episodes):
        ep = MagicMock()
        ep.id = f"test_campaign_ep{i}"
        ep.world_composition = "unit_faction_tension"
        ep.perspective = "hero_guild_perspective"
        ep.initial_conditions = {}
        episodes.append(ep)
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
    position: tuple[float, float] = (10.0, 20.0),
    kind: str = "human",
    role: int = 0,
    properties: dict | None = None,
    traits: set | None = None,
    personality: dict | None = None,
) -> MagicMock:
    """Build a mock EntityState with controlled field values."""
    entity = MagicMock()
    entity.kind = kind
    entity.identity.evolution_level = level
    entity.identity.evolution_points = xp
    entity.identity.faction = faction
    entity.identity.role = role
    entity.identity.properties = properties or {}
    entity.identity.traits = traits or set()
    personality = personality or {"greed": 0.0, "bravery": 0.0, "sociability": 0.0, "industry": 0.0}
    entity.identity.personality.greed = personality["greed"]
    entity.identity.personality.bravery = personality["bravery"]
    entity.identity.personality.sociability = personality["sociability"]
    entity.identity.personality.industry = personality["industry"]
    entity.lifecycle.active = lifecycle_active
    entity.combat.alive = combat_alive
    entity.social.public_reputation = reputation
    entity.equipment.slots = equip_slots or {}
    entity.equipment.durability = equip_durability or {}
    entity.navigation.position = position
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
# TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION:
# _extract_entity_carry_forwards captures last_position unconditionally
# ---------------------------------------------------------------------------

def test_extract_entity_carry_forward_captures_last_position():
    manifest = _make_manifest()
    orch = CampaignOrchestrator(manifest)

    mock_entity = _make_mock_entity(entity_id=1, position=(42.0, -7.0))
    final_state = _make_mock_final_state(entities={1: mock_entity})
    result = orch._extract_entity_carry_forwards(final_state)

    assert result[1].last_position == (42.0, -7.0)


def test_extract_entity_carry_forward_last_position_not_gated_by_carry_rules():
    """Unlike level/xp/reputation, last_position is not an opt-in carry-forward
    rule -- it's captured even when carry_level/carry_xp/carry_reputation are off."""
    manifest = _make_manifest()
    manifest = dataclasses.replace(
        manifest,
        carry_forward_rules=CarryForwardRules(
            carry_level=False, carry_xp=False, carry_reputation=False, carry_equipment=False,
        ),
    )
    orch = CampaignOrchestrator(manifest)

    mock_entity = _make_mock_entity(entity_id=1, position=(5.0, 5.0))
    final_state = _make_mock_final_state(entities={1: mock_entity})
    result = orch._extract_entity_carry_forwards(final_state)

    assert result[1].last_position == (5.0, 5.0)
    assert result[1].level == 1  # confirms carry_level=False actually took effect


# ---------------------------------------------------------------------------
# TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-RECONSTRUCTION:
# _extract_entity_carry_forwards captures kind/role/faction/properties/traits/
# personality unconditionally, matching last_position's own treatment.
# ---------------------------------------------------------------------------

def test_extract_entity_carry_forward_captures_identity_fields():
    manifest = _make_manifest()
    orch = CampaignOrchestrator(manifest)

    mock_entity = _make_mock_entity(
        entity_id=1,
        kind="goblin",
        role=2,
        faction=3,
        properties={"archetype_id": "goblin_raider", "faction_id": "monster_horde"},
        traits={"brave", "cunning"},
        personality={"greed": 0.4, "bravery": 0.7, "sociability": 0.1, "industry": 0.2},
    )
    final_state = _make_mock_final_state(entities={1: mock_entity})
    result = orch._extract_entity_carry_forwards(final_state)

    assert result[1].kind == "goblin"
    assert result[1].role == 2
    assert result[1].faction == 3
    assert result[1].properties == {"archetype_id": "goblin_raider", "faction_id": "monster_horde"}
    assert set(result[1].traits) == {"brave", "cunning"}
    assert result[1].personality == {
        "greed": 0.4, "bravery": 0.7, "sociability": 0.1, "industry": 0.2
    }


def test_extract_entity_carry_forward_identity_fields_not_gated_by_carry_rules():
    manifest = _make_manifest()
    manifest = dataclasses.replace(
        manifest,
        carry_forward_rules=CarryForwardRules(
            carry_level=False, carry_xp=False, carry_reputation=False, carry_equipment=False,
        ),
    )
    orch = CampaignOrchestrator(manifest)

    mock_entity = _make_mock_entity(entity_id=1, kind="goblin", role=2, faction=3)
    final_state = _make_mock_final_state(entities={1: mock_entity})
    result = orch._extract_entity_carry_forwards(final_state)

    assert result[1].kind == "goblin"
    assert result[1].role == 2
    assert result[1].faction == 3


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


# ---------------------------------------------------------------------------
# TCK-20260824-GRIEF-NEMESIS-REACHABILITY — Step 1a: run_id plumbing
# ---------------------------------------------------------------------------

def test_episode_summary_carries_run_id():
    """Step 1a: run_episode() captures svc.run_id into EpisodeSummary.run_id."""
    manifest = _make_manifest(n_episodes=1)
    orch = CampaignOrchestrator(manifest)

    mock_svc = MagicMock()
    mock_svc.final_state = _make_mock_final_state(entities={})
    mock_svc.tick = 10
    mock_svc.run_id = "run_12345_abcd"

    with patch(
        "src.engine.scenario_runtime.ScenarioRuntimeService",
        return_value=mock_svc,
    ):
        summary = orch.run_episode()

    assert summary.run_id == "run_12345_abcd"
    assert orch.state.episode_history[0].run_id == "run_12345_abcd"


def test_episode_summary_run_id_defaults_empty_when_svc_run_id_none():
    """Step 1a: a falsy svc.run_id (e.g. None) must not propagate as None — EpisodeSummary.run_id
    stays a str, defaulting to ''."""
    manifest = _make_manifest(n_episodes=1)
    orch = CampaignOrchestrator(manifest)

    mock_svc = MagicMock()
    mock_svc.final_state = _make_mock_final_state(entities={})
    mock_svc.tick = 10
    mock_svc.run_id = None

    with patch(
        "src.engine.scenario_runtime.ScenarioRuntimeService",
        return_value=mock_svc,
    ):
        summary = orch.run_episode()

    assert summary.run_id == ""


# ---------------------------------------------------------------------------
# TCK-20260824-GRIEF-NEMESIS-REACHABILITY — Step 1b: event_recorder wiring
# ---------------------------------------------------------------------------

def test_run_episode_passes_event_recorder_to_scenario_runtime():
    """Step 1b: run_episode() must wire self._scenario_event_recorder through to
    ScenarioRuntimeService — previously silently dropped at orchestrator.py:172."""
    manifest = _make_manifest(n_episodes=1)
    spy_recorder = MagicMock()
    orch = CampaignOrchestrator(manifest, scenario_event_recorder=spy_recorder)

    mock_svc = MagicMock()
    mock_svc.final_state = _make_mock_final_state(entities={})
    mock_svc.tick = 10
    mock_svc.run_id = "run_x"

    with patch(
        "src.engine.scenario_runtime.ScenarioRuntimeService",
        return_value=mock_svc,
    ) as mock_ctor:
        orch.run_episode()

    _, kwargs = mock_ctor.call_args
    assert kwargs.get("scenario_event_recorder") is spy_recorder


# ---------------------------------------------------------------------------
# TCK-20260824-GRIEF-NEMESIS-REACHABILITY — Step 5b: episode-teardown flush ordering
# ---------------------------------------------------------------------------

def test_run_episode_flushes_pending_grief_triggers_before_reading_final_state():
    """Step 5b: flush_pending_grief_triggers() must be called after svc.start() and
    strictly before final_state is read (final_state returns a live-at-read-time
    reference that the flush reassigns)."""
    manifest = _make_manifest(n_episodes=1)
    orch = CampaignOrchestrator(manifest)

    call_order = []
    mock_svc = MagicMock()
    mock_svc.start.side_effect = lambda *a, **k: call_order.append("start")
    mock_svc.flush_pending_grief_triggers.side_effect = lambda: call_order.append("flush")
    type(mock_svc).final_state = property(
        lambda self: call_order.append("read_final_state") or _make_mock_final_state(entities={})
    )
    mock_svc.tick = 5
    mock_svc.run_id = "run_y"

    with patch(
        "src.engine.scenario_runtime.ScenarioRuntimeService",
        return_value=mock_svc,
    ):
        orch.run_episode()

    assert call_order.index("start") < call_order.index("flush") < call_order.index(
        "read_final_state"
    )


# ---------------------------------------------------------------------------
# TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY — Region/Place carry into per-episode
# AuthoritativeState (both the episode-0 and survivor-reconstruction branches)
# ---------------------------------------------------------------------------

def _real_episode_spec(world_id: str = "unit_faction_tension") -> MagicMock:
    """Episode spec whose world_composition names a real, tiny corpus world.

    TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING: `id`/`perspective`/
    `initial_conditions` set to real values for the same reason as `_make_manifest()`,
    above — `ScenarioSetupResolver.resolve()` now genuinely runs for the episode-0
    branch and needs real strings, not MagicMock attributes.
    """
    spec = MagicMock()
    spec.id = f"test_spec_{world_id}"
    spec.world_composition = world_id
    spec.perspective = "hero_guild_perspective"
    spec.initial_conditions = {}
    return spec


def test_build_initial_state_episode_zero_carries_compiled_regions_and_places():
    """Episode 0 (no surviving carry-forwards) must get real compiled regions/places,
    AND real entities.

    Before TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY this branch returned a bare
    AuthoritativeState(tick=0, seed=...) with regions={} / places={}.

    TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING: before that ticket, this same
    branch also always returned `entities={}` — this test used to assert exactly that
    (`state.entities == {}`) as an intentional invariant. That was the actual bug the
    later ticket fixed (`campaign_life_arc` ran with zero entities for its entire
    episode); the old assertion was correct for the code as it stood, but described a
    real defect, not a design contract worth preserving. Updated to assert the new,
    intended behavior instead of silently deleting the coverage — deliberately NOT
    just relaxed to "don't crash"; a real non-empty entities dict is now asserted.
    """
    orch = CampaignOrchestrator(_make_manifest(n_episodes=1))
    assert orch.state.persistent_entities == {}, "precondition: episode-0 branch"

    state = orch._build_initial_state(7, _real_episode_spec())

    assert state.regions, (
        "episode 0 must receive real compiled regions — an empty dict is the exact "
        "pre-fix bug TCK-20260904-CAMPAIGN-REGION-PLACE-CARRY exists to close"
    )
    assert all(
        hasattr(region, "id") and region.id == region_id
        for region_id, region in state.regions.items()
    ), "compiled regions must be real RegionState objects keyed by their own id"
    # places is a real compiled dict (may legitimately be empty for a world whose
    # modules declare no Places — assert the type/carry, not a non-empty count).
    assert isinstance(state.places, dict)
    assert state.tick == 0 and state.seed == 7, "seed/tick contract unchanged"
    assert state.entities, (
        "episode 0 must receive real spawned entities — an empty dict is the exact "
        "pre-fix bug TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING exists to close "
        "(campaign_life_arc previously ran with zero entities for its entire episode)"
    )
    assert all(
        hasattr(entity, "id") and entity.id == entity_id
        for entity_id, entity in state.entities.items()
    ), "spawned entities must be real EntityState objects keyed by their own id"


def test_build_initial_state_survivor_branch_also_carries_compiled_regions_and_places():
    """Episode N>0 (survivor reconstruction) must get compiled regions/places too."""
    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    orch.state.persistent_entities[42] = EntityCarryForward(
        entity_id=42, level=4, xp=900, equipment={}, reputation=0.8, alive=True
    )

    state = orch._build_initial_state(11, _real_episode_spec())

    assert state.regions, (
        "the survivor-reconstruction branch must receive real compiled regions, not "
        "just the episode-0 branch"
    )
    assert isinstance(state.places, dict)
    assert 42 in state.entities, "carried survivor must still be reconstructed"
    assert state.entities[42].identity.evolution_level == 4, (
        "carry-forward reconstruction must be unaffected by the region/place change"
    )
    assert state.seed == 11


def test_town_resolution_no_longer_early_exits_once_campaign_regions_are_populated():
    """Deliberate verification of the ticket's own second Scope bullet.

    TownResolutionSystem.resolve() early-exits when both town_tiles and regions are
    empty (`src/engine/town_resolution.py`). That early exit is exactly what made
    regional tax/suppression logic silently inert for every Campaign-mode episode.
    This asserts the real state produced by _build_initial_state() no longer trips
    it, and that running the now-live path is non-crashing and update-shaped.
    """
    from src.core.updates import StateUpdate
    from src.engine.town_resolution import TownResolutionSystem

    orch = CampaignOrchestrator(_make_manifest(n_episodes=1))
    state = orch._build_initial_state(3, _real_episode_spec())

    assert len(state.regions) > 0, "precondition: regions are now populated"

    update = StateUpdate()
    result = TownResolutionSystem.resolve(state, update)

    # The early-exit path returns the *identical* update object; the live path
    # builds a new one. Identity (not equality) is what distinguishes them.
    assert result is not update, (
        "with regions populated, resolve() must run its real regional logic instead "
        "of hitting the `not has_town and not has_regions` early-exit"
    )


# ---------------------------------------------------------------------------
# TCK-20260909-CAMPAIGN-INFORMATION-SOURCE-PROFILES-NOT-THREADED
# ---------------------------------------------------------------------------

def test_build_initial_state_episode_zero_carries_information_source_profiles():
    """Real regression for the confirmed gap: information_source_profiles was computed by
    WorldCompiler.compile() but never threaded into either _build_initial_state() branch,
    so it stayed permanently empty for every Campaign-mode episode regardless of what the
    world composition declared. frontier_living_world genuinely declares one
    (town_notice_board) -- use it explicitly rather than the tiny unit_faction_tension
    world, which declares none."""
    orch = CampaignOrchestrator(_make_manifest(n_episodes=1))

    state = orch._build_initial_state(7, _real_episode_spec(world_id="frontier_living_world"))

    assert state.information_source_profiles, (
        "episode 0 must receive the real compiled information_source_profiles -- an empty "
        "list is the exact pre-fix gap this ticket exists to close"
    )
    source_ids = {p.source_id for p in state.information_source_profiles}
    assert "town_notice_board" in source_ids, (
        f"expected frontier_living_world's own declared source, got {source_ids}"
    )


def test_build_initial_state_survivor_branch_also_carries_information_source_profiles():
    """The survivor-reconstruction branch must get the same fix as episode 0."""
    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    orch.state.persistent_entities[42] = EntityCarryForward(
        entity_id=42, level=4, xp=900, equipment={}, reputation=0.8, alive=True
    )

    state = orch._build_initial_state(11, _real_episode_spec(world_id="frontier_living_world"))

    assert state.information_source_profiles, (
        "the survivor-reconstruction branch must also receive real compiled "
        "information_source_profiles, not just the episode-0 branch"
    )


def test_build_initial_state_does_not_thread_pending_information_responses_yet():
    """Deliberate negative assertion, not an oversight: pending_information_responses is
    NOT threaded (TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH --
    doing so naively would resolve target_population_id against a completely different,
    unused entity-numbering scheme and silently misdeliver seeded facts to the wrong
    entity). frontier_living_world genuinely declares a non-empty
    pending_information_responses too, so this asserts the field is still empty on the
    real returned state despite real source content existing -- the correct, deliberate
    behavior until the follow-up ticket lands a real fix."""
    orch = CampaignOrchestrator(_make_manifest(n_episodes=1))

    state = orch._build_initial_state(7, _real_episode_spec(world_id="frontier_living_world"))

    assert state.pending_information_responses == [], (
        "pending_information_responses must stay empty until "
        "TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH lands a real "
        "actor-id resolution fix -- threading it naively would misdeliver to the wrong entity"
    )


def test_threaded_information_source_profiles_are_actually_consumable_by_the_real_router():
    """AC3: 'information_belief phase confirmed to actually consume the now-populated data
    ... not just that the field is non-empty on the constructed state.'

    A full real-episode run doesn't reliably exercise this: InformationBeliefPhase.apply()'s
    routing branch only fires for an actor with an unresolved self_model.knowledge.unknowns
    entry, a separate strategic-cognition precondition unrelated to this ticket's own fix
    (confirmed empirically: a real 70-tick frontier_living_world episode with the fix applied
    produced zero routed/assimilated entity properties, because no actor happened to have an
    unknown to route in that window -- not because the data path is broken). So this proves
    the real consumer function (InformationQueryRouter.route(), the same one
    InformationBeliefPhase.apply() calls) genuinely returns a candidate from the threaded
    data, isolating "is the data live and consumable" from "did an actor's independent
    strategic state happen to trigger consumption within N ticks" -- the latter is out of
    this ticket's own scope.
    """
    from src.domains.information.router import InformationQueryRouter
    from src.domains.information.schema import InformationQuery

    orch = CampaignOrchestrator(_make_manifest(n_episodes=1))
    state = orch._build_initial_state(7, _real_episode_spec(world_id="frontier_living_world"))
    assert state.information_source_profiles, "precondition: the fix threaded real profiles"

    actor = next(iter(state.entities.values()))
    query = InformationQuery(subject="ore_deposits", kind="material_source")

    candidates = InformationQueryRouter.route(actor, query, state, state.information_source_profiles)

    assert candidates, (
        "the real router must find a candidate from the now-threaded "
        "information_source_profiles -- town_notice_board declares common_resource_sources, "
        "which matches a material_source query"
    )
    assert any(c.source_id == "town_notice_board" for c in candidates)
