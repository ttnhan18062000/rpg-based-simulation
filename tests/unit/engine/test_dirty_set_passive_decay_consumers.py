"""
Real-pipeline evidence for TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION.

The published `dirty_set` (AuthoritativeApplyPipeline.refine()'s own return value, built by
DirtySetBuilder.mark_from_update() from update.entity_updates only) never reflects passive-decay
-only entity changes -- those are computed later, entirely inside ApplyPath.apply_generation() /
ApplyPlanBuilder.build_plan(), and never staged as an EntityUpdate. This module constructs the
exact real scenario the originating hotfix ticket cited (TCK-20260908-HOTFIX-INCREMENTAL-MIDRUN-
DEACTIVATE-RECOLOR-GAP): an entity already killed in real combat on a prior tick, whose only
remaining state change is driven entirely by the passive decay path, with zero explicit
EntityUpdate that tick -- and checks each of the two consumers the investigation ticket named.

Note on scope: a *live*, critically-wounded entity that then dies from passive decay was also
tried as a scenario and rejected -- src/ai/goals/scorers.py's own hp_ratio-based goal scoring
(COMBAT_RETREAT below hp_ratio 0.5, TOWN_RETURN as the default fallback above it) means
strategic_intelligence (must_run_every_tick=True) assigns some project to any live, cognitively
active entity essentially every tick regardless of HP, which marks it dirty via the
strategic/movement domain and masks the omission being investigated. That is itself a real,
evidenced boundary on how narrow the omission's practical blast radius is for live entities --
recorded in investigation.md, not chased further here (out of this ticket's own scope).
"""
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.core.builder import V2EntityBuilder
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath
from src.api.read_model_cache import ReadModelCache


def _build_already_combat_dead_entity():
    """An entity already killed in combat on a PRIOR tick (combat.alive=False, hp=0) but whose
    lifecycle.active cleanup hasn't happened yet -- "a dead entity stops acting, so its only
    remaining state changes come from this passive path" (the originating hotfix ticket's own
    framing). A dead entity draws no strategic-goal reaction (see module docstring). The
    biological branch of src/engine/apply.py's `_compute_entity_changes` is gated only on
    lifecycle.active (still True pre-tick here), not combat.alive -- so hunger/sleep_debt keep
    passively accruing even after death, purely from age-tick advancement, with no explicit
    EntityUpdate of any domain."""
    return (
        V2EntityBuilder(1)
        .kind("HERO")
        .location(0.0, 0.0)
        .biological(hunger=10.0, sleep_debt=10.0)
        .combat(hp=0, max_hp=100, alive=False)
        .lifecycle(active=True, age_ticks=10, max_age_ticks=100_000)
        .build()
    )


def _run_real_passive_decay_tick():
    """Real pipeline + real apply -- hunger passively accrues and lifecycle.active flips, with no
    EntityUpdate of any domain for this entity."""
    entity = _build_already_combat_dead_entity()
    prior_state = AuthoritativeState(tick=100, seed=42, entities={1: entity})
    empty_update = StateUpdate()

    refined = AuthoritativeApplyPipeline.refine(prior_state, empty_update)
    next_state = ApplyPath.apply_generation(prior_state, refined, next_tick=101, next_world_time=101)
    return prior_state, refined, next_state


def test_passive_decay_only_tick_produces_real_state_change_with_no_entity_update():
    """Sanity precondition: real, committed state changes (hunger accrues, lifecycle.active
    flips) with genuinely no EntityUpdate staged for this entity."""
    prior_state, refined, next_state = _run_real_passive_decay_tick()

    assert prior_state.entities[1].lifecycle.active is True
    assert next_state.entities[1].lifecycle.active is False
    assert next_state.entities[1].biological.hunger > prior_state.entities[1].biological.hunger

    assert 1 not in refined.entity_updates


def test_consumer_1_phase_shortcircuit_is_confirmed_benign_not_a_bug():
    """`near_death_hardening` and `evolution` (the only can_skip_when_no_dirty phases whose
    input_domains include lifecycle/biological, evaluated against a real, non-None dirty_set --
    see src/engine/pipeline.py's checkpoints at lines 374/389, both before their own run_phase()
    calls) are genuinely skipped on this tick. But both phases only ever iterate
    update.entity_updates (src/engine/pipeline_phases/hardening.py, src/engine/evolution.py) --
    the exact same source DirtySetBuilder.mark_from_update() reads to populate the dirty_set. A
    passive-decay-only entity is invisible to both at once, by the same structural cause -- so the
    skip drops zero real work, not just none observed in this one scenario."""
    prior_state, refined, next_state = _run_real_passive_decay_tick()

    assert refined.metric_counters.get("skip_near_death_hardening") == 1
    assert refined.metric_counters.get("skip_evolution") == 1

    assert refined.dirty_set is not None
    assert refined.dirty_set.combat_entities == set()
    assert refined.dirty_set.biological_entities == set()
    assert refined.dirty_set.lifecycle_entities == set()
    assert refined.dirty_set.attribute_entities == set()

    # The two phases' own trigger condition (membership in update.entity_updates) is already
    # false for entity 1 -- confirmed above -- so running them would have iterated an empty/
    # irrelevant dict for this entity regardless of the skip. Running them for real (bypassing
    # should_run_phase) proves it directly rather than by inference alone.
    from src.engine.pipeline_phases.hardening import NearDeathHardeningPhase
    from src.engine.evolution import EvolutionSystem

    forced_hardening = NearDeathHardeningPhase.apply(prior_state, refined)
    forced_evolution = EvolutionSystem.evaluate(prior_state, refined)
    assert forced_hardening.entity_updates == refined.entity_updates
    assert forced_evolution.entity_updates == refined.entity_updates


def test_consumer_2_read_model_cache_invalidates_passive_decay_only_change():
    """ReadModelCache (src/api/read_model_cache.py), wired live in
    V2EngineManager._update_latest_state() every tick and read by the real
    get_entity/get_entities_paged API endpoints, invalidates a cached entity DTO for IDs in
    dirty_set.all_dirty_entities (ReadModelInvalidationPolicy.get_dirty_entity_ids) UNION
    next_state._apply_time_dirty_set.all_dirty_entities -- the real, apply-time-computed DirtySet
    that ApplyPath.apply_generation() now always attaches to the state it returns
    (TCK-20260908-READMODEL-CACHE-PASSIVE-DECAY-STALENESS), independent of the published
    pre-apply dirty_set's own semantics (which apply_plan.py's own `invalidate_read_model` field
    was meant to drive but never did -- confirmed dead, grep for "invalidate_read_model" outside
    its own definition/assignment finds only a stale comment in
    src/domains/combat_engagement/phase.py).

    Real, committed state changed (hunger genuinely accrued) and the published pre-apply dirty_set
    for this tick is empty, but next_state's own _apply_time_dirty_set now carries entity 1 --
    apply_generation() marks any entity with a real component change, passive-decay-only included.
    The cache correctly drops the stale DTO."""
    prior_state, refined, next_state = _run_real_passive_decay_tick()
    entity_id = 1

    cache = ReadModelCache()
    cache.update(prior_state, dirty_set=None)
    stale_dto = cache.get_entity_dto(prior_state.entities[entity_id])
    assert stale_dto["biological"]["hunger"] == 10.0

    # The real published pre-apply dirty_set from this exact tick -- still empty, per the prior
    # test. The fix does not change this -- other consumers (phase gating, movement cache) still
    # see exactly what they saw before.
    assert refined.dirty_set.all_dirty_entities == set()

    # But next_state's own apply-time dirty set is real and non-empty for this entity.
    assert next_state._apply_time_dirty_set is not None
    assert entity_id in next_state._apply_time_dirty_set.all_dirty_entities

    cache.update(next_state, dirty_set=refined.dirty_set)

    served_dto = cache.get_entity_dto(next_state.entities[entity_id])

    # FIXED: the cache correctly invalidated and recomputed. Hunger genuinely accrued.
    assert served_dto is not stale_dto
    assert served_dto["biological"]["hunger"] > 10.0
    assert served_dto["biological"]["hunger"] == next_state.entities[entity_id].biological.hunger


def test_consumer_2_full_scan_or_explicit_dirty_tag_avoids_the_staleness():
    """Control: the same scenario does NOT go stale when dirty_set legitimately includes the
    entity (e.g. force_full_scan, or any real per-tick invalidation path) -- isolates the defect
    to the passive-decay omission specifically, not to ReadModelCache's invalidation logic itself
    (already covered generically by tests/unit/api/test_read_model_cache.py)."""
    prior_state, refined, next_state = _run_real_passive_decay_tick()
    entity_id = 1

    cache = ReadModelCache()
    cache.update(prior_state, dirty_set=None)
    cache.get_entity_dto(prior_state.entities[entity_id])

    cache.update(next_state, dirty_set=refined.dirty_set, force_full_scan=True)
    fresh_dto = cache.get_entity_dto(next_state.entities[entity_id])

    assert fresh_dto["biological"]["hunger"] > 10.0
