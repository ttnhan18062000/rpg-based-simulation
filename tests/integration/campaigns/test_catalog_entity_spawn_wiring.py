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
import ast
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pytest

from src.core.governance import RuntimeMode
from src.domains.campaigns.orchestrator import CampaignManifest, CampaignOrchestrator
from src.engine.domain.action_router import ActionRouter
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.engine.pipeline_phases.actions import ActionRoutingPhase
from src.engine.scenario_runtime import ScenarioRuntimeService
from src.engine.tactical import TacticalDecisionSystem
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
    """Real per-entity spawn positions (TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION,
    which replaced the interim CampaignOrchestrator._scatter_catalog_entities() grid-scatter
    workaround this test used to describe) must leave every entity on a distinct tile --
    co-location is what trips LAW-OCCUPANCY-COLLISION below."""
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


# ---------------------------------------------------------------------------------------------------------------------
# The campaign episode's event-stream plausibility, as three tests over ONE episode run
# (TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS).
#
# The episode runs under a governor pinned to NORMAL, so the assertions do not depend on host speed or on the
# worker-utilization coupling (#175) that once forced this workers-disabled kernel into DEGRADED mode.
# Thresholds are the original ones: InvariantViolation == 0, cooperation share < 0.5, >= 3 deliberate attacks.
# ---------------------------------------------------------------------------------------------------------------------

_EPISODE_TICKS = 70
_CAMPAIGN_TICKET = "TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS"
_SHARE_TICKET = "TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR"
_OFFENSIVE_ACTIONS = ("ATTACK", "AOE_ATTACK", "SKILL")
# Copied from TacticalDecisionSystem.evaluate_entity_intent's neighbour scan (tactical.py); pinned by test_perception_scan_constants_match_tactical.
_PERCEPTION_RADIUS = 10.0
_MAX_SALIENT_TARGETS = 5


class _PinnedNormalGovernor(ResourceGovernor):
    """Pins NORMAL: the test asserts event-stream plausibility, which must not depend on host speed or the #175 coupling."""

    def _get_indicated_mode(self, profile, signals):
        return RuntimeMode.NORMAL

    def force_mode(self, mode, status, current_tick):
        return None  # the mid-tick wall-clock throttle must not flip the mode either


@dataclass
class _Counts:
    """What the instrumentation saw. ``attempts`` is the PRIMARY measure of deliberate attacks."""

    ticks: int = 0
    route_calls: int = 0
    decisions: int = 0
    decisions_with_hostile_perceived: int = 0
    attempts: int = 0  # decisions that set an ENTITY_ACT of ATTACK / AOE_ATTACK / SKILL: the origin of every attempt
    dispatches: int = 0  # DIAGNOSTIC only, never added to attempts: router dispatches of those kinds (decision -> task -> dispatch)
    dispatches_all_kinds: int = 0


def _hostiles_perceived(state, entity, neighbors):
    """How many neighbours ``entity`` would perceive as hostile, by the public perception API.

    Mirrors the scan inside TacticalDecisionSystem.evaluate_entity_intent (same neighbour set, perception gate and faction
    check) from public calls only, with no frame inspection. If the decision's scan changes, the positive control and the
    comparison recorded in the ticket are what notice."""
    from src.content_semantics.faction import get_faction_id_str, get_faction_semantics_service, get_species_id_str
    from src.content_semantics.relation import RelationContext
    from src.engine.behavior_consumers import get_entity_signals, get_perception_gate
    from src.engine.cognition import SensoryFilter
    from src.engine.domain_logic import SimulationDomainLogic
    from src.engine.legality import LegalityServiceV2
    from src.entities.identity_resolver import EntityIdentityResolver, IdentityResolutionError

    if neighbors is None:
        neighbors = SensoryFilter.filter_saliency(
            entity, SimulationDomainLogic.get_neighbor_view(state, entity, radius=_PERCEPTION_RADIUS), max_targets=_MAX_SALIENT_TARGETS
        )
    resolver, gate, semantics = EntityIdentityResolver(), get_perception_gate(), get_faction_semantics_service()
    try:
        src_faction = resolver.resolve(entity).faction_id
    except IdentityResolutionError:
        src_faction = get_faction_id_str(entity)
    found = 0
    for n in neighbors:
        if not n.combat.alive:
            continue
        dist = LegalityServiceV2.get_manhattan_dist(entity.navigation.position, n.navigation.position)
        if not gate.can_perceive(entity, get_entity_signals(n), {"distance": float(dist)}).perceived:
            continue
        try:
            tgt_faction = resolver.resolve(n).faction_id
        except IdentityResolutionError:
            tgt_faction = get_faction_id_str(n)
        context = RelationContext(
            distance=float(dist),
            combat_engaged=(entity.task.payload.get("target_id") == n.id or n.task.payload.get("target_id") == entity.id),
            source_species=get_species_id_str(entity),
            target_species=get_species_id_str(n),
        )
        if semantics.is_hostile_compat(src_faction, tgt_faction, context):
            found += 1
    return found


def _instrument(mp, counts):
    """Count, on the public entry points the episode uses (all restored when ``mp`` exits).

    Counts dispatch ATTEMPTS, including ones the router answers with the typed posture-withheld failure, because the defect
    under study is "never attempted". SKILL counts as offensive by origin: tactical.py has exactly one SKILL writer, in its
    combat branch with a hostile target (guarded by test_tactical_has_exactly_one_skill_writer)."""
    original_decision = TacticalDecisionSystem.evaluate_entity_intent
    original_route = ActionRoutingPhase.route
    original_execute = ActionRouter.execute_action
    original_tick = Kernel.tick_once

    def decision(state, entity, neighbors=None, region_trauma=None):
        counts.decisions += 1
        if _hostiles_perceived(state, entity, neighbors):
            counts.decisions_with_hostile_perceived += 1
        result = original_decision(state, entity, neighbors, region_trauma)
        task = getattr(result, "task", None)
        if task is not None and task.work_kind_set == "ENTITY_ACT" and (task.payload_set or {}).get("action") in _OFFENSIVE_ACTIONS:
            counts.attempts += 1
        return result

    def route(state, update):
        counts.route_calls += 1
        return original_route(state, update)

    def execute(entity, payload=None, *args, **kwargs):
        counts.dispatches_all_kinds += 1
        if (payload or {}).get("action") in _OFFENSIVE_ACTIONS:
            counts.dispatches += 1
        return original_execute(entity, payload, *args, **kwargs)

    def tick_once(self, *args, **kwargs):
        counts.ticks += 1
        return original_tick(self, *args, **kwargs)

    mp.setattr(TacticalDecisionSystem, "evaluate_entity_intent", staticmethod(decision))
    mp.setattr(ActionRoutingPhase, "route", staticmethod(route))
    mp.setattr(ActionRouter, "execute_action", staticmethod(execute))
    mp.setattr(Kernel, "tick_once", tick_once)


_EPISODE_SEEDS = (42, 1337)


def _run_episode(seed):
    """Run one pinned-NORMAL campaign episode and return (event_types, counts).

    Preconditions fail hard here, so a dependent strict xfail can never outlive the contact it needs: the episode ran its
    ticks, the router phase was reached every tick, tactical decisions were made, and at least one decision perceived a
    hostile. (Router dispatches are 0 for every kind in this episode, so a dispatch count cannot be the denominator.)"""
    recorder = _CollectingRecorder()
    counts = _Counts()
    with pytest.MonkeyPatch.context() as mp:
        _instrument(mp, counts)
        orch = CampaignOrchestrator(_campaign_life_arc_shaped_manifest(tick_limit=_EPISODE_TICKS))
        spec = orch._manifest.episodes[0]
        svc = ScenarioRuntimeService(
            spec, initial_state=orch._build_initial_state(seed, spec), scenario_event_recorder=None,
            governor=_PinnedNormalGovernor(),
        )
        svc._kernel = svc._build_kernel()
        svc._kernel._event_listeners = [lambda events: recorder.events.extend(events)]
        svc.start(tick_limit=_EPISODE_TICKS)
        svc.abort()
    event_types = Counter(e.event_type for e in recorder.events)
    assert counts.ticks == _EPISODE_TICKS, f"seed {seed}: the episode ran {counts.ticks} ticks, expected {_EPISODE_TICKS}"
    assert counts.route_calls == counts.ticks, (
        f"seed {seed}: the router phase ran {counts.route_calls} times in {counts.ticks} ticks: this episode no longer "
        f"reaches it, so an attempt count would be structurally 0"
    )
    assert counts.decisions > 0, f"seed {seed}: no tactical decision was made: attempts cannot be measured"
    assert counts.decisions_with_hostile_perceived > 0, (
        f"seed {seed}: no decision perceived a hostile in {counts.decisions} decisions: this episode offers no contact, so "
        f"the deliberate-attack check cannot say anything here (see {_CAMPAIGN_TICKET}: choose a seed or scenario with "
        f"measured contact)"
    )
    return event_types, counts


@pytest.fixture(scope="module")
def episodes_by_seed():
    """Run the pinned campaign episode ONCE per seed in `_EPISODE_SEEDS` and share the streams between the tests."""
    return {seed: _run_episode(seed) for seed in _EPISODE_SEEDS}


@pytest.fixture(scope="module")
def episode(episodes_by_seed):
    """Seed 42's event stream and counts: the episode the hard-law and deliberate-attack tests read."""
    return episodes_by_seed[_EPISODE_SEEDS[0]]


@pytest.mark.slow
def test_real_campaign_episode_has_no_hard_law_violation(episode):
    """Real, committed entities must not trip a sustained hard-law violation (LAW-OCCUPANCY-COLLISION and the rest):
    a non-zero count means the scatter workaround regressed or entities are co-located again."""
    event_types, _ = episode
    assert event_types.get("InvariantViolation", 0) == 0


@pytest.mark.slow
def test_real_campaign_episode_event_mix_is_not_dominated_by_cooperation(episodes_by_seed):
    """A real, spread-out episode should not be dominated by cooperation_event (co-located entities inflate it to ~79%).

    Pooled across the seeds in `_EPISODE_SEEDS` (cooperation events over all events), not per seed: the claim is about the
    scenario, and seed 42 alone sat at 0.4962 under AGENCY-07 (decision 21), a 0.0038 margin too thin to assert (see
    `TCK-20261006-CAMPAIGN-EPISODE-COOPERATION-SHARE-ABOVE-HALF-UNDER-A-PINNED-NORMAL-GOVERNOR`). The per-seed shares are in the message so a seed drifting toward 0.5 shows before the pooled value
    crosses it."""
    shares = {}
    pooled_cooperation = pooled_total = 0
    for seed, (event_types, _) in episodes_by_seed.items():
        total = sum(event_types.values())
        cooperation = event_types.get("cooperation_event", 0)
        shares[seed] = f"{cooperation / max(1, total):.4f} ({cooperation} of {total})"
        pooled_cooperation += cooperation
        pooled_total += total
    pooled = pooled_cooperation / max(1, pooled_total)
    assert pooled < 0.5, f"pooled cooperation_event share is {pooled:.4f} ({pooled_cooperation} of {pooled_total}); per seed: {shares}"


@pytest.mark.slow
@pytest.mark.xfail(
    strict=True,
    reason=f"{_CAMPAIGN_TICKET}: as measured on 0c89bd390 (seed 42, 70 ticks): 0 deliberate attacks among 250 decisions; "
           f"11 perceived a hostile (10 of 11 SAFETY_PRESSURE_RETREAT at full HP, 1 pursued), none in reach. Not the "
           f"attack fix's acceptance signal: an XPASS is a bonus",
)
def test_real_campaign_episode_makes_deliberate_attacks(episode):
    """>= 3 deliberate attacks attempted (decisions that set an offensive ENTITY_ACT), not combat_initiated: the latter was
    only ever met by incidental opportunity attacks drawn while fleeing."""
    _, counts = episode
    assert counts.attempts >= 3, (
        f"{counts.attempts} deliberate attacks among {counts.decisions} decisions; {counts.decisions_with_hostile_perceived} "
        f"perceived a hostile; {counts.route_calls} router-phase calls over {counts.ticks} ticks; router dispatches of "
        f"offensive kinds (diagnostic, not added): {counts.dispatches} of {counts.dispatches_all_kinds}"
    )


# ---------------------------------------------------------------------------------------------------------------------
# Positive controls for the instrument: a zero is only evidence if the same counters read >= 1 when the event happens.
# ---------------------------------------------------------------------------------------------------------------------


def _two_entities(attacker_hp=100):
    """A hero next to a monster, for the instrument controls (real engine objects, no episode)."""
    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole, Faction
    from src.core.state import AuthoritativeState

    def make(eid, pos, role, faction, hp):
        return (
            V2EntityBuilder(eid).kind("hero" if role == EntityRole.HERO else "monster").location(*pos)
            .identity(role=role, faction=faction)
            .combat(hp=hp, max_hp=100, attack_range=1, readiness=100.0, alive=True)
            .lifecycle(active=True).build()
        )

    hero = make(1, (10.0, 10.0), EntityRole.HERO, Faction.HERO_GUILD, attacker_hp)
    monster = make(2, (10.0, 11.0), EntityRole.MONSTER, Faction.MONSTER_HORDE, 100)
    state = AuthoritativeState(tick=5, seed=42, world_time=5, entities={1: hero, 2: monster})
    return state, hero, monster


def test_instrument_counts_a_router_attack_dispatch():
    state, hero, monster = _two_entities()
    counts = _Counts()
    with pytest.MonkeyPatch.context() as mp:
        _instrument(mp, counts)
        ActionRouter.execute_action(hero, {"action": "ATTACK", "target_id": monster.id}, 5, [(monster.id, monster)], state)
    assert counts.dispatches >= 1 and counts.dispatches_all_kinds >= 1


def test_instrument_counts_a_decision_that_attacks_and_a_perceived_hostile():
    state, hero, monster = _two_entities()
    counts = _Counts()
    with pytest.MonkeyPatch.context() as mp:
        _instrument(mp, counts)
        result = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
    assert counts.decisions == 1
    assert counts.decisions_with_hostile_perceived >= 1, "a hostile next to the entity must count as perceived"
    assert result.task is not None and (result.task.payload_set or {}).get("action") in _OFFENSIVE_ACTIONS, (
        "control scenario: a healthy hero beside a monster should decide to attack"
    )
    assert counts.attempts >= 1


def test_instrument_restores_the_entry_points_it_wrapped():
    before = (TacticalDecisionSystem.evaluate_entity_intent, ActionRoutingPhase.route, ActionRouter.execute_action, Kernel.tick_once)
    with pytest.MonkeyPatch.context() as mp:
        _instrument(mp, _Counts())
    after = (TacticalDecisionSystem.evaluate_entity_intent, ActionRoutingPhase.route, ActionRouter.execute_action, Kernel.tick_once)
    assert before == after


def test_tactical_has_exactly_one_skill_writer():
    """SKILL counts as an offensive attempt by origin; a second, non-offensive writer would inflate the count silently."""
    source = (Path(__file__).resolve().parents[3] / "src" / "engine" / "tactical.py").read_text()
    writers = [
        node for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Dict)
        and any(isinstance(k, ast.Constant) and k.value == "action" and isinstance(v, ast.Constant) and v.value == "SKILL"
                for k, v in zip(node.keys, node.values))
    ]
    assert len(writers) == 1, f"tactical.py writes a SKILL action in {len(writers)} places; review them for offensiveness"


def test_perception_scan_constants_match_tactical():
    """_hostiles_perceived copies the decision's neighbour radius and saliency cap; if tactical.py changes them, K would silently
    measure a different scan than the one the decision reads."""
    source = (Path(__file__).resolve().parents[3] / "src" / "engine" / "tactical.py").read_text()
    decision = next(
        n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef) and n.name == "evaluate_entity_intent"
    )
    found = {}
    for call in ast.walk(decision):
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr in ("get_neighbor_view", "filter_saliency"):
            for kw in call.keywords:
                if kw.arg in ("radius", "max_targets") and isinstance(kw.value, ast.Constant):
                    found[(call.func.attr, kw.arg)] = kw.value.value
    assert found == {
        ("get_neighbor_view", "radius"): _PERCEPTION_RADIUS,
        ("filter_saliency", "max_targets"): _MAX_SALIENT_TARGETS,
    }, f"tactical.py's neighbour scan changed: {found}"
