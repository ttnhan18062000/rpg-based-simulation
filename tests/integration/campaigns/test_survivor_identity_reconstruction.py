"""
Real-pipeline acceptance evidence for TCK-20260911-CAMPAIGN-SURVIVOR-IDENTITY-NOT-RESTORED-ON-
RECONSTRUCTION.

Before this ticket, `CampaignOrchestrator._build_initial_state()`'s survivor-reconstruction branch
never restored `kind`, `identity.role`, `.faction`, `.properties`, `.traits`, or `.personality` --
every reconstructed survivor came back with `EntityState`'s own bare defaults for all six
(`kind="entity"`, `role=0`=HERO, `faction=0`, empty `properties`/`traits`, all-zero personality),
regardless of what they actually were when spawned.

This module exercises the real production pipeline end to end: a real episode 0 spawn (real
archetypes via `WorldEntitySpawner`/`ArchetypeEntityFactory`), a real `run_episode()` completion,
real extraction (`_extract_entity_carry_forwards()`), and real reconstruction
(`_build_initial_state()`'s survivor branch) into episode 1 -- not a mocked field-by-field
comparison. `test_survivor_reconstruction_position.py`, alongside this file, covers the sibling
position fix and does not assert full episode completion; this module picks that acceptance bar up.
"""
import pytest

from src.content_semantics.faction import get_faction_id_str
from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
from src.observability.hard_law_monitor import HardLawMonitor
from src.scenarios.schema import SimulationScenarioDefinition


def _three_episode_manifest(tick_limit: int = 150) -> CampaignManifest:
    return CampaignManifest(
        id="test_survivor_identity_three_episode",
        episodes=[
            SimulationScenarioDefinition(
                id=f"test_survivor_identity_ep{i}",
                world_composition="frontier_living_world",
                perspective="hero_guild_perspective",
                victory_conditions=[{"kind": "tick_limit", "value": tick_limit}],
            )
            for i in range(3)
        ],
        base_seed=42,
    )


@pytest.mark.slow
@pytest.mark.resource_budget_large  # 3 real episodes x 150 ticks each exceeds the 60s default
def test_reconstructed_survivors_are_identity_equivalent_to_the_real_extracted_snapshot():
    """The governing invariant this ticket states directly: a reconstructed survivor's identity
    must match what was really extracted from their own completed episode, not defaults. Real
    end-to-end pipeline (spawn -> run -> extract -> reconstruct), not a mocked comparison."""
    manifest = _three_episode_manifest()
    orch = CampaignOrchestrator(manifest)

    summary0 = orch.run_episode()
    assert summary0.completed_tick > 0

    # orch.state.persistent_entities is the real extraction result from episode 0's real,
    # completed final state -- the ground truth this ticket's fix must faithfully restore.
    alive_snapshot = {
        eid: cf for eid, cf in orch.state.persistent_entities.items() if cf.alive
    }
    assert alive_snapshot, "episode 0 produced no survivors -- this test's own premise is vacuous"
    assert any(cf.kind != "" for cf in alive_snapshot.values()), (
        "every survivor's extracted kind is empty -- extraction itself isn't capturing real "
        "archetype data, which would make this comparison meaningless"
    )

    spec1 = orch._manifest.episodes[1]
    seed1 = orch._manifest.base_seed + 1
    initial_state_1 = orch._build_initial_state(seed1, spec1)

    checked = 0
    for eid, cf in alive_snapshot.items():
        assert eid in initial_state_1.entities, (
            f"survivor {eid} was alive in the extracted snapshot but missing from episode 1's "
            f"reconstructed entities"
        )
        reconstructed = initial_state_1.entities[eid]
        assert reconstructed.kind == cf.kind, (
            f"entity {eid}: kind mismatch, reconstructed={reconstructed.kind!r} "
            f"extracted={cf.kind!r}"
        )
        assert reconstructed.identity.role == cf.role, f"entity {eid}: role mismatch"
        assert reconstructed.identity.faction == cf.faction, f"entity {eid}: faction mismatch"
        assert reconstructed.identity.properties == cf.properties, (
            f"entity {eid}: properties mismatch"
        )
        assert set(reconstructed.identity.traits) == set(cf.traits), (
            f"entity {eid}: traits mismatch"
        )
        reconstructed_personality = {
            "greed": reconstructed.identity.personality.greed,
            "bravery": reconstructed.identity.personality.bravery,
            "sociability": reconstructed.identity.personality.sociability,
            "industry": reconstructed.identity.personality.industry,
        }
        assert reconstructed_personality == cf.personality, f"entity {eid}: personality mismatch"

        # The confirmed downstream consumer this ticket's own audit found: get_faction_id_str()
        # must resolve to the survivor's real faction, not a uniform default.
        assert get_faction_id_str(reconstructed) == get_faction_id_str_from_carry_forward(cf), (
            f"entity {eid}: get_faction_id_str() diverges between the extracted snapshot and the "
            f"reconstructed entity"
        )
        checked += 1

    assert checked == len(alive_snapshot)


def get_faction_id_str_from_carry_forward(cf) -> str:
    """Mirrors get_faction_id_str()'s own resolution order (properties["faction_id"] first,
    falling back to the bare faction int) against an EntityCarryForward snapshot directly, so the
    test above can compare against ground truth without needing a live EntityState."""
    faction_id = cf.properties.get("faction_id")
    if faction_id:
        return faction_id
    from src.core.enums import Faction
    try:
        return Faction(cf.faction).name.lower()
    except (ValueError, TypeError):
        return str(cf.faction)


@pytest.mark.slow
@pytest.mark.resource_budget_large  # 3 real episodes x 150 ticks each exceeds the 60s default
def test_real_three_episode_campaign_completion_after_identity_fix():
    """The acceptance bar transferred from TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-
    COLLISION: does a real 3-episode campaign_life_arc-shaped run complete all three episodes now
    that identity is also restored? Records whichever of the three predicted outcomes (completes /
    still stalls / stall changes shape) actually occurs -- not assumed in advance."""
    tick_limit = 150
    manifest = _three_episode_manifest(tick_limit=tick_limit)
    orch = CampaignOrchestrator(manifest)

    summary0 = orch.run_episode()
    assert summary0.completed_tick >= tick_limit - 15

    spec1 = orch._manifest.episodes[1]
    seed1 = orch._manifest.base_seed + 1
    initial_state_1 = orch._build_initial_state(seed1, spec1)
    violations1 = HardLawMonitor.check_initial_placement(initial_state_1)
    assert not [v for v in violations1 if v.law_id == "LAW-SPAWN-OCCUPANCY"]

    summary1 = orch.run_episode()
    assert summary1.completed_tick >= tick_limit - 15, (
        f"episode 1 completed at tick {summary1.completed_tick} (limit {tick_limit})"
    )

    spec2 = orch._manifest.episodes[2]
    seed2 = orch._manifest.base_seed + 2
    initial_state_2 = orch._build_initial_state(seed2, spec2)
    violations2 = HardLawMonitor.check_initial_placement(initial_state_2)
    assert not [v for v in violations2 if v.law_id == "LAW-SPAWN-OCCUPANCY"]

    summary2 = orch.run_episode()

    # Real, unhedged evidence, not an assumed outcome: report exactly what happened.
    print(
        f"\n[identity-fix acceptance] episode 2 completed_tick={summary2.completed_tick} "
        f"(limit={tick_limit}, prior known stall=52)"
    )
    assert summary2.completed_tick >= tick_limit - 15, (
        f"episode 2 completed at tick {summary2.completed_tick} (limit {tick_limit}), prior "
        f"known stall was tick 52 -- if this is still ~52, the identity fix did NOT resolve the "
        f"stall (a third layer exists, per this ticket's own Scope); if it's a different tick, "
        f"the stall's shape changed, which is the most informative outcome and should be chased "
        f"rather than this assertion silently loosened to pass"
    )
