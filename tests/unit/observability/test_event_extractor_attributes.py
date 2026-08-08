"""TCK-20260808-ENTITY-ATTRIBUTES-OBSERVABILITY-GAP — attribute_changed event coverage.

Real-kernel verification was attempted first (per this ticket's own investigation.md plan) but
confirmed unreachable within a reasonable budget: `sandbox_world` has zero HERO-role entities (all
WORKER/GUARD/CITIZEN, all at evolution_level 1), and none leveled up within a real 1500-tick
Kernel.tick_once() loop (checked directly during Implement, not assumed) -- non-hero leveling
(src/engine/evolution.py's real, pipeline-wired producer) is simply too rare in this small
calibration world's timeframe to hit in a unit test. Falls back to this repo's own precedented
hand-built-state pattern instead (see test_information_intent_execution_fires_through_kernel_tick_once),
same fallback already used for wound_sustained/wound_healed/scar_gained in the sibling vitals
ticket.
"""
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tools.calibrate_simq import _load_world_state  # noqa: E402
from src.observability.event_extractor import EventExtractor  # noqa: E402


def _attr_fixture_states():
    state, _report = _load_world_state("sandbox_world", 42)
    eid = next(iter(state.entities.keys()))
    prior_ent = state.entities[eid]
    return state, eid, prior_ent


def test_attribute_changed_fires_on_real_delta():
    state, eid, prior_ent = _attr_fixture_states()
    extractor = EventExtractor()
    new_attrs = replace(
        prior_ent.attributes,
        strength=prior_ent.attributes.strength + 5,
        endurance=prior_ent.attributes.endurance + 2,
    )
    new_ent = replace(prior_ent, attributes=new_attrs)
    new_state = replace(state, entities={**state.entities, eid: new_ent})

    events = extractor.extract(state, new_state, None, mode=None)
    matches = [e for e in events if e.event_type == "attribute_changed"]
    assert len(matches) == 1
    assert matches[0].payload["deltas"] == {"strength": 5, "endurance": 2}


def test_attribute_changed_severity_negative_delta_is_warning():
    state, eid, prior_ent = _attr_fixture_states()
    extractor = EventExtractor()
    new_attrs = replace(prior_ent.attributes, strength=prior_ent.attributes.strength - 2)
    new_ent = replace(prior_ent, attributes=new_attrs)
    new_state = replace(state, entities={**state.entities, eid: new_ent})

    events = extractor.extract(state, new_state, None, mode=None)
    matches = [e for e in events if e.event_type == "attribute_changed"]
    assert len(matches) == 1
    assert matches[0].severity == "WARNING"


def test_attribute_changed_severity_positive_only_is_info():
    state, eid, prior_ent = _attr_fixture_states()
    extractor = EventExtractor()
    new_attrs = replace(prior_ent.attributes, vitality=prior_ent.attributes.vitality + 3)
    new_ent = replace(prior_ent, attributes=new_attrs)
    new_state = replace(state, entities={**state.entities, eid: new_ent})

    events = extractor.extract(state, new_state, None, mode=None)
    matches = [e for e in events if e.event_type == "attribute_changed"]
    assert len(matches) == 1
    assert matches[0].severity == "INFO"


def test_attribute_changed_payload_only_includes_changed_fields():
    state, eid, prior_ent = _attr_fixture_states()
    extractor = EventExtractor()
    new_attrs = replace(
        prior_ent.attributes,
        strength=prior_ent.attributes.strength + 1,
        wisdom=prior_ent.attributes.wisdom + 1,
    )
    new_ent = replace(prior_ent, attributes=new_attrs)
    new_state = replace(state, entities={**state.entities, eid: new_ent})

    events = extractor.extract(state, new_state, None, mode=None)
    matches = [e for e in events if e.event_type == "attribute_changed"]
    assert len(matches) == 1
    assert set(matches[0].payload["deltas"].keys()) == {"strength", "wisdom"}
    assert matches[0].payload["deltas"] == {"strength": 1, "wisdom": 1}


def test_attribute_changed_suppressed_in_light_and_long_run_modes():
    from src.observability.config import ObservabilityMode

    state, eid, prior_ent = _attr_fixture_states()
    new_attrs = replace(prior_ent.attributes, agility=prior_ent.attributes.agility + 1)
    new_ent = replace(prior_ent, attributes=new_attrs)
    new_state = replace(state, entities={**state.entities, eid: new_ent})

    extractor = EventExtractor()
    for mode in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
        events = extractor.extract(state, new_state, None, mode=mode)
        matches = [e for e in events if e.event_type == "attribute_changed"]
        assert not matches, f"attribute_changed fired in {mode}, should be suppressed"


def test_no_event_on_zero_delta():
    state, eid, prior_ent = _attr_fixture_states()
    extractor = EventExtractor()
    same_state = replace(state, entities={**state.entities, eid: prior_ent})

    events = extractor.extract(state, same_state, None, mode=None)
    matches = [e for e in events if e.event_type == "attribute_changed"]
    assert not matches, "attribute_changed fired with zero real delta"
