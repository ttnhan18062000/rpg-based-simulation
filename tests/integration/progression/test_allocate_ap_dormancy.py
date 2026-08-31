"""
tests/integration/progression/test_allocate_ap_dormancy.py

TCK-20260824-ALLOCATE-AP-BRANCH-DECISION

Dormancy proof backing DEV-004 (docs/guidelines/intentional_divergences.md): over a real,
non-mocked Kernel.tick_once() loop against a real compiled world, neither of the two
ALLOCATE_AP implementations ever fires --
src/engine/domain/core_actions.py::execute_allocate_ap (wired into ActionRouter, but with no
payload producer anywhere in src/) nor src/domains/progression/resolver.py's
ConversionIntentResolver.resolve ConversionKind.ALLOCATE_AP branch (real gap-resolution
pipeline, but gated behind ENABLE_PROGRESSION_EVOLUTION == FeatureMode.OFF per DEV-003).

Both implementations' only observable footprint is a negative
IdentityUpdate.unspent_ap_delta -- grep-confirmed the only two negative-unspent_ap_delta call
sites anywhere in src/ are src/domains/progression/resolver.py:90 and
src/engine/domain/core_actions.py:173; src/engine/evolution.py:122 (the real, live AP
producer -- level-up milestones) only ever grants AP, never spends it. Tracking that no
entity's unspent_ap ever decreases across a real tick loop is therefore airtight proof that
neither path fired, unlike checking for attribute_changed events alone: both dormant branches
can decrement unspent_ap while granting a zero, no-op AttributeUpdate for any of the 7
unhandled attribute names, which produces no attribute_changed event at all (see the
corrected PROG-068/PROG-069 parity_ledger entries and
tests/unit/quest/test_progression_regression.py::test_execute_allocate_ap_silently_no_ops_for_unhandled_attribute).
"""
from __future__ import annotations

from src.worldbuilding.schema import load_world_spec_from_yaml
from src.worldbuilding.compiler import WorldCompiler
from src.config.profiles import PROD_SMALL
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel
from src.observability.config import ObservabilityConfig, ObservabilityMode

_TICKS = 150


def test_allocate_ap_unreachable_via_real_kernel_tick():
    spec = load_world_spec_from_yaml("data/worlds/sandbox_world/resolved/world.resolved.yaml")
    state, _report = WorldCompiler.compile(spec, seed=42)

    ObservabilityConfig.set_override_mode(ObservabilityMode.NORMAL)
    kernel = Kernel(PROD_SMALL, state, DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        prior_unspent_ap = {
            eid: entity.identity.unspent_ap for eid, entity in kernel.state.entities.items()
        }
        decreased_ap_ticks: list[tuple[int, int]] = []

        for _ in range(_TICKS):
            kernel.tick_once()
            for eid, entity in kernel.state.entities.items():
                prior = prior_unspent_ap.get(eid, entity.identity.unspent_ap)
                if entity.identity.unspent_ap < prior:
                    decreased_ap_ticks.append((kernel.state.tick, eid))
                prior_unspent_ap[eid] = entity.identity.unspent_ap

        assert decreased_ap_ticks == [], (
            "unspent_ap decreased for (tick, entity_id) pairs "
            f"{decreased_ap_ticks} -- an ALLOCATE_AP path fired despite being decided dormant "
            "per DEV-004 (docs/guidelines/intentional_divergences.md)"
        )

        decreased_ap_tick_entity_pairs = {(t, e) for t, e in decreased_ap_ticks}
        allocate_ap_attribute_events = [
            ev for ev in kernel._event_recorder.events
            if getattr(ev, "event_type", None) == "attribute_changed"
            and (ev.tick, ev.entity_id) in decreased_ap_tick_entity_pairs
        ]
        assert allocate_ap_attribute_events == [], (
            "found attribute_changed events co-occurring with an unspent_ap decrease -- "
            "this would be the signature of a live ALLOCATE_AP path"
        )
    finally:
        kernel.shutdown()
        ObservabilityConfig.set_override_mode(None)
