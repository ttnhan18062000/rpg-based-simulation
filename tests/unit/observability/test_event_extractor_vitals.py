"""TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP — biological/stamina/wound event coverage."""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tools.calibrate_simq import _load_world_state  # noqa: E402
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.core.state import ScarState, WoundState  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.observability.event_extractor import EventExtractor  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402


def _run_real_ticks(world_name: str, seed: int, ticks: int):
    state, _report = _load_world_state(world_name, seed)
    rng = DeterministicRNG(state.seed)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=rng, flags={"no_frame_pacing": True})
    try:
        extractor = EventExtractor()
        prior = kernel.state
        all_events = []
        for _ in range(ticks):
            kernel.tick_once()
            all_events.extend(extractor.extract(prior, kernel.state, None, mode=None))
            prior = kernel.state
        return all_events
    finally:
        kernel.shutdown()


def test_biological_state_changed_fires_through_real_kernel_tick_once():
    events = _run_real_ticks("sandbox_world", 42, 15)
    matches = [e for e in events if e.event_type == "biological_state_changed"]
    assert matches, "biological_state_changed never fired through a real 15-tick loop"


def test_stamina_changed_fires_through_real_kernel_tick_once():
    events = _run_real_ticks("sandbox_world", 42, 15)
    matches = [e for e in events if e.event_type == "stamina_changed"]
    assert matches, "stamina_changed never fired through a real 15-tick loop"


def _wound_fixture_states():
    """Real EntityState/WoundState objects — combat is corpus-wide gated off
    (ENABLE_COMBAT_ENGAGEMENT), so a live Kernel.tick_once() loop cannot naturally produce a
    wound right now. Matches this repo's own precedented pattern for gated mechanics (see
    test_information_intent_execution_fires_through_kernel_tick_once)."""
    state, _report = _load_world_state("sandbox_world", 42)
    eid = next(iter(state.entities.keys()))
    prior_ent = state.entities[eid]
    return state, eid, prior_ent


def test_wound_sustained_severity_mapping():
    state, eid, prior_ent = _wound_fixture_states()
    extractor = EventExtractor()
    for severity, expected in [(0.8, "CRITICAL"), (0.5, "WARNING"), (0.1, "INFO")]:
        wound = WoundState(id=f"w-{severity}", kind="SLASH", severity=severity, tick_inflicted=state.tick)
        new_combat = replace(prior_ent.combat, wounds=[wound])
        new_ent = replace(prior_ent, combat=new_combat)
        new_state = replace(state, entities={**state.entities, eid: new_ent})
        events = extractor.extract(state, new_state, None, mode=None)
        matches = [e for e in events if e.event_type == "wound_sustained"]
        assert len(matches) == 1
        assert matches[0].severity == expected


def test_wound_healed_fires():
    state, eid, prior_ent = _wound_fixture_states()
    extractor = EventExtractor()
    wound = WoundState(id="w1", kind="SLASH", severity=0.5, tick_inflicted=state.tick)
    combat_with_wound = replace(prior_ent.combat, wounds=[wound])
    ent_with_wound = replace(prior_ent, combat=combat_with_wound)
    state_with_wound = replace(state, entities={**state.entities, eid: ent_with_wound})

    healed_wound = replace(wound, healed=True)
    combat_healed = replace(combat_with_wound, wounds=[healed_wound])
    ent_healed = replace(ent_with_wound, combat=combat_healed)
    state_healed = replace(state, entities={**state.entities, eid: ent_healed})

    events = extractor.extract(state_with_wound, state_healed, None, mode=None)
    matches = [e for e in events if e.event_type == "wound_healed"]
    assert len(matches) == 1


def test_scar_gained_fires():
    state, eid, prior_ent = _wound_fixture_states()
    extractor = EventExtractor()
    scar = ScarState(id="s1", wound_kind="SLASH", tick_created=state.tick)
    scarred_combat = replace(prior_ent.combat, scars=[scar])
    scarred_ent = replace(prior_ent, combat=scarred_combat)
    scarred_state = replace(state, entities={**state.entities, eid: scarred_ent})

    events = extractor.extract(state, scarred_state, None, mode=None)
    matches = [e for e in events if e.event_type == "scar_gained"]
    assert len(matches) == 1


def test_vitals_events_suppressed_in_light_and_long_run_modes():
    from src.observability.config import ObservabilityMode

    state, eid, prior_ent = _wound_fixture_states()
    bio = prior_ent.biological
    changed_bio = replace(bio, hunger=bio.hunger + 5.0)
    changed_ent = replace(prior_ent, biological=changed_bio)
    changed_state = replace(state, entities={**state.entities, eid: changed_ent})

    extractor = EventExtractor()
    for mode in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
        events = extractor.extract(state, changed_state, None, mode=mode)
        matches = [e for e in events if e.event_type == "biological_state_changed"]
        assert not matches, f"biological_state_changed fired in {mode}, should be suppressed"
