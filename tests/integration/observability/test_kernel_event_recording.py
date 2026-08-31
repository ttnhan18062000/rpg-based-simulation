from __future__ import annotations
import pytest
from src.engine.kernel import Kernel
from src.core.state import AuthoritativeState
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.core.builder import V2EntityBuilder
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.events import LifecycleEvent

def test_kernel_observability_event_recording(tmp_path):
    # Enable CERTIFICATION mode
    ObservabilityConfig.set_override_mode(ObservabilityMode.CERTIFICATION)
    
    profile = RuntimeProfile(
        name="test-obs-recording",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=16.6
    )

    # Setup one active entity in current state
    e1 = V2EntityBuilder(1).combat(hp=100, alive=True).location(10.0, 10.0).build()
    state = AuthoritativeState(tick=1, seed=42, world_time=101, entities={1: e1})
    rng = DeterministicRNG(42)
    
    # Initialize kernel with current state
    kernel = Kernel(profile, state, rng)
    
    # Prior state has empty entities list (representing spawn of entity 1)
    prior_state = AuthoritativeState(tick=0, seed=42, world_time=100, entities={})
    
    # Invoke post-tick observability phase manually to verify seamless event flow
    kernel._phase_observability(prior_state, None)
    
    # The spawn event should be recorded in kernel._entity_timeline_store
    timeline = kernel._entity_timeline_store.get_entity_timeline(1)
    assert len(timeline) >= 1
    
    # The event should be a spawn LifecycleEvent
    spawn_evs = [ev for ev in timeline if isinstance(ev, LifecycleEvent) and ev.action == "spawn"]
    assert len(spawn_evs) == 1
    assert spawn_evs[0].entity_id == 1
    assert spawn_evs[0].tick == 1
    
    # Assert events exist in recorder
    assert len(kernel._event_recorder.events) >= 1
    assert any(isinstance(ev, LifecycleEvent) and ev.action == "spawn" for ev in kernel._event_recorder.events)
    
    # Shutdown kernel
    kernel.shutdown()

    # Reset override mode
    ObservabilityConfig.set_override_mode(None)


def test_belief_assimilated_fires_through_real_tick_once_loop():
    """Kernel tick-alignment fix (event_extractor.py:286, compares against
    prior_state.tick instead of the post-advance tick): the compile-time-seeded
    pending_information_responses entry for urban_political's pop_0 now fires
    belief_assimilated through the real Kernel.tick_once() loop, not just the
    direct AuthoritativeApplyPipeline.refine() call
    (TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER)."""
    from dataclasses import replace as dataclass_replace
    from src.worldbuilding.schema import load_world_spec_from_yaml
    from src.worldbuilding.compiler import WorldCompiler
    from src.domains.optimization.feature_flags import FeatureMode
    from src.config.profiles import PROD_SMALL
    from src.platform.rng import DeterministicRNG as _RNG

    spec = load_world_spec_from_yaml("data/worlds/urban_political/resolved/world.resolved.yaml")
    compiled_state, _ = WorldCompiler.compile(spec, seed=42)
    compiled_state = dataclass_replace(
        compiled_state, feature_flags={"ENABLE_BELIEF_ASSIMILATION": FeatureMode.ON}
    )
    actor_id = compiled_state.pending_information_responses[0]["actor_id"]

    ObservabilityConfig.set_override_mode(ObservabilityMode.NORMAL)
    kernel = Kernel(PROD_SMALL, compiled_state, _RNG(42))
    try:
        kernel.tick_once()
        belief_events = [
            ev for ev in kernel._event_recorder.events
            if getattr(ev, "event_type", None) == "belief_assimilated" and ev.entity_id == actor_id
        ]
        assert len(belief_events) == 1
        assert belief_events[0].payload["subject"] == "bandit_road_danger"
    finally:
        kernel.shutdown()
        ObservabilityConfig.set_override_mode(None)


def test_calamity_spawned_fires_through_real_tick_once_loop():
    """Kernel tick-alignment fix (event_extractor.py:899, compares against
    prior_state.tick instead of the post-advance tick): calamity_spawned had
    never fired through any real Kernel.tick_once() loop prior to this fix.
    A minimal state meeting CalamityService's spawn gates (tick a multiple of
    CALAMITY_FORCE_INTERVAL=5000, >= CALAMITY_MIN_INTERVAL=2000 ticks since
    last_calamity_tick, a region with calamity_intensity > 0.3) fires it once
    on the real loop (TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER)."""
    from src.core.state import RegionState
    from src.config.profiles import PROD_SMALL
    from src.platform.rng import DeterministicRNG as _RNG

    region = RegionState(
        id="danger_region", name="Danger Region", bounds=(0, 0, 10, 10),
        calamity_intensity=0.5,
    )
    state = AuthoritativeState(
        tick=5000, seed=42, world_time=0, last_calamity_tick=0,
        regions={"danger_region": region},
    )

    ObservabilityConfig.set_override_mode(ObservabilityMode.NORMAL)
    kernel = Kernel(PROD_SMALL, state, _RNG(42))
    try:
        kernel.tick_once()
        calamity_events = [
            ev for ev in kernel._event_recorder.events
            if getattr(ev, "event_type", None) == "calamity_spawned"
        ]
        assert len(calamity_events) == 1
        # payload["tick"]/event.tick both use the post-advance tick label (kernel.py's
        # existing, unchanged convention — only the stamped-property comparison that
        # gates whether this event fires at all was fixed, not the tick label itself).
        assert calamity_events[0].payload["tick"] == 5001
        assert calamity_events[0].tick == 5001
    finally:
        kernel.shutdown()
        ObservabilityConfig.set_override_mode(None)


def test_wound_sustained_fires_through_real_tick_once_loop():
    """event_extractor.py's wound/scar diff blocks (lines ~280-281, ~302-303) gated
    entity_wounds/entity_scars with `isinstance(x, list)` -- but the real, authoritative apply
    path (WoundPatch.apply, src/engine/patches.py:639; AuthoritativeState's freeze logic,
    src/core/state.py:846) always commits wounds/scars as tuples, so the check was always False
    and wound_sustained never fired through any real Kernel.tick_once() loop
    (TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND). Reuses the exact deterministic
    combat fixture from
    tests/integration/combat/test_wound_healing_permanence.py::test_wound_healed_and_scar_gained_have_zero_production_producers
    (attacker ATK 80 vs. defender max_hp 100, hostile factions, adjacent,
    ENABLE_COMBAT_ENGAGEMENT ON, seed 42) that reliably inflicts a real wound at tick 9 through
    the full production combat-resolution path -- proving, after the isinstance(x, (list, tuple))
    fix, that wound_sustained now genuinely reaches the event-observability layer, not just
    authoritative state."""
    from dataclasses import replace as dataclass_replace
    from src.core.enums import Faction
    from src.core.state import EntityRole
    from src.config.profiles import PROD_SMALL
    from src.platform.rng import DeterministicRNG as _RNG

    def _make_combatant(eid, pos, faction_id, faction_enum, atk, hp=100, def_stat=1):
        return (
            V2EntityBuilder(eid)
            .kind("actor")
            .location(*pos)
            .identity(faction=faction_enum, role=EntityRole.HERO, properties={"faction_id": faction_id})
            .combat(hp=hp, max_hp=hp, atk=atk, def_stat=def_stat, attack_range=2, readiness=100.0, alive=True)
            .lifecycle(active=True)
            .build()
        )

    attacker = _make_combatant(1, (1.0, 1.0), "hero_guild", Faction.HERO_GUILD, atk=80, hp=100, def_stat=1)
    defender = _make_combatant(2, (2.0, 1.0), "goblin_warband", Faction.MONSTER_HORDE, atk=1, hp=100, def_stat=1)

    state = AuthoritativeState(tick=0, seed=42, entities={1: attacker, 2: defender})
    state = dataclass_replace(state, feature_flags={"ENABLE_COMBAT_ENGAGEMENT": "ON"})

    ObservabilityConfig.set_override_mode(ObservabilityMode.NORMAL)
    rng = _RNG(42)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=rng, flags={"no_frame_pacing": True, "no_replay": True})
    try:
        for _ in range(40):
            kernel.tick_once()

        wound_events = [
            ev for ev in kernel._event_recorder.events
            if getattr(ev, "event_type", None) == "wound_sustained"
        ]
        assert wound_events, (
            "wound_sustained never fired through the real Kernel.tick_once() event-observability "
            "layer -- the isinstance(x, (list, tuple)) fix at event_extractor.py:280-281 regressed"
        )
        assert wound_events[0].entity_id == 2
        assert wound_events[0].payload["wound_id"]
    finally:
        kernel.shutdown()
        ObservabilityConfig.set_override_mode(None)


def test_governor_mode_changed_fires_through_real_tick_once_loop():
    """Kernel tick-alignment fix (kernel.py:836, compares against
    prior_state.tick instead of the post-advance tick): GovernorModeChanged had
    never fired through any real Kernel.tick_once() loop prior to this fix.
    Seeding state.work_debt above the profile's max_work_debt makes
    ResourceGovernor._get_indicated_mode() escalate to SURVIVAL on the very
    first tick, which reset_dwell() stamps with the pre-advance tick
    (TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER)."""
    from src.platform.rng import DeterministicRNG as _RNG

    profile = RuntimeProfile(
        name="test-governor-escalation",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1024,
        max_cpu_percent=100.0,
        max_worker_count=1,
        max_queue_depth=100,
        max_work_debt=100,
        max_replay_buffer_kb=0,
        max_observability_budget_percent=0.0,
        max_tick_budget_ms=16.6,
    )
    state = AuthoritativeState(tick=0, seed=7, world_time=0, work_debt={"queue": 500})

    ObservabilityConfig.set_override_mode(ObservabilityMode.NORMAL)
    kernel = Kernel(profile, state, _RNG(7))
    try:
        kernel.tick_once()
        mode_events = [
            ev for ev in kernel._event_recorder.events
            if getattr(ev, "event_type", None) == "GovernorModeChanged"
        ]
        assert len(mode_events) == 1
        assert mode_events[0].payload["current_mode"] == "SURVIVAL"
    finally:
        kernel.shutdown()
        ObservabilityConfig.set_override_mode(None)
