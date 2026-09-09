"""
Real-pipeline evidence for TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING.

Before this ticket, `CampaignOrchestrator._build_initial_state()`'s "no alive carry-forwards"
branch (episode 0, or any episode after a full-party wipe) never spawned any entities at all --
`campaign_life_arc` (and any Campaign-mode profile shaped like it) ran with zero entities for its
entire episode (TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION's own root-cause finding).
This module exercises the real fix through the real production entrypoint
(`CampaignOrchestrator.run_episode()`), not a lower-level unit call, and checks the two real risks
peer review specifically asked to be verified rather than assumed: entity co-location tripping the
engine's own `LAW-OCCUPANCY-COLLISION` hard law, and whether the resulting event stream looks like
a plausible simulation rather than a degenerate artifact.
"""
from collections import Counter

import pytest

from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
from src.scenarios.schema import SimulationScenarioDefinition


class _CollectingRecorder:
    """Duck-typed event_recorder: only needs .record(event), matching EventRecorder's own
    interface -- avoids the filesystem I/O of a real EventRecorder for this test."""

    def __init__(self):
        self.events = []

    def record(self, event):
        self.events.append(event)


def _campaign_life_arc_shaped_manifest(tick_limit: int = 70) -> CampaignManifest:
    return CampaignManifest(
        id="test_campaign_life_arc_shape",
        episodes=[
            SimulationScenarioDefinition(
                id="test_ep0",
                world_composition="frontier_living_world",
                perspective="hero_guild_perspective",
                victory_conditions=[{"kind": "tick_limit", "value": tick_limit}],
            )
        ],
        base_seed=42,
    )


@pytest.mark.slow
def test_episode_zero_spawns_real_entities_matching_the_world_composition():
    """The core fix: `_build_initial_state()`'s empty branch now spawns real entities, not {}."""
    orch = CampaignOrchestrator(_campaign_life_arc_shaped_manifest())
    spec = orch._manifest.episodes[0]

    state = orch._build_initial_state(42, spec)

    assert state.entities, "episode 0 must spawn real entities, not the pre-fix empty dict"
    kinds = {e.kind for e in state.entities.values()}
    # frontier_living_world's own module list (frontier_village_core, wolf_den_near_forest,
    # goblin_camp_conflict, old_mine_resource_loop, bandit_road_trade_pressure,
    # undead_battlefield, trading_company_hub) -- real content resolved, not a synthetic subset.
    assert "human" in kinds and "goblin" in kinds, (
        f"expected real archetype-resolved entities from the composition's modules, got {kinds}"
    )
    assert state.regions, "regions must still be populated alongside the new entities"


@pytest.mark.slow
def test_episode_zero_entities_are_scattered_not_co_located():
    """Interim workaround (CampaignOrchestrator._scatter_catalog_entities) must leave every
    entity on a distinct tile -- co-location is what trips LAW-OCCUPANCY-COLLISION below."""
    orch = CampaignOrchestrator(_campaign_life_arc_shaped_manifest())
    spec = orch._manifest.episodes[0]

    state = orch._build_initial_state(42, spec)

    tiles = {(int(e.navigation.position[0]), int(e.navigation.position[1])) for e in state.entities.values()}
    assert len(tiles) == len(state.entities), (
        "every spawned entity must land on a distinct tile -- a shared tile is exactly the "
        "LAW-OCCUPANCY-COLLISION-triggering co-location this scatter exists to prevent"
    )


@pytest.mark.slow
def test_real_campaign_episode_does_not_stall_early():
    """The real production entrypoint (CampaignOrchestrator.run_episode(), not a lower-level unit
    call) must not reproduce the pre-fix ~52-tick stall. Pre-fix: every campaign_life_arc-shaped
    episode stalled at ~tick 52 (STALL_THRESHOLD=50 consecutive zero-event ticks) because
    _build_initial_state() never spawned any entities. Real entities now generate real activity
    throughout, so the episode must run close to its configured length instead."""
    manifest = _campaign_life_arc_shaped_manifest(tick_limit=70)
    orch = CampaignOrchestrator(manifest)

    summary = orch.run_episode()

    assert summary.completed_tick >= 65, (
        f"episode completed at tick {summary.completed_tick}, expected close to the configured "
        f"70-tick limit -- an early stop this close to the old ~52-tick stall point would suggest "
        f"the fix regressed rather than a real, unrelated victory condition"
    )


@pytest.mark.slow
def test_real_campaign_episode_event_stream_is_plausible_not_degenerate():
    """Same real scenario shape and real Kernel ticks as run_episode() itself uses internally,
    but with a kernel._event_listeners hook attached so the full per-tick SimulationEvent stream
    can be inspected -- CampaignOrchestrator.run_episode()'s own `event_recorder` parameter only
    ever receives scenario-level bookkeeping events (scenario_objective_progressed/completed/
    stalled, emitted directly by ScenarioRuntimeService._evaluate_after_tick()), never the
    kernel-generated combat/cooperation/hard-law events this test needs to see -- confirmed by
    running this test against `event_recorder=` first and observing it collects only those 2
    scenario-level event types, zero of anything else, regardless of what the kernel itself does.

    Checks the two real risks peer review specifically asked to be verified rather than assumed:
    entity co-location tripping LAW-OCCUPANCY-COLLISION (a real, sustained ERROR-severity hard-law
    violation, confirmed via a real pre-scatter run: 41 occurrences over 70 ticks), and whether the
    event mix looks like a plausible simulation rather than a degenerate artifact (co-located
    entities inflated cooperation_event to 935/1190 == 79% of all activity with only 1 real combat
    exchange in the whole run, before the scatter fix)."""
    from src.engine.scenario_runtime import ScenarioRuntimeService

    recorder = _CollectingRecorder()
    manifest = _campaign_life_arc_shaped_manifest(tick_limit=70)
    orch = CampaignOrchestrator(manifest)
    spec = orch._manifest.episodes[0]
    initial_state = orch._build_initial_state(42, spec)

    svc = ScenarioRuntimeService(spec, initial_state=initial_state, event_recorder=None)
    svc._kernel = svc._build_kernel()
    svc._kernel._event_listeners = [lambda events: recorder.events.extend(events)]
    svc.start(tick_limit=70)
    svc.abort()

    event_types = Counter(e.event_type for e in recorder.events)

    assert event_types.get("InvariantViolation", 0) == 0, (
        "real, committed entities must not trip a sustained hard-law violation -- a non-zero "
        "count here means the scatter workaround regressed or entities are co-located again"
    )
    assert event_types.get("combat_initiated", 0) >= 3, (
        "expected multiple distinct combat engagements across a real, spread-out episode, not "
        "the single isolated fight the pre-scatter co-located run produced"
    )
    total_events = sum(event_types.values())
    cooperation_share = event_types.get("cooperation_event", 0) / max(1, total_events)
    assert cooperation_share < 0.5, (
        f"cooperation_event is {cooperation_share:.0%} of all activity -- co-located entities "
        f"inflate this to ~79%; a real, spread-out episode should not be dominated by it"
    )
