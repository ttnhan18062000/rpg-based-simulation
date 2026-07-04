"""Unit tests for AgencyScorer — SQ-01, SQ-02, SQ-12."""
from __future__ import annotations
import uuid

import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.scorers.agency import AgencyScorer
from src.simulation_quality.weights import ScoringWeights


def _ctx(tick: int = 10, window_tags: dict | None = None) -> ScoringContext:
    window = window_tags or {}
    return ScoringContext(
        run_id="test",
        current_tick=tick,
        entity_count=10,
        pillar_scores={p: 0.0 for p in PillarId},
        pillar_event_counts={p: 0 for p in PillarId},
        window_tag_counts={p: (window if p == PillarId.AGENCY else {}) for p in PillarId},
    )


def _env(event_type: str, tick: int = 10, entity_id: int = 1, payload: dict | None = None) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex,
        run_id="test",
        tick=tick,
        entity_id=entity_id,
        event_type=event_type,
        event_category="strategy",
        severity="INFO",
        source_system="test",
        message="",
        payload=payload or {},
    )


@pytest.fixture
def scorer(scoring_weights: ScoringWeights) -> AgencyScorer:
    return AgencyScorer(scoring_weights)


class TestActionExecuted:
    def test_positive_delta(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("action_executed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["action_taken"]
        assert rec.pillar == PillarId.AGENCY
        assert "action_taken" in rec.tags

    def test_null_for_unknown(self, scorer: AgencyScorer) -> None:
        rec = scorer.score(_env("unknown_event_xyz"), _ctx())
        assert rec is None


class TestRouteFamily:
    def test_novelty_reward(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("route_family_first_use"), _ctx())
        assert rec is not None
        expected = scoring_weights["route_novelty"] + scoring_weights["entropy_reward"]
        assert rec.delta == pytest.approx(expected)
        assert "route_novelty" in rec.tags
        assert "entropy_reward" in rec.tags


class TestRouteSelected:
    def test_navigation_active(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("route_selected"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["navigation_active"]
        assert "navigation_active" in rec.tags


class TestProjectCompleted:
    def test_project_done(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("project_completed", payload={}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["project_done"]
        assert "project_done" in rec.tags

    def test_commitment_complete(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("project_completed", payload={"is_commitment": True}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["commitment_complete"]
        assert "commitment_complete" in rec.tags


class TestDefer:
    def test_defer_base_delta(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("defer_with_reason"), _ctx(tick=100, window_tags={"defer_idle": 3, "action_taken": 1}))
        assert rec is not None
        assert rec.delta == scoring_weights["defer_idle"]
        assert "defer_idle" in rec.tags

    def test_stasis_no_fire_before_gate(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("stasis_gate_ticks")
        ctx = _ctx(tick=100, window_tags={"defer_idle": gate - 1, "action_taken": 1})
        rec = scorer.score(_env("defer_with_reason"), ctx)
        assert rec is not None
        assert "stasis_N" not in rec.tags

    def test_stasis_fires_after_gate(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("stasis_gate_ticks")
        cap = scoring_weights.int_param("stasis_extra_ticks_cap")
        entity_id = 42
        ctx = _ctx(tick=100, window_tags={"defer_idle": 0, "action_taken": 1})

        recs = []
        for call_num in range(1, gate + cap + 5):
            rec = scorer.score(_env("defer_with_reason", tick=100 + call_num, entity_id=entity_id), ctx)
            recs.append(rec)
            assert rec is not None

        # calls 1..gate: below/at gate, no stasis_N tag, flat defer_idle only
        for i in range(gate):
            assert "stasis_N" not in recs[i].tags
            assert recs[i].delta == pytest.approx(scoring_weights["defer_idle"])

        # calls gate+1 .. gate+cap-1: past gate but extra < cap -- tag present, escalation NOT fired
        # (this is the exact defect the architecture review caught: firing here would always
        # yield capped_extra=1 regardless of `cap`'s configured value)
        for i in range(gate, gate + cap - 1):
            assert "stasis_N" in recs[i].tags
            assert recs[i].delta == pytest.approx(scoring_weights["defer_idle"])

        # call gate+cap (streak == gate + cap): the one-shot fires here
        fire_index = gate + cap - 1
        assert "stasis_N" in recs[fire_index].tags
        expected_fire_delta = scoring_weights["defer_idle"] + scoring_weights["stasis_per_tick"] * cap
        assert recs[fire_index].delta == pytest.approx(expected_fire_delta)

        # all subsequent calls in the same streak: tag still present, escalation already fired
        for i in range(fire_index + 1, len(recs)):
            assert "stasis_N" in recs[i].tags
            assert recs[i].delta == pytest.approx(scoring_weights["defer_idle"])

    def test_population_stasis_fires_when_no_actions(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("stasis_gate_ticks")
        ctx = _ctx(tick=gate + 10, window_tags={"defer_idle": gate + 1, "action_taken": 0})
        rec = scorer.score(_env("defer_with_reason"), ctx)
        assert rec is not None
        assert "population_stasis" in rec.tags
        assert rec.delta == scoring_weights["population_stasis"]

    def test_population_stasis_fires_only_once(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("stasis_gate_ticks")
        ctx = _ctx(tick=gate + 10, window_tags={"defer_idle": gate + 1, "action_taken": 0})
        rec1 = scorer.score(_env("defer_with_reason"), ctx)
        rec2 = scorer.score(_env("defer_with_reason"), ctx)
        assert rec1 is not None and "population_stasis" in rec1.tags
        assert rec2 is None or "population_stasis" not in rec2.tags


class TestStasisBounding:
    @pytest.mark.parametrize("streak_length", [20, 2000])
    def test_stasis_one_shot_bounded_for_long_streak(
        self, scorer: AgencyScorer, scoring_weights: ScoringWeights, streak_length: int
    ) -> None:
        gate = scoring_weights.int_param("stasis_gate_ticks")
        cap = scoring_weights.int_param("stasis_extra_ticks_cap")
        entity_id = 99
        ctx = _ctx(tick=100, window_tags={"defer_idle": 0, "action_taken": 1})

        total_delta = 0.0
        for call_num in range(streak_length):
            rec = scorer.score(_env("defer_with_reason", tick=100 + call_num, entity_id=entity_id), ctx)
            assert rec is not None
            total_delta += rec.delta

        base_total = scoring_weights["defer_idle"] * streak_length
        escalation_contribution = total_delta - base_total
        expected_escalation = scoring_weights["stasis_per_tick"] * cap
        assert escalation_contribution == pytest.approx(expected_escalation)

    def test_streak_resets_on_non_defer_action(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("stasis_gate_ticks")
        cap = scoring_weights.int_param("stasis_extra_ticks_cap")
        entity_id = 7
        ctx = _ctx(tick=100, window_tags={"defer_idle": 0, "action_taken": 1})

        def run_streak_to_fire() -> None:
            fired = False
            for call_num in range(gate + cap):
                rec = scorer.score(_env("defer_with_reason", tick=100 + call_num, entity_id=entity_id), ctx)
                assert rec is not None
                expected_fire = scoring_weights["defer_idle"] + scoring_weights["stasis_per_tick"] * cap
                if rec.delta == pytest.approx(expected_fire):
                    fired = True
            assert fired, "expected the one-shot escalation to fire once within gate+cap calls"

        run_streak_to_fire()

        # non-defer action resets the streak for this entity
        reset_rec = scorer.score(_env("action_executed", entity_id=entity_id), ctx)
        assert reset_rec is not None

        # deferring past the gate again should fire the one-shot a second time
        run_streak_to_fire()

    def test_two_entities_streaks_independent(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("stasis_gate_ticks")
        cap = scoring_weights.int_param("stasis_extra_ticks_cap")
        entity_a = 101
        entity_b = 102
        ctx = _ctx(tick=100, window_tags={"defer_idle": 0, "action_taken": 1})
        expected_fire = scoring_weights["defer_idle"] + scoring_weights["stasis_per_tick"] * cap

        fired = {entity_a: False, entity_b: False}
        for call_num in range(gate + cap):
            rec_a = scorer.score(_env("defer_with_reason", tick=100 + call_num, entity_id=entity_a), ctx)
            rec_b = scorer.score(_env("defer_with_reason", tick=100 + call_num, entity_id=entity_b), ctx)
            assert rec_a is not None and rec_b is not None
            if rec_a.delta == pytest.approx(expected_fire):
                fired[entity_a] = True
            if rec_b.delta == pytest.approx(expected_fire):
                fired[entity_b] = True

        assert fired[entity_a]
        assert fired[entity_b]


class TestRejectionCascade:
    def test_normal_cascade(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("rejection_cascade_tick", payload={"count": 150}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["rejection_cascade"]
        assert "rejection_cascade" in rec.tags

    def test_sustained_cascade(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("rejection_cascade_tick", payload={"count": 600}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["rejection_cascade_sustained"]
        assert "rejection_cascade_sustained" in rec.tags

    def test_below_threshold_returns_none(self, scorer: AgencyScorer) -> None:
        rec = scorer.score(_env("rejection_cascade_tick", payload={"count": 50}), _ctx())
        assert rec is None


class TestNewEventTypes:
    def test_scorer_handles_defer_with_reason_event(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        """E-1: defer_with_reason → ScoreRecord with AGENCY pillar and negative delta (defer_idle weight)."""
        rec = scorer.score(_env("defer_with_reason"), _ctx(tick=100, window_tags={"defer_idle": 3, "action_taken": 1}))
        assert rec is not None
        assert rec.pillar == PillarId.AGENCY
        assert rec.delta == scoring_weights["defer_idle"]
        assert "defer_idle" in rec.tags

    def test_scorer_handles_commitment_abandoned_returns_none(self, scorer: AgencyScorer) -> None:
        """E-2: commitment_abandoned → None (scorer intentionally no-ops; contract must stay stable)."""
        rec = scorer.score(_env("commitment_abandoned", payload={"category": "voluntary_quit", "penalty": 0.2}), _ctx())
        assert rec is None

    def test_scorer_handles_rejection_cascade_tick_at_500(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        """E-3: rejection_cascade_tick count=501 → rejection_cascade_sustained ScoreRecord."""
        rec = scorer.score(_env("rejection_cascade_tick", payload={"count": 501}), _ctx())
        assert rec is not None
        assert "rejection_cascade_sustained" in rec.tags

    def test_scorer_handles_rejection_cascade_tick_at_100(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        """E-4: rejection_cascade_tick count=150 → rejection_cascade ScoreRecord."""
        rec = scorer.score(_env("rejection_cascade_tick", payload={"count": 150}), _ctx())
        assert rec is not None
        assert "rejection_cascade" in rec.tags

    def test_scorer_handles_route_family_first_use(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        """E-5: route_family_first_use → ScoreRecord with route_novelty and entropy_reward tags."""
        rec = scorer.score(_env("route_family_first_use", payload={"family": "recover", "entity_id": 1}), _ctx())
        assert rec is not None
        assert "route_novelty" in rec.tags
        assert "entropy_reward" in rec.tags


class TestProjectCycle:
    def test_cycle_fires_on_immediate_restart(self, scorer: AgencyScorer, scoring_weights: ScoringWeights) -> None:
        scorer.score(_env("project_abandoned", entity_id=5, payload={"project_type": "gather"}), _ctx())
        rec = scorer.score(_env("project_started", entity_id=5, payload={"project_type": "gather"}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["project_cycle"]
        assert "project_cycle" in rec.tags

    def test_no_cycle_for_different_project(self, scorer: AgencyScorer) -> None:
        scorer.score(_env("project_abandoned", entity_id=7, payload={"project_type": "gather"}), _ctx())
        rec = scorer.score(_env("project_started", entity_id=7, payload={"project_type": "craft"}), _ctx())
        assert rec is None

    def test_abandon_without_start_returns_none(self, scorer: AgencyScorer) -> None:
        rec = scorer.score(_env("project_abandoned", payload={"project_type": "gather"}), _ctx())
        assert rec is None
