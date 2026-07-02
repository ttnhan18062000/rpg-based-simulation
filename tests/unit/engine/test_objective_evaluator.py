"""
Unit tests for ObjectiveEvaluator.

Ticket: TCK-20260619-E31B-OBJECTIVE-FSM
AC coverage:
  - Empty conditions → RUNNING
  - None conditions → RUNNING
  - tick_limit exact boundary (>=)
  - tick_limit not yet reached
  - tick_limit exceeded
  - entity_count with alive/dead mix (uses e.combat.alive, not len(entities))
  - entity_count above threshold → RUNNING
  - Unknown kind skipped (no crash)
  - Multiple conditions: first-match-wins
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


def _make_state(tick: int = 0, entities: dict | None = None) -> MagicMock:
    """Build a minimal mock AuthoritativeState."""
    state = MagicMock()
    state.tick = tick
    state.entities = entities if entities is not None else {}
    return state


def _alive_entity() -> MagicMock:
    e = MagicMock()
    e.combat.alive = True
    return e


def _dead_entity() -> MagicMock:
    e = MagicMock()
    e.combat.alive = False
    return e


class TestObjectiveEvaluatorEmptyAndNone:
    def test_none_conditions_returns_running(self):
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        state = _make_state(tick=9999)
        result = ObjectiveEvaluator.evaluate(state, None)
        assert result == ScenarioObjectiveState.RUNNING

    def test_empty_list_returns_running(self):
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        state = _make_state(tick=9999)
        result = ObjectiveEvaluator.evaluate(state, [])
        assert result == ScenarioObjectiveState.RUNNING


class TestTickLimitCondition:
    def test_tick_limit_exact_boundary_fires(self):
        """state.tick == value → OBJECTIVE_MET."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        state = _make_state(tick=50)
        result = ObjectiveEvaluator.evaluate(state, [{"kind": "tick_limit", "value": 50}])
        assert result == ScenarioObjectiveState.OBJECTIVE_MET

    def test_tick_limit_exceeded_fires(self):
        """state.tick > value → OBJECTIVE_MET."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        state = _make_state(tick=51)
        result = ObjectiveEvaluator.evaluate(state, [{"kind": "tick_limit", "value": 50}])
        assert result == ScenarioObjectiveState.OBJECTIVE_MET

    def test_tick_limit_not_reached_stays_running(self):
        """state.tick < value → RUNNING."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        state = _make_state(tick=49)
        result = ObjectiveEvaluator.evaluate(state, [{"kind": "tick_limit", "value": 50}])
        assert result == ScenarioObjectiveState.RUNNING

    def test_tick_limit_zero_fires_immediately(self):
        """tick_limit: 0 fires at tick 0."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        state = _make_state(tick=0)
        result = ObjectiveEvaluator.evaluate(state, [{"kind": "tick_limit", "value": 0}])
        assert result == ScenarioObjectiveState.OBJECTIVE_MET

    def test_tick_limit_with_model_object(self):
        """Accepts VictoryCondition-like objects (attribute access)."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        cond = MagicMock()
        cond.kind = "tick_limit"
        cond.value = 10
        state = _make_state(tick=10)
        result = ObjectiveEvaluator.evaluate(state, [cond])
        assert result == ScenarioObjectiveState.OBJECTIVE_MET


class TestEntityCountCondition:
    def test_all_dead_below_threshold_fires_failed(self):
        """All entities dead and alive count < threshold → OBJECTIVE_FAILED."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        entities = {1: _dead_entity(), 2: _dead_entity()}
        state = _make_state(tick=5, entities=entities)
        result = ObjectiveEvaluator.evaluate(state, [{"kind": "entity_count", "value": 1}])
        assert result == ScenarioObjectiveState.OBJECTIVE_FAILED

    def test_zero_entities_below_threshold_fires_failed(self):
        """Empty entity dict, value=1 → OBJECTIVE_FAILED."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        state = _make_state(tick=5, entities={})
        result = ObjectiveEvaluator.evaluate(state, [{"kind": "entity_count", "value": 1}])
        assert result == ScenarioObjectiveState.OBJECTIVE_FAILED

    def test_enough_alive_stays_running(self):
        """alive count >= threshold → RUNNING."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        entities = {1: _alive_entity(), 2: _alive_entity()}
        state = _make_state(tick=5, entities=entities)
        result = ObjectiveEvaluator.evaluate(state, [{"kind": "entity_count", "value": 1}])
        assert result == ScenarioObjectiveState.RUNNING

    def test_uses_combat_alive_not_dict_len(self):
        """Dead entities in the dict are NOT counted as alive (guards e.combat.alive)."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        # One alive, one dead; value=2 → alive(1) < 2 → OBJECTIVE_FAILED
        entities = {1: _alive_entity(), 2: _dead_entity()}
        state = _make_state(tick=5, entities=entities)
        result = ObjectiveEvaluator.evaluate(state, [{"kind": "entity_count", "value": 2}])
        assert result == ScenarioObjectiveState.OBJECTIVE_FAILED

    def test_exactly_at_threshold_stays_running(self):
        """alive == value → NOT failed (condition is alive < value)."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        entities = {1: _alive_entity()}
        state = _make_state(tick=5, entities=entities)
        # alive=1, value=1 → 1 < 1 is False → RUNNING
        result = ObjectiveEvaluator.evaluate(state, [{"kind": "entity_count", "value": 1}])
        assert result == ScenarioObjectiveState.RUNNING


class TestUnknownKind:
    def test_unknown_kind_is_skipped(self):
        """Unknown condition kinds are silently skipped — no crash, returns RUNNING."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        state = _make_state(tick=100)
        result = ObjectiveEvaluator.evaluate(
            state, [{"kind": "future_condition_kind", "value": 5}]
        )
        assert result == ScenarioObjectiveState.RUNNING

    def test_unknown_kind_does_not_prevent_later_match(self):
        """Unknown kind skipped; later tick_limit condition still fires."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        state = _make_state(tick=10)
        conditions = [
            {"kind": "unknown", "value": 5},
            {"kind": "tick_limit", "value": 10},
        ]
        result = ObjectiveEvaluator.evaluate(state, conditions)
        assert result == ScenarioObjectiveState.OBJECTIVE_MET


class TestMultipleConditionsFirstMatchWins:
    def test_tick_limit_before_entity_count(self):
        """tick_limit listed first; at tick==5 with 0 alive → OBJECTIVE_MET (not FAILED)."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        state = _make_state(tick=5, entities={})
        conditions = [
            {"kind": "tick_limit", "value": 5},
            {"kind": "entity_count", "value": 1},
        ]
        result = ObjectiveEvaluator.evaluate(state, conditions)
        assert result == ScenarioObjectiveState.OBJECTIVE_MET

    def test_entity_count_before_tick_limit(self):
        """entity_count listed first; 0 alive at tick 3 (limit=5) → OBJECTIVE_FAILED."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        state = _make_state(tick=3, entities={})
        conditions = [
            {"kind": "entity_count", "value": 1},
            {"kind": "tick_limit", "value": 5},
        ]
        result = ObjectiveEvaluator.evaluate(state, conditions)
        assert result == ScenarioObjectiveState.OBJECTIVE_FAILED

    def test_both_not_met_returns_running(self):
        """Neither condition met → RUNNING."""
        from src.engine.scenario_runtime import ObjectiveEvaluator, ScenarioObjectiveState
        entities = {1: _alive_entity(), 2: _alive_entity()}
        state = _make_state(tick=3, entities=entities)
        conditions = [
            {"kind": "tick_limit", "value": 10},
            {"kind": "entity_count", "value": 1},
        ]
        result = ObjectiveEvaluator.evaluate(state, conditions)
        assert result == ScenarioObjectiveState.RUNNING
