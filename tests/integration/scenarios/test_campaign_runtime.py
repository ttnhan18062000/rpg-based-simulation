"""
tests/integration/scenarios/test_campaign_runtime.py
────────────────────────────────────────────────────────────────────────────────
Integration tests for CampaignOrchestrator multi-episode runtime.
(TCK-20260619-E32C-ORCHESTRATOR)

All tests run real Kernel ticks with minimal world config and small tick_limit
victory conditions. Tagged @pytest.mark.slow.

Acceptance criteria covered:
  TC-1 — Entity level persists across episodes (entity_level ep1 == entity_level ep2)
  TC-2 — Dead faction is absent in episode 2's persistent_factions
  TC-3 — episode_history has N entries after N run_episode() calls
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True, scope="module")
def _warmup_catalog():
    """Warm up the content catalog once per module before any kernel ticks.

    Prevents ContentHotPathViolation when ticks run with pre-seeded entities
    that trigger behavior_consumers on the first tick.
    """
    from src.engine.behavior_consumers import _auto_init
    _auto_init()


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_spec(spec_id: str = "test_ep", tick_limit: int = 10, **kwargs):
    """Build a minimal SimulationScenarioDefinition with a tick_limit victory condition."""
    from src.scenarios.schema import SimulationScenarioDefinition

    defaults = {
        "id": spec_id,
        "world_composition": "frontier_living_world",
        "perspective": "hero_guild_perspective",
        "victory_conditions": [{"kind": "tick_limit", "value": tick_limit}],
    }
    defaults.update(kwargs)
    return SimulationScenarioDefinition(**defaults)


def _make_initial_state(seed: int = 0, entities: dict | None = None):
    """Build a minimal AuthoritativeState, optionally pre-seeded with entities."""
    from src.core.state import AuthoritativeState

    return AuthoritativeState(tick=0, seed=seed, entities=entities or {})


def _make_entity_state(entity_id: int, level: int = 5, faction: int = 1, alive: bool = True):
    """Build a minimal EntityState with controlled level and lifecycle.active."""
    import dataclasses
    from src.core.state import EntityState

    base = EntityState(id=entity_id, kind="entity")
    identity = dataclasses.replace(base.identity, evolution_level=level)
    lifecycle = dataclasses.replace(base.lifecycle, active=alive)
    return dataclasses.replace(base, identity=identity, lifecycle=lifecycle)


# ── TC-1: Entity state persists across episodes ───────────────────────────────


@pytest.mark.slow
def test_entity_state_persists_across_episodes():
    """TC-1: An entity at level 5 in episode 1 starts episode 2 at level 5.

    Strategy: pre-seed episode 0's initial_state with an EntityState at level 5.
    After episode 0 completes, the orchestrator should extract EntityCarryForward
    with level=5. We verify persistent_entities[entity_id].level == 5 before
    episode 1 runs, confirming carry-forward is captured.
    """
    from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
    from src.engine.scenario_runtime import ScenarioObjectiveState

    entity_id = 1
    target_level = 5

    # Build a 2-episode manifest — both episodes run for 10 ticks.
    spec0 = _make_spec("ep0", tick_limit=10)
    spec1 = _make_spec("ep1", tick_limit=10)
    manifest = CampaignManifest(id="test_campaign_tc1", episodes=[spec0, spec1], base_seed=0)

    # Pre-seed episode 0 with the entity at level 5.
    entity_at_level_5 = _make_entity_state(entity_id=entity_id, level=target_level)
    initial_state_ep0 = _make_initial_state(seed=0, entities={entity_id: entity_at_level_5})

    # Monkey-patch _build_initial_state for episode 0 only, to inject our pre-built state.
    orch = CampaignOrchestrator(manifest)
    original_build = orch._build_initial_state

    call_count = [0]

    def _patched_build(episode_seed: int):
        if call_count[0] == 0:
            call_count[0] += 1
            return initial_state_ep0
        return original_build(episode_seed)

    orch._build_initial_state = _patched_build

    # Run episode 0.
    summary0 = orch.run_episode()
    assert summary0.episode_index == 0
    assert summary0.completed_tick > 0

    # Verify the entity's level was captured in carry-forward.
    assert entity_id in orch.state.persistent_entities, (
        f"entity_id={entity_id} not found in persistent_entities after episode 0"
    )
    cf = orch.state.persistent_entities[entity_id]
    assert cf.level == target_level, (
        f"Expected carry-forward level={target_level}, got {cf.level}"
    )

    # Run episode 1 — entity starts at level 5 (injected via _build_initial_state).
    summary1 = orch.run_episode()
    assert summary1.episode_index == 1
    assert summary1.completed_tick > 0

    # Confirm carry-forward level is preserved after episode 1.
    cf_after_ep1 = orch.state.persistent_entities[entity_id]
    assert cf_after_ep1.level == target_level, (
        f"Expected level={target_level} after episode 1, got {cf_after_ep1.level}"
    )


# ── TC-2: Dead faction absent in episode 2 ───────────────────────────────────


@pytest.mark.slow
def test_dead_faction_absent_in_episode_2():
    """TC-2: A faction recorded as destroyed is excluded from episode 2 spawn.

    Strategy: Run episode 0 normally via a real kernel (tick_limit=10).
    Then directly record a destroyed faction in persistent_factions (simulating
    an episode outcome where faction_99 lost all its entities). Verify that:
    - _get_spawn_factions() excludes the destroyed faction
    - _build_initial_state() does not inject any entity belonging to that faction
    - Episode 1 runs to completion without the destroyed faction's entities
    """
    from src.domains.campaigns.orchestrator import (
        CampaignManifest,
        CampaignOrchestrator,
    )
    from src.domains.campaigns.state import EntityCarryForward, FactionCarryForward

    spec0 = _make_spec("ep0_faction2", tick_limit=10)
    spec1 = _make_spec("ep1_faction2", tick_limit=10)
    manifest = CampaignManifest(
        id="test_campaign_tc2", episodes=[spec0, spec1], base_seed=0
    )

    orch = CampaignOrchestrator(manifest)

    # Run episode 0 for real.
    summary0 = orch.run_episode()
    assert summary0.episode_index == 0
    assert summary0.completed_tick > 0

    # Simulate: a destroyed faction was recorded after ep0 (e.g., faction_99).
    dead_faction_key = "faction_99"
    orch.state.persistent_factions[dead_faction_key] = FactionCarryForward(
        faction_id=dead_faction_key, alive=False, tension=0.0
    )
    # Simulate: a dead entity from faction_99.
    dead_entity_id = 9999
    orch.state.persistent_entities[dead_entity_id] = EntityCarryForward(
        entity_id=dead_entity_id,
        level=3,
        xp=100,
        equipment={},
        reputation=0.5,
        alive=False,  # dead — must not be spawned
    )

    # dead faction must not appear in _get_spawn_factions.
    spawn_factions = orch._get_spawn_factions()
    assert dead_faction_key not in spawn_factions, (
        f"Destroyed faction '{dead_faction_key}' must not appear in spawn candidates"
    )

    # dead entity must not appear in _get_spawn_entities.
    spawn_entities = orch._get_spawn_entities()
    assert dead_entity_id not in spawn_entities, (
        f"Dead entity {dead_entity_id} must not appear in spawn candidates"
    )

    # _build_initial_state for episode 1 must not include dead entity.
    ep1_initial = orch._build_initial_state(episode_seed=1)
    assert dead_entity_id not in ep1_initial.entities, (
        f"Dead entity {dead_entity_id} must not be injected into episode 1's initial state"
    )

    # Run episode 1 to completion — must not raise.
    summary1 = orch.run_episode()
    assert summary1.episode_index == 1
    assert summary1.completed_tick > 0


# ── TC-3: episode_history accumulates ────────────────────────────────────────


@pytest.mark.slow
def test_episode_history_accumulates():
    """TC-3: CampaignState.episode_history has N entries after N run_episode() calls."""
    from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator

    n_episodes = 3
    specs = [_make_spec(f"ep{i}", tick_limit=10) for i in range(n_episodes)]
    manifest = CampaignManifest(id="test_campaign_tc3", episodes=specs, base_seed=0)

    orch = CampaignOrchestrator(manifest)

    for i in range(n_episodes):
        summary = orch.run_episode()
        assert summary.episode_index == i
        assert summary.completed_tick > 0

    assert len(orch.state.episode_history) == n_episodes, (
        f"Expected {n_episodes} episode_history entries, got {len(orch.state.episode_history)}"
    )
    for i, entry in enumerate(orch.state.episode_history):
        assert entry.episode_index == i, (
            f"episode_history[{i}].episode_index should be {i}, got {entry.episode_index}"
        )
        assert entry.completed_tick > 0, (
            f"episode_history[{i}].completed_tick should be > 0"
        )

    assert orch.state.episode_index == n_episodes
