"""
Behavioral tests for MotivationPressureResolver + PerceptionGate wired into
TacticalDecisionSystem.evaluate_entity_intent.

Acceptance criteria (TCK-20260610-PRESSURE-PERCEPTION-CONSUMERS):
- Unperceived enemy cannot be selected as combat target
- Territorial animal scores intruder higher when territory_pressure elevated
- Merchant flee decision triggered by safety_pressure above threshold
- Guard prioritises duty-related threat when duty_pressure elevated
- All tests are deterministic and do not use scripted behavior
"""

from __future__ import annotations

import pytest
from dataclasses import replace
from types import SimpleNamespace

from src.content.repository import CatalogRepository
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
from src.engine.tactical import TacticalDecisionSystem


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(autouse=True, scope="module")
def configure_consumers(catalog):
    configure_behavior_consumers(catalog)
    yield
    reset_behavior_consumers()


def _hero(eid: int, pos=(0.0, 0.0), **props):
    e = (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(float(pos[0]), float(pos[1]))
        .identity(faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, tactical_role="VANGUARD", readiness=100.0)
        .lifecycle(active=True)
        .build()
    )
    if props:
        merged = {**(e.identity.properties or {}), **props}
        e = replace(e, identity=replace(e.identity, properties=merged))
    return e


def _monster(eid: int, pos=(1.0, 0.0), **props):
    e = (
        V2EntityBuilder(eid)
        .kind("monster")
        .location(float(pos[0]), float(pos[1]))
        .identity(faction=Faction.MONSTER_HORDE)
        .combat(hp=100, max_hp=100, alive=True, tactical_role="VANGUARD", readiness=100.0)
        .lifecycle(active=True)
        .build()
    )
    if props:
        merged = {**(e.identity.properties or {}), **props}
        e = replace(e, identity=replace(e.identity, properties=merged))
    return e


# ---------------------------------------------------------------------------
# 1. Perception gate: unperceived enemy cannot be targeted
# ---------------------------------------------------------------------------

def test_magic_only_target_not_perceived_by_normal_humanoid():
    """
    A target emitting only magic_signal with no visibility/noise/scent is invisible
    to a normal humanoid (magic_sense=none). It must not appear as a combat target.
    """
    attacker = _hero(1, pos=(0.0, 0.0), sense_profile_id="normal_humanoid_senses")
    # Target emits only magic_signal; normal humanoid cannot detect it
    target = _monster(2, pos=(1.0, 0.0),
                      visibility_signal="none", noise_signal="none", scent_signal="none",
                      magic_signal="very_high", life_signal="none", vibration_signal="none")

    state = AuthoritativeState(tick=1, seed=1, entities={1: attacker, 2: target})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)

    # No combat target should be selected
    assert update.task is None or update.task.payload_set is None or \
        update.task.payload_set.get("target_id") != 2, \
        "Normal humanoid should not target magic-only entity it cannot perceive"


def test_arcane_entity_can_target_magic_only_signal():
    """
    An entity with arcane_senses (high magic_sense) CAN perceive a magic-only target.
    """
    attacker = _hero(1, pos=(0.0, 0.0), sense_profile_id="arcane_senses")
    target = _monster(2, pos=(1.0, 0.0),
                      visibility_signal="none", noise_signal="none", scent_signal="none",
                      magic_signal="high", life_signal="none", vibration_signal="none")

    state = AuthoritativeState(tick=1, seed=1, entities={1: attacker, 2: target})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)

    assert update.task is not None and update.task.payload_set is not None
    assert update.task.payload_set.get("target_id") == 2, \
        "Arcane entity should perceive magic-only target"


# ---------------------------------------------------------------------------
# 2. Territory pressure: territorial entity prioritises targets more aggressively
# ---------------------------------------------------------------------------

def test_territorial_entity_selects_target_with_elevated_priority(catalog):
    """
    Entity with territorial_predator drive (high territory_pressure) should
    select targets more aggressively (lower effective distance in scoring).
    The test verifies it still selects a valid target — priority adjustment is
    deterministic and data-driven.
    """
    attacker = _hero(1, pos=(0.0, 0.0),
                     sense_profile_id="predator_smell_senses",
                     drive_profile_id="territorial_predator")
    near = _monster(2, pos=(2.0, 0.0))
    far = _monster(3, pos=(5.0, 0.0))

    state = AuthoritativeState(tick=1, seed=1, entities={1: attacker, 2: near, 3: far})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)

    assert update.task is not None and update.task.payload_set is not None
    target_id = update.task.payload_set.get("target_id")
    assert target_id in (2, 3), "Territorial entity should select a combat target"


# ---------------------------------------------------------------------------
# 3. Safety pressure: merchant-type entity retreats from hostiles
# ---------------------------------------------------------------------------

def test_safety_pressure_above_threshold_triggers_retreat():
    """
    Entity with cautious_commoner drive (high safety_pressure > 0.75) should
    retreat when hostiles are detected, not engage.
    """
    # cautious_commoner drive: safety_pressure is high (see data/content/living/drive_profiles.yaml)
    merchant = _hero(1, pos=(0.0, 0.0),
                     drive_profile_id="cautious_commoner")
    attacker = _monster(2, pos=(1.0, 0.0))

    state = AuthoritativeState(tick=1, seed=1, entities={1: merchant, 2: attacker})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, merchant)

    # Should retreat rather than engage
    assert update.task is not None
    assert update.task.work_kind_set == "ENTITY_MOVE"
    reason = (update.task.payload_set or {}).get("reason", "")
    assert reason == "SAFETY_PRESSURE_RETREAT", \
        f"Expected SAFETY_PRESSURE_RETREAT, got {reason!r}"


def test_low_safety_pressure_does_not_trigger_retreat():
    """
    Entity with low safety_pressure should NOT trigger safety retreat.
    """
    # Use an entity with no pressure profiles (all pressures = 0.0)
    warrior = _hero(1, pos=(0.0, 0.0))
    attacker = _monster(2, pos=(1.0, 0.0))

    state = AuthoritativeState(tick=1, seed=1, entities={1: warrior, 2: attacker})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, warrior)

    reason = (update.task.payload_set or {}).get("reason", "")
    assert reason != "SAFETY_PRESSURE_RETREAT", \
        "Low-safety entity should not trigger safety retreat"


# ---------------------------------------------------------------------------
# 4. Duty pressure: guard prioritises threats more aggressively
# ---------------------------------------------------------------------------

def test_duty_pressure_entity_selects_target():
    """
    Entity with disciplined_protector drive (high duty_pressure, medium safety)
    should engage combat targets — duty pressure reduces effective distance.
    """
    # disciplined_protector: duty=high, safety=medium (0.6 < 0.75 threshold → no flee)
    guard = _hero(1, pos=(0.0, 0.0), drive_profile_id="disciplined_protector")
    attacker = _monster(2, pos=(3.0, 0.0))

    state = AuthoritativeState(tick=1, seed=1, entities={1: guard, 2: attacker})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, guard)

    assert update.task is not None and update.task.payload_set is not None
    assert update.task.payload_set.get("target_id") == 2


# ---------------------------------------------------------------------------
# 5. Determinism
# ---------------------------------------------------------------------------

def test_tactical_decision_with_consumers_is_deterministic():
    """Same state + pressures → identical EntityUpdate."""
    entity = _hero(1, pos=(0.0, 0.0), sense_profile_id="normal_humanoid_senses")
    enemy = _monster(2, pos=(1.0, 0.0))

    state = AuthoritativeState(tick=1, seed=1, entities={1: entity, 2: enemy})
    upd_a = TacticalDecisionSystem.evaluate_entity_intent(state, entity)
    upd_b = TacticalDecisionSystem.evaluate_entity_intent(state, entity)

    assert (upd_a.task.payload_set if upd_a.task else None) == \
           (upd_b.task.payload_set if upd_b.task else None)
