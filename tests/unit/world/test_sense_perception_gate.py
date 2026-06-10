"""
Tests for PerceptionGate.

Verifies:
- Wolf (predator_smell_senses) detects scent signal better than normal humanoid
- Spider (spider_vibration_senses) detects vibration signal
- Arcane (arcane_senses) detects magic_signal
- Normal humanoid cannot detect magic_signal
- Entity with no sense_profile_id uses baseline humanoid defaults
- Perception is deterministic for same inputs
- Gate never mutates catalog or entity
- PerceptionResult profile_source reflects profile used
"""

from __future__ import annotations

import pytest
from types import SimpleNamespace

from src.content.repository import CatalogRepository
from src.world.perception.gate import PerceptionGate, PerceptionResult


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def gate(catalog):
    return PerceptionGate(catalog)


def _entity(sense_profile_id=None):
    props = {}
    if sense_profile_id:
        props["sense_profile_id"] = sense_profile_id
    identity = SimpleNamespace(properties=props)
    return SimpleNamespace(identity=identity)


# ---------------------------------------------------------------------------
# Archetype test cases
# ---------------------------------------------------------------------------

def test_wolf_detects_scent_signal(gate):
    """Predator smell profile has very_high smell; scent signal should be perceived."""
    wolf = _entity("predator_smell_senses")
    result = gate.can_perceive(wolf, {"scent": "medium"}, {"distance": 5.0})
    assert result.perceived, "Wolf should detect scent signal"
    assert "scent" in result.signals_used
    assert result.profile_source == "predator_smell_senses"


def test_normal_humanoid_weaker_scent_than_wolf(gate):
    """Normal humanoid has low smell; same scent signal → lower confidence than wolf."""
    human = _entity("normal_humanoid_senses")
    wolf = _entity("predator_smell_senses")
    ctx = {"distance": 5.0}
    human_result = gate.can_perceive(human, {"scent": "medium"}, ctx)
    wolf_result = gate.can_perceive(wolf, {"scent": "medium"}, ctx)
    assert wolf_result.confidence >= human_result.confidence


def test_spider_detects_vibration(gate):
    """Spider vibration profile has very_high vibration; vibration signal detected."""
    spider = _entity("spider_vibration_senses")
    result = gate.can_perceive(spider, {"vibration": "low"}, {"distance": 2.0})
    assert result.perceived, "Spider should detect vibration"
    assert "vibration" in result.signals_used
    assert result.profile_source == "spider_vibration_senses"


def test_arcane_entity_detects_magic_signal(gate):
    """Arcane senses profile has high magic_sense; magic_signal detected."""
    mage = _entity("arcane_senses")
    result = gate.can_perceive(mage, {"magic_signal": "high"}, {"distance": 3.0})
    assert result.perceived, "Arcane entity should detect magic signal"
    assert "magic_signal" in result.signals_used
    assert result.profile_source == "arcane_senses"


def test_normal_humanoid_cannot_detect_magic_signal(gate):
    """Normal humanoid has magic_sense=none; magic_signal not perceived."""
    human = _entity("normal_humanoid_senses")
    result = gate.can_perceive(human, {"magic_signal": "very_high"}, {"distance": 1.0})
    assert "magic_signal" not in result.signals_used


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

def test_no_sense_profile_uses_baseline_humanoid(gate):
    """Entity without sense_profile_id falls back to baseline_humanoid defaults."""
    entity = _entity()
    result = gate.can_perceive(entity, {"visibility": "medium"})
    assert result.profile_source == "baseline_humanoid"
    assert result.perceived


def test_unknown_sense_profile_falls_back_to_baseline(gate):
    """Entity with unrecognised sense_profile_id falls back to baseline."""
    entity = _entity("nonexistent_profile_xyz")
    result = gate.can_perceive(entity, {"visibility": "medium"})
    assert result.profile_source == "baseline_humanoid"


# ---------------------------------------------------------------------------
# Determinism and immutability
# ---------------------------------------------------------------------------

def test_perception_is_deterministic(gate):
    wolf = _entity("predator_smell_senses")
    signals = {"scent": "medium", "noise": "low"}
    ctx = {"distance": 10.0, "alertness": 0.7}
    result_a = gate.can_perceive(wolf, signals, ctx)
    result_b = gate.can_perceive(wolf, signals, ctx)
    assert result_a == result_b


def test_gate_does_not_mutate_catalog(catalog):
    profile_count = len(catalog.sense_profiles) if hasattr(catalog, "sense_profiles") else None
    gate = PerceptionGate(catalog)
    entity = _entity("predator_smell_senses")
    gate.can_perceive(entity, {"scent": "high"})
    if profile_count is not None:
        assert len(catalog.sense_profiles) == profile_count


# ---------------------------------------------------------------------------
# Context effects
# ---------------------------------------------------------------------------

def test_high_distance_reduces_confidence(gate):
    wolf = _entity("predator_smell_senses")
    near = gate.can_perceive(wolf, {"scent": "high"}, {"distance": 1.0})
    far = gate.can_perceive(wolf, {"scent": "high"}, {"distance": 40.0})
    assert near.confidence > far.confidence


def test_no_signal_means_no_perception(gate):
    wolf = _entity("predator_smell_senses")
    result = gate.can_perceive(wolf, {"scent": "none"})
    assert "scent" not in result.signals_used
