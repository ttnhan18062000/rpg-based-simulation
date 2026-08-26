"""Unit tests for EventExtractor.detect_grief_triggers()
(TCK-20260824-GRIEF-NEMESIS-REACHABILITY, Step 4).

detect_grief_triggers() re-walks the lifecycle.active True->False transition
independently of extract() (whose own List[SimulationEvent] return type must not
change), returning (griever_id, dead_ally_id, urgency) triples for every currently-alive
entity whose entity.social.trust_history toward the newly-dead entity meets
ALLY_TRUST_THRESHOLD (0.30).
"""
from __future__ import annotations

from unittest.mock import MagicMock

from src.observability.event_extractor import EventExtractor
from src.domains.campaigns.grief_urgency import ALLY_TRUST_THRESHOLD


def _entity(eid: int, active: bool = True, trust_history: dict | None = None):
    e = MagicMock()
    e.id = eid
    e.lifecycle = MagicMock()
    e.lifecycle.active = active
    e.social = MagicMock()
    e.social.trust_history = trust_history or {}
    return e


def _state(entities: dict):
    s = MagicMock()
    s.entities = entities
    return s


def test_detect_grief_triggers_finds_qualifying_ally():
    prior = _state({1: _entity(1), 2: _entity(2, active=True)})
    current = _state({
        1: _entity(1, trust_history={2: 0.9}),
        2: _entity(2, active=False),
    })

    triggers = EventExtractor.detect_grief_triggers(prior, current)

    assert triggers == [(1, 2, round(min(1.0, 0.9 * 0.8), 6))]


def test_detect_grief_triggers_below_threshold_not_included():
    prior = _state({1: _entity(1), 2: _entity(2, active=True)})
    current = _state({
        1: _entity(1, trust_history={2: ALLY_TRUST_THRESHOLD - 0.01}),
        2: _entity(2, active=False),
    })

    triggers = EventExtractor.detect_grief_triggers(prior, current)
    assert triggers == []


def test_detect_grief_triggers_no_death_no_triggers():
    prior = _state({1: _entity(1), 2: _entity(2, active=True)})
    current = _state({
        1: _entity(1, trust_history={2: 0.9}),
        2: _entity(2, active=True),
    })

    triggers = EventExtractor.detect_grief_triggers(prior, current)
    assert triggers == []


def test_detect_grief_triggers_ignores_dead_griever():
    """A grieving candidate that is itself no longer alive must not generate a trigger."""
    prior = _state({1: _entity(1), 2: _entity(2, active=True)})
    current = _state({
        1: _entity(1, active=False, trust_history={2: 0.9}),
        2: _entity(2, active=False),
    })

    triggers = EventExtractor.detect_grief_triggers(prior, current)
    assert triggers == []


def test_detect_grief_triggers_multiple_grievers():
    prior = _state({1: _entity(1), 2: _entity(2), 3: _entity(3, active=True)})
    current = _state({
        1: _entity(1, trust_history={3: 0.9}),
        2: _entity(2, trust_history={3: 0.5}),
        3: _entity(3, active=False),
    })

    triggers = EventExtractor.detect_grief_triggers(prior, current)
    triples = sorted(triggers)
    assert triples == sorted([
        (1, 3, round(min(1.0, 0.9 * 0.8), 6)),
        (2, 3, round(min(1.0, 0.5 * 0.8), 6)),
    ])


def test_detect_grief_triggers_new_entity_not_in_prior_state_skipped():
    """An entity present in current_state but absent from prior_state (a same-tick spawn)
    must not be treated as a death — prior_ent lookup returns None, so it's skipped."""
    prior = _state({1: _entity(1)})
    current = _state({
        1: _entity(1, trust_history={2: 0.9}),
        2: _entity(2, active=False),
    })

    triggers = EventExtractor.detect_grief_triggers(prior, current)
    assert triggers == []
