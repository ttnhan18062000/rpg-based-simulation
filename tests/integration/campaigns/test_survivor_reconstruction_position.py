"""
Real-pipeline acceptance evidence for TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-
COLLISION.

Before this ticket, `CampaignOrchestrator._build_initial_state()`'s survivor-reconstruction
branch (episode N>0) left every survivor at `NavigationComponent`'s own dataclass default,
`(0.0, 0.0)` -- identical for every survivor, tripping `LAW-SPAWN-OCCUPANCY`. This module exercises
the real fix through the real production entrypoint (`CampaignOrchestrator.run_episode()`, called
once per episode, matching how a real multi-episode campaign actually progresses), not a lower-
level unit call.

**Scope note, corrected 2026-09-11 after this exact real run surfaced a separate defect**: this
ticket's own confirmed claim is that survivors reconstruct at distinct, legal positions with zero
LAW-SPAWN-OCCUPANCY violations -- verified directly below for both episode 1 and episode 2. It does
NOT claim episode 2 (or any later episode) completes at full tick length -- that requires
`TCK-20260911-CAMPAIGN-SURVIVOR-KIND-FACTION-IDENTITY-CARRY-FORWARD-GAP`'s own fix first (survivor
`kind`/`identity.faction` are separately, confirmedly dropped by the same reconstruction branch;
episode 2 stalls at tick 52 for that reason, not a position collision -- confirmed here by the fact
that the occupancy checks below pass even though episode 2 still stalls). The full
campaign-completion acceptance bar is transferred to that ticket's own Acceptance Criteria, not
silently dropped -- see this module's assertions for exactly what stays proven here.
"""
import pytest

from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
from src.observability.hard_law_monitor import HardLawMonitor
from src.scenarios.schema import SimulationScenarioDefinition


def _three_episode_manifest(tick_limit: int = 150) -> CampaignManifest:
    return CampaignManifest(
        id="test_survivor_placement_three_episode",
        episodes=[
            SimulationScenarioDefinition(
                id=f"test_survivor_placement_ep{i}",
                world_composition="frontier_living_world",
                perspective="hero_guild_perspective",
                victory_conditions=[{"kind": "tick_limit", "value": tick_limit}],
            )
            for i in range(3)
        ],
        base_seed=42,
    )


def _assert_no_spawn_occupancy_violations(initial_state, episode_idx: int) -> None:
    assert initial_state.entities, (
        f"episode {episode_idx} reconstructed zero entities -- no survivors carried forward, "
        f"which would make this check vacuous"
    )
    tiles = [
        (int(e.navigation.position[0]), int(e.navigation.position[1]))
        for e in initial_state.entities.values()
    ]
    assert len(set(tiles)) == len(tiles), (
        f"episode {episode_idx}: {len(tiles) - len(set(tiles))} survivor(s) share a tile with "
        f"another -- the exact collision this ticket exists to fix"
    )
    violations = HardLawMonitor.check_initial_placement(initial_state)
    spawn_violations = [v for v in violations if v.law_id == "LAW-SPAWN-OCCUPANCY"]
    assert not spawn_violations, (
        f"episode {episode_idx}'s reconstructed initial state has "
        f"{len(spawn_violations)} LAW-SPAWN-OCCUPANCY violation(s): "
        f"{[v.message for v in spawn_violations[:5]]}"
    )


@pytest.mark.slow
@pytest.mark.resource_budget_large  # 3 real episodes x 150 ticks each exceeds the 60s default
def test_real_three_episode_campaign_survivors_reconstruct_at_distinct_legal_positions():
    """This ticket's own confirmed claim: real survivors reconstructed after episode 0 and after
    episode 1 land on distinct, legal tiles with zero LAW-SPAWN-OCCUPANCY violations. Does not
    assert full campaign completion -- see module docstring for why, and which ticket owns that."""
    tick_limit = 150
    manifest = _three_episode_manifest(tick_limit=tick_limit)
    orch = CampaignOrchestrator(manifest)

    # Episode 0: no survivor reconstruction, just the baseline. Confirmed elsewhere
    # (TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING's own tests) -- run it here only to
    # produce real survivors for episode 1's reconstruction.
    summary0 = orch.run_episode()
    assert summary0.completed_tick >= tick_limit - 15, (
        f"episode 0 completed at tick {summary0.completed_tick} (limit {tick_limit}) -- unexpected "
        f"early stop unrelated to this ticket's own scope"
    )

    # Episode 1: reconstructed from episode 0's survivors -- the first real exercise of this
    # ticket's own fix.
    spec1 = orch._manifest.episodes[1]
    seed1 = orch._manifest.base_seed + 1
    initial_state_1 = orch._build_initial_state(seed1, spec1)
    _assert_no_spawn_occupancy_violations(initial_state_1, episode_idx=1)

    summary1 = orch.run_episode()
    assert summary1.completed_tick >= tick_limit - 15, (
        f"episode 1 completed at tick {summary1.completed_tick} (limit {tick_limit}) -- expected "
        f"full completion; this ticket's own fix (position only) does not touch anything that "
        f"should cause an early stop here"
    )

    # Episode 2: reconstructed from episode 1's survivors -- the second real exercise, a smaller
    # cast (fewer survivors than episode 1). This ticket's own claim (occupancy-violation-free
    # reconstruction) is checked and must hold; full episode completion is NOT asserted here --
    # confirmed separately (see module docstring) to be blocked by a different, un-fixed defect.
    spec2 = orch._manifest.episodes[2]
    seed2 = orch._manifest.base_seed + 2
    initial_state_2 = orch._build_initial_state(seed2, spec2)
    _assert_no_spawn_occupancy_violations(initial_state_2, episode_idx=2)

    # Run episode 2 anyway (real production entrypoint) to confirm it doesn't crash or hang --
    # its own completed_tick is intentionally not asserted against tick_limit here.
    summary2 = orch.run_episode()
    assert summary2.completed_tick > 0, (
        "episode 2 produced no real ticks at all -- a materially different (and more severe) "
        "failure than the known, separately-tracked stall"
    )
