"""Consolidated time-gate penalty tests for all SimQ pillars.

Verifies that each time-gate rule in config/simulation_quality/detection_params.yaml:
  1. Fires the correct penalty at tick > threshold (not at tick <= threshold)
  2. Does NOT fire before the threshold
  3. Fires only once (one-shot flag pattern)

All tests inject events directly — no full engine run required.
Discoverable by: pytest tests/simulation_quality/ -k timegate

Threshold values are read from the session-scoped `scoring_weights` fixture so
tests stay in sync with config changes automatically.
"""
from __future__ import annotations
import uuid

import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.scorers.agency import AgencyScorer
from src.simulation_quality.scorers.economy import EconomyScorer
from src.simulation_quality.scorers.narrative import NarrativeScorer
from src.simulation_quality.scorers.progression import ProgressionScorer
from src.simulation_quality.weights import ScoringWeights


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _env(
    event_type: str,
    tick: int = 10,
    entity_id: int = 1,
    payload: dict | None = None,
    category: str = "test",
) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex,
        run_id="timegate-test",
        tick=tick,
        entity_id=entity_id,
        event_type=event_type,
        event_category=category,
        severity="INFO",
        source_system="test",
        message="",
        payload=payload or {},
    )


def _ctx(
    pillar: PillarId,
    tick: int = 10,
    window_tags: dict | None = None,
) -> ScoringContext:
    wt = window_tags or {}
    return ScoringContext(
        run_id="timegate-test",
        current_tick=tick,
        entity_count=10,
        pillar_scores={p: 0.0 for p in PillarId},
        pillar_event_counts={p: 0 for p in PillarId},
        window_tag_counts={p: (wt if p == pillar else {}) for p in PillarId},
    )


# ---------------------------------------------------------------------------
# ECONOMY time-gates
# ---------------------------------------------------------------------------

class TestEconomyTimegate:
    """Tests for EconomyScorer time-gate rules.

    Gates tested (from detection_params.yaml):
      zero_harvest_after_tick  = 100
      zero_crafting_after_tick = 200
      zero_trade_after_tick    = 300
    """

    @pytest.fixture
    def scorer(self, scoring_weights: ScoringWeights) -> EconomyScorer:
        return EconomyScorer(scoring_weights)

    # --- zero_harvest gate (threshold = 100) ---

    def test_zero_harvest_timegate_fires_at_threshold(
        self, scorer: EconomyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """zero_harvest penalty fires on first resource_harvested after tick > 100 with empty window."""
        gate = scoring_weights.int_param("zero_harvest_after_tick")
        rec = scorer.score(
            _env("resource_harvested", tick=gate + 1),
            _ctx(PillarId.ECONOMY, tick=gate + 1, window_tags={}),
        )
        assert rec is not None, "Expected ScoreRecord at threshold+1"
        assert "zero_harvest" in rec.tags
        assert rec.delta == scoring_weights["zero_harvest"]
        assert rec.delta < 0, "zero_harvest is a penalty — delta must be negative"

    def test_zero_harvest_timegate_not_before_threshold(
        self, scorer: EconomyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """zero_harvest penalty must NOT fire before tick 100 (positive harvest signal instead)."""
        gate = scoring_weights.int_param("zero_harvest_after_tick")
        rec = scorer.score(
            _env("resource_harvested", tick=gate - 1),
            _ctx(PillarId.ECONOMY, tick=gate - 1, window_tags={}),
        )
        assert rec is not None
        assert "zero_harvest" not in rec.tags
        assert "harvest_active" in rec.tags, "Before gate a harvest should score harvest_active"

    def test_zero_harvest_timegate_fires_once(
        self, scorer: EconomyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """zero_harvest penalty is a one-shot flag — second trigger returns positive signal."""
        gate = scoring_weights.int_param("zero_harvest_after_tick")
        ctx = _ctx(PillarId.ECONOMY, tick=gate + 1, window_tags={})
        rec1 = scorer.score(_env("resource_harvested", tick=gate + 1), ctx)
        assert rec1 is not None and "zero_harvest" in rec1.tags
        rec2 = scorer.score(_env("resource_harvested", tick=gate + 2), ctx)
        assert rec2 is not None
        assert "zero_harvest" not in rec2.tags, "Gate must fire only once"

    # --- zero_crafting gate (threshold = 200) ---

    def test_zero_crafting_timegate_fires_at_threshold(
        self, scorer: EconomyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """zero_crafting penalty fires on first item_crafted after tick > 200 with empty window."""
        gate = scoring_weights.int_param("zero_crafting_after_tick")
        rec = scorer.score(
            _env("item_crafted", tick=gate + 1),
            _ctx(PillarId.ECONOMY, tick=gate + 1, window_tags={}),
        )
        assert rec is not None
        assert "zero_crafting" in rec.tags
        assert rec.delta == scoring_weights["zero_crafting"]
        assert rec.delta < 0

    def test_zero_crafting_timegate_not_before_threshold(
        self, scorer: EconomyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """zero_crafting penalty must NOT fire before tick 200."""
        gate = scoring_weights.int_param("zero_crafting_after_tick")
        rec = scorer.score(
            _env("item_crafted", tick=gate - 1),
            _ctx(PillarId.ECONOMY, tick=gate - 1, window_tags={}),
        )
        assert rec is not None
        assert "zero_crafting" not in rec.tags
        assert "crafting_active" in rec.tags

    def test_zero_crafting_timegate_fires_once(
        self, scorer: EconomyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """zero_crafting is a one-shot flag."""
        gate = scoring_weights.int_param("zero_crafting_after_tick")
        ctx = _ctx(PillarId.ECONOMY, tick=gate + 1, window_tags={})
        rec1 = scorer.score(_env("item_crafted", tick=gate + 1), ctx)
        assert rec1 is not None and "zero_crafting" in rec1.tags
        rec2 = scorer.score(_env("item_crafted", tick=gate + 5), ctx)
        assert rec2 is not None
        assert "zero_crafting" not in rec2.tags

    # --- zero_trade gate (threshold = 300) ---

    def test_zero_trade_timegate_fires_at_threshold(
        self, scorer: EconomyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """zero_trade penalty fires on first trade_executed after tick > 300 with empty window."""
        gate = scoring_weights.int_param("zero_trade_after_tick")
        rec = scorer.score(
            _env("trade_executed", tick=gate + 1),
            _ctx(PillarId.ECONOMY, tick=gate + 1, window_tags={}),
        )
        assert rec is not None
        assert "zero_trade" in rec.tags
        assert rec.delta == scoring_weights["zero_trade"]
        assert rec.delta < 0

    def test_zero_trade_timegate_not_before_threshold(
        self, scorer: EconomyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """zero_trade penalty must NOT fire before tick 300."""
        gate = scoring_weights.int_param("zero_trade_after_tick")
        rec = scorer.score(
            _env("trade_executed", tick=gate - 1),
            _ctx(PillarId.ECONOMY, tick=gate - 1, window_tags={}),
        )
        assert rec is not None
        assert "zero_trade" not in rec.tags
        assert "trade_active" in rec.tags

    def test_zero_trade_timegate_fires_once(
        self, scorer: EconomyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """zero_trade is a one-shot flag."""
        gate = scoring_weights.int_param("zero_trade_after_tick")
        ctx = _ctx(PillarId.ECONOMY, tick=gate + 1, window_tags={})
        rec1 = scorer.score(_env("trade_executed", tick=gate + 1), ctx)
        assert rec1 is not None and "zero_trade" in rec1.tags
        rec2 = scorer.score(_env("trade_executed", tick=gate + 5), ctx)
        assert rec2 is not None
        assert "zero_trade" not in rec2.tags


# ---------------------------------------------------------------------------
# PROGRESSION time-gates
# ---------------------------------------------------------------------------

class TestProgressionTimegate:
    """Tests for ProgressionScorer time-gate rules.

    Gates tested (from detection_params.yaml):
      progression_frozen_by_tick = 200  (used for all_level_1 check)
      xp_plateau_by_tick         = 50   (used for xp_rate_zero check)

    progression_frozen tag fires on progression_plateau_detected (type=xp_freeze)
    with no tick check in the scorer — detection is engine-side via 200-tick window.
    """

    @pytest.fixture
    def scorer(self, scoring_weights: ScoringWeights) -> ProgressionScorer:
        return ProgressionScorer(scoring_weights)

    # --- all_level_1 gate (progression_frozen_by_tick = 200) ---

    def test_all_level_1_timegate_fires_at_threshold(
        self, scorer: ProgressionScorer, scoring_weights: ScoringWeights
    ) -> None:
        """all_level_1 penalty fires on first level_up after tick > 200 with no level milestones."""
        gate = scoring_weights.int_param("progression_frozen_by_tick")
        rec = scorer.score(
            _env("level_up", tick=gate + 1),
            _ctx(PillarId.PROGRESSION, tick=gate + 1, window_tags={}),
        )
        assert rec is not None
        assert "all_level_1" in rec.tags
        assert rec.delta == scoring_weights["all_level_1"]
        assert rec.delta < 0

    def test_all_level_1_timegate_not_before_threshold(
        self, scorer: ProgressionScorer, scoring_weights: ScoringWeights
    ) -> None:
        """all_level_1 must NOT fire before tick 200 — scores positive level_milestone instead."""
        gate = scoring_weights.int_param("progression_frozen_by_tick")
        rec = scorer.score(
            _env("level_up", tick=gate - 1),
            _ctx(PillarId.PROGRESSION, tick=gate - 1, window_tags={}),
        )
        assert rec is not None
        assert "all_level_1" not in rec.tags
        assert "level_milestone" in rec.tags

    def test_all_level_1_timegate_fires_once(
        self, scorer: ProgressionScorer, scoring_weights: ScoringWeights
    ) -> None:
        """all_level_1 is a one-shot flag."""
        gate = scoring_weights.int_param("progression_frozen_by_tick")
        ctx = _ctx(PillarId.PROGRESSION, tick=gate + 1, window_tags={})
        rec1 = scorer.score(_env("level_up", tick=gate + 1), ctx)
        assert rec1 is not None and "all_level_1" in rec1.tags
        rec2 = scorer.score(_env("level_up", tick=gate + 5), ctx)
        assert rec2 is not None
        assert "all_level_1" not in rec2.tags

    # --- progression_frozen (no tick check in scorer — fires via payload type) ---

    def test_progression_frozen_fires_on_xp_freeze_payload(
        self, scorer: ProgressionScorer, scoring_weights: ScoringWeights
    ) -> None:
        """progression_frozen fires on progression_plateau_detected with type=xp_freeze.

        No tick gate in the scorer itself; the engine emits this event only after
        detecting a 200-tick window with zero XP gain. We verify the scorer receives
        and correctly applies the penalty regardless of tick.
        """
        rec = scorer.score(
            _env("progression_plateau_detected", tick=10, payload={"type": "xp_freeze"}),
            _ctx(PillarId.PROGRESSION, tick=10),
        )
        assert rec is not None
        assert "progression_frozen" in rec.tags
        assert rec.delta == scoring_weights["progression_frozen"]
        assert rec.delta < 0

    # --- xp_plateau gate (xp_plateau_by_tick = 50) ---

    def test_xp_plateau_timegate_fires_at_threshold(
        self, scorer: ProgressionScorer, scoring_weights: ScoringWeights
    ) -> None:
        """xp_plateau fires on progression_plateau_detected (type=xp_rate_zero) after tick > 50."""
        gate = scoring_weights.int_param("xp_plateau_by_tick")
        rec = scorer.score(
            _env("progression_plateau_detected", tick=gate + 1, payload={"type": "xp_rate_zero"}),
            _ctx(PillarId.PROGRESSION, tick=gate + 1),
        )
        assert rec is not None
        assert "xp_plateau" in rec.tags
        assert rec.delta == scoring_weights["xp_plateau"]

    def test_xp_plateau_timegate_not_before_threshold(
        self, scorer: ProgressionScorer, scoring_weights: ScoringWeights
    ) -> None:
        """xp_plateau must NOT fire before tick 50 — returns None (gate not met)."""
        gate = scoring_weights.int_param("xp_plateau_by_tick")
        rec = scorer.score(
            _env("progression_plateau_detected", tick=gate - 1, payload={"type": "xp_rate_zero"}),
            _ctx(PillarId.PROGRESSION, tick=gate - 1),
        )
        # Before gate: xp_rate_zero doesn't match any other branch — should return None
        assert rec is None, "xp_plateau must not fire before the tick gate"


# ---------------------------------------------------------------------------
# NARRATIVE time-gates
# ---------------------------------------------------------------------------

class TestNarrativeTimegate:
    """Tests for NarrativeScorer time-gate rules.

    Gates tested (from detection_params.yaml):
      zero_quests_after_tick    = 200
      zero_chronicle_after_tick = 300
    """

    @pytest.fixture
    def scorer(self, scoring_weights: ScoringWeights) -> NarrativeScorer:
        return NarrativeScorer(scoring_weights)

    # --- quest_system_dormant gate (zero_quests_after_tick = 200) ---

    def test_quest_dormant_timegate_fires_at_threshold(
        self, scorer: NarrativeScorer, scoring_weights: ScoringWeights
    ) -> None:
        """quest_system_dormant fires on first quest_started after tick > 200 with empty window."""
        gate = scoring_weights.int_param("zero_quests_after_tick")
        rec = scorer.score(
            _env("quest_started", tick=gate + 1),
            _ctx(PillarId.NARRATIVE, tick=gate + 1, window_tags={}),
        )
        assert rec is not None
        assert "quest_system_dormant" in rec.tags
        assert rec.delta == scoring_weights["quest_system_dormant"]
        assert rec.delta < 0

    def test_quest_dormant_timegate_not_before_threshold(
        self, scorer: NarrativeScorer, scoring_weights: ScoringWeights
    ) -> None:
        """quest_system_dormant must NOT fire before tick 200 — positive quest_active instead."""
        gate = scoring_weights.int_param("zero_quests_after_tick")
        rec = scorer.score(
            _env("quest_started", tick=gate - 1),
            _ctx(PillarId.NARRATIVE, tick=gate - 1, window_tags={}),
        )
        assert rec is not None
        assert "quest_system_dormant" not in rec.tags
        assert "quest_active" in rec.tags

    def test_quest_dormant_timegate_fires_once(
        self, scorer: NarrativeScorer, scoring_weights: ScoringWeights
    ) -> None:
        """quest_system_dormant is a one-shot flag."""
        gate = scoring_weights.int_param("zero_quests_after_tick")
        ctx = _ctx(PillarId.NARRATIVE, tick=gate + 1, window_tags={})
        rec1 = scorer.score(_env("quest_started", tick=gate + 1), ctx)
        assert rec1 is not None and "quest_system_dormant" in rec1.tags
        rec2 = scorer.score(_env("quest_started", tick=gate + 5), ctx)
        assert rec2 is not None
        assert "quest_system_dormant" not in rec2.tags

    # --- history_silent gate (zero_chronicle_after_tick = 300) ---

    def test_chronicle_silent_timegate_fires_at_threshold(
        self, scorer: NarrativeScorer, scoring_weights: ScoringWeights
    ) -> None:
        """history_silent fires on first chronicle_entry_created after tick > 300 with empty window."""
        gate = scoring_weights.int_param("zero_chronicle_after_tick")
        rec = scorer.score(
            _env("chronicle_entry_created", tick=gate + 1),
            _ctx(PillarId.NARRATIVE, tick=gate + 1, window_tags={}),
        )
        assert rec is not None
        assert "history_silent" in rec.tags
        assert rec.delta == scoring_weights["history_silent"]
        assert rec.delta < 0

    def test_chronicle_silent_timegate_not_before_threshold(
        self, scorer: NarrativeScorer, scoring_weights: ScoringWeights
    ) -> None:
        """history_silent must NOT fire before tick 300 — positive history_forming instead."""
        gate = scoring_weights.int_param("zero_chronicle_after_tick")
        rec = scorer.score(
            _env("chronicle_entry_created", tick=gate - 1),
            _ctx(PillarId.NARRATIVE, tick=gate - 1, window_tags={}),
        )
        assert rec is not None
        assert "history_silent" not in rec.tags
        assert "history_forming" in rec.tags

    def test_chronicle_silent_timegate_fires_once(
        self, scorer: NarrativeScorer, scoring_weights: ScoringWeights
    ) -> None:
        """history_silent is a one-shot flag."""
        gate = scoring_weights.int_param("zero_chronicle_after_tick")
        ctx = _ctx(PillarId.NARRATIVE, tick=gate + 1, window_tags={})
        rec1 = scorer.score(_env("chronicle_entry_created", tick=gate + 1), ctx)
        assert rec1 is not None and "history_silent" in rec1.tags
        rec2 = scorer.score(_env("chronicle_entry_created", tick=gate + 5), ctx)
        assert rec2 is not None
        assert "history_silent" not in rec2.tags


# ---------------------------------------------------------------------------
# AGENCY time-gates
# ---------------------------------------------------------------------------

class TestAgencyTimegate:
    """Tests for AgencyScorer time-gate rules.

    Gates tested (from detection_params.yaml):
      stasis_gate_ticks = 5

    stasis_N: per-defer-event accumulation once defer_idle count > stasis_gate_ticks
    population_stasis: one-shot when tick > stasis_gate AND action_taken == 0 in window
    """

    @pytest.fixture
    def scorer(self, scoring_weights: ScoringWeights) -> AgencyScorer:
        return AgencyScorer(scoring_weights)

    # --- stasis_N accumulation (stasis_gate_ticks = 5) ---

    def test_stasis_N_timegate_fires_after_gate(
        self, scorer: AgencyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """stasis_N tag appears once the per-entity streak exceeds stasis_gate_ticks, and the
        one-shot escalation delta fires only when the streak reaches gate + cap (not at the
        first post-gate call)."""
        gate = scoring_weights.int_param("stasis_gate_ticks")
        cap = scoring_weights.int_param("stasis_extra_ticks_cap")
        entity_id = 55
        ctx = _ctx(PillarId.AGENCY, tick=100, window_tags={"defer_idle": 0, "action_taken": 1})

        recs = [
            scorer.score(_env("defer_with_reason", tick=100 + i, entity_id=entity_id), ctx)
            for i in range(gate + cap)
        ]
        assert all(rec is not None for rec in recs)
        # first post-gate call (index == gate) already carries the stasis_N tag
        assert "stasis_N" in recs[gate].tags, "stasis_N tag must be present once streak exceeds gate"
        # but the escalation delta only fires at streak == gate + cap (the last call here)
        expected_fire = scoring_weights["defer_idle"] + scoring_weights["stasis_per_tick"] * cap
        assert recs[-1].delta == pytest.approx(expected_fire)
        assert recs[gate].delta == pytest.approx(scoring_weights["defer_idle"]), (
            "escalation must NOT fire at the first post-gate call (streak = gate+1)"
        )

    def test_stasis_N_timegate_not_before_gate(
        self, scorer: AgencyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """stasis_N must NOT appear while the per-entity streak is at or below stasis_gate_ticks."""
        gate = scoring_weights.int_param("stasis_gate_ticks")
        entity_id = 56
        ctx = _ctx(PillarId.AGENCY, tick=100, window_tags={"defer_idle": 0, "action_taken": 1})

        for i in range(gate):
            rec = scorer.score(_env("defer_with_reason", tick=100 + i, entity_id=entity_id), ctx)
            assert rec is not None
            assert "stasis_N" not in rec.tags, "stasis_N must not fire before streak exceeds gate"

    def test_stasis_N_timegate_bounded_one_shot(
        self, scorer: AgencyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """stasis_N's score contribution is a one-shot capped escalation, not unbounded linear
        accumulation: the cumulative escalation contribution over a long streak stays fixed at
        stasis_per_tick * stasis_extra_ticks_cap, regardless of streak length."""
        gate = scoring_weights.int_param("stasis_gate_ticks")
        cap = scoring_weights.int_param("stasis_extra_ticks_cap")
        entity_id = 57
        ctx = _ctx(PillarId.AGENCY, tick=100, window_tags={"defer_idle": 0, "action_taken": 1})

        streak_length = gate + cap + 50
        total_delta = 0.0
        for i in range(streak_length):
            rec = scorer.score(_env("defer_with_reason", tick=100 + i, entity_id=entity_id), ctx)
            assert rec is not None
            total_delta += rec.delta

        base_total = scoring_weights["defer_idle"] * streak_length
        escalation_contribution = total_delta - base_total
        expected_escalation = scoring_weights["stasis_per_tick"] * cap
        assert escalation_contribution == pytest.approx(expected_escalation), (
            f"Expected fixed one-shot escalation of {expected_escalation}, got "
            f"{escalation_contribution}. stasis_N must not accumulate linearly with streak length."
        )

    # --- population_stasis one-shot (tick > stasis_gate AND action_taken == 0) ---

    def test_population_stasis_timegate_fires_at_gate(
        self, scorer: AgencyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """population_stasis fires when tick > stasis_gate and action_taken == 0 in window."""
        gate = scoring_weights.int_param("stasis_gate_ticks")
        ctx = _ctx(
            PillarId.AGENCY,
            tick=gate + 1,
            window_tags={"defer_idle": gate + 1, "action_taken": 0},
        )
        rec = scorer.score(_env("defer_with_reason", tick=gate + 1), ctx)
        assert rec is not None
        assert "population_stasis" in rec.tags
        assert rec.delta == scoring_weights["population_stasis"]
        assert rec.delta < 0

    def test_population_stasis_timegate_not_before_gate(
        self, scorer: AgencyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """population_stasis must NOT fire when tick <= stasis_gate."""
        gate = scoring_weights.int_param("stasis_gate_ticks")
        # Use tick=gate (not > gate, so condition fails)
        ctx = _ctx(
            PillarId.AGENCY,
            tick=gate,
            window_tags={"defer_idle": gate, "action_taken": 0},
        )
        rec = scorer.score(_env("defer_with_reason", tick=gate), ctx)
        assert rec is not None
        assert "population_stasis" not in rec.tags, (
            "population_stasis must not fire at tick==gate (condition is tick > gate)"
        )

    def test_population_stasis_timegate_fires_once(
        self, scorer: AgencyScorer, scoring_weights: ScoringWeights
    ) -> None:
        """population_stasis is a one-shot flag — second trigger does not re-fire."""
        gate = scoring_weights.int_param("stasis_gate_ticks")
        ctx = _ctx(
            PillarId.AGENCY,
            tick=gate + 10,
            window_tags={"defer_idle": gate + 1, "action_taken": 0},
        )
        rec1 = scorer.score(_env("defer_with_reason", tick=gate + 1), ctx)
        assert rec1 is not None and "population_stasis" in rec1.tags
        rec2 = scorer.score(_env("defer_with_reason", tick=gate + 2), ctx)
        # Second call: population_stasis already fired; scorer returns defer_idle base or stasis_N
        assert rec2 is None or "population_stasis" not in rec2.tags, (
            "population_stasis must fire only once"
        )
