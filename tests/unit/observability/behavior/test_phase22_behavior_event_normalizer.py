"""
Phase 22 — BehaviorEventNormalizer unit tests.

Tests verify:
- Each known event type maps to the correct behavior_category / behavior_family.
- source_event_ids links the raw event.
- Normalization does not mutate raw events.
- Unknown event categories produce no output (or deterministic output).
- Unknown event types within a known category are handled gracefully.
- Normalization is deterministic (same input → same output).
"""
from __future__ import annotations

import pytest

from src.observability.behavior.normalizer import BehaviorEventNormalizer
from src.observability.behavior.normalization_context import BehaviorNormalizationContext
from src.observability.events import (
    CombatDamageEvent,
    CombatKillEvent,
    GoldTransactionEvent,
    LifecycleEvent,
    MovementEvent,
    QuestEvent,
    SimulationEvent,
    ObservabilityEventEnvelope,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def normalizer() -> BehaviorEventNormalizer:
    return BehaviorEventNormalizer()


@pytest.fixture
def ctx() -> BehaviorNormalizationContext:
    return BehaviorNormalizationContext.minimal("run_test_001")


@pytest.fixture
def ctx_with_subject() -> BehaviorNormalizationContext:
    return BehaviorNormalizationContext(
        run_id="run_test_002",
        entity_subject_map={1: "Warrior", 2: "Mage"},
        route_family_map={1: "combat_route"},
    )


# ---------------------------------------------------------------------------
# Movement
# ---------------------------------------------------------------------------

class TestMovementNormalization:

    def test_movement_event_maps_to_movement_behavior(self, normalizer, ctx):
        """MovementEvent → movement/travel (roadmap spec)."""
        event = MovementEvent(
            event_id="evt_move_1",
            tick=5,
            entity_id=1,
            start_pos=(0.0, 0.0),
            end_pos=(1.0, 1.0),
            source_system="locomotion_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert len(results) == 1
        be = results[0]
        assert be.behavior_category == "movement"
        assert be.behavior_family == "travel"

    def test_movement_event_links_source_event_id(self, normalizer, ctx):
        event = MovementEvent(
            event_id="evt_move_abc",
            tick=3,
            entity_id=1,
            start_pos=(0.0, 0.0),
            end_pos=(2.0, 2.0),
            source_system="locomotion_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert "evt_move_abc" in results[0].source_event_ids

    def test_movement_event_does_not_mutate_raw(self, normalizer, ctx):
        event = MovementEvent(
            event_id="evt_move_2",
            tick=1,
            entity_id=1,
            start_pos=(0.0, 0.0),
            end_pos=(0.5, 0.5),
            source_system="locomotion_system",
        )
        original_type = event.event_type
        normalizer.normalize_event(event, ctx)
        assert event.event_type == original_type


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------

class TestCombatNormalization:

    def test_combat_damage_event_maps_to_combat_engage(self, normalizer, ctx):
        """CombatDamageEvent → combat/engage."""
        event = CombatDamageEvent(
            event_id="evt_dmg_1",
            tick=7,
            entity_id=2,
            attacker_id=3,
            damage=15,
            is_lethal=False,
            source_system="combat_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert len(results) == 1
        be = results[0]
        assert be.behavior_category == "combat"
        assert be.behavior_family == "engage"

    def test_combat_kill_event_maps_to_combat_behavior(self, normalizer, ctx):
        """CombatKillEvent → combat/kill_or_defeat."""
        event = CombatKillEvent(
            event_id="evt_kill_1",
            tick=8,
            entity_id=2,
            killer_id=3,
            source_system="combat_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert len(results) == 1
        be = results[0]
        assert be.behavior_category == "combat"
        assert be.behavior_family == "kill_or_defeat"

    def test_combat_damage_links_source_event_id(self, normalizer, ctx):
        event = CombatDamageEvent(
            event_id="evt_dmg_xyz",
            tick=7,
            entity_id=2,
            attacker_id=3,
            damage=5,
            is_lethal=False,
            source_system="combat_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert "evt_dmg_xyz" in results[0].source_event_ids

    def test_combat_event_maps_with_subject(self, normalizer, ctx_with_subject):
        """Subject label should be attached from context."""
        event = CombatDamageEvent(
            event_id="evt_dmg_s",
            tick=7,
            entity_id=1,
            attacker_id=2,
            damage=10,
            is_lethal=False,
            source_system="combat_system",
        )
        results = normalizer.normalize_event(event, ctx_with_subject)
        assert results[0].subject == "Warrior"
        assert results[0].route_family == "combat_route"


# ---------------------------------------------------------------------------
# Quest
# ---------------------------------------------------------------------------

class TestQuestNormalization:

    def test_quest_event_maps_to_quest_behavior(self, normalizer, ctx):
        """QuestEvent with status=progress → quest/progress."""
        event = QuestEvent(
            event_id="evt_quest_1",
            tick=12,
            entity_id=5,
            quest_id="q_001",
            status="progress",
            source_system="quest_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert len(results) == 1
        be = results[0]
        assert be.behavior_category == "quest"
        assert be.behavior_family == "progress"

    def test_quest_started_maps_to_accept(self, normalizer, ctx):
        event = QuestEvent(
            event_id="evt_quest_start",
            tick=1,
            entity_id=5,
            quest_id="q_001",
            status="started",
            source_system="quest_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert results[0].behavior_family == "accept"

    def test_quest_completed_maps_to_complete(self, normalizer, ctx):
        event = QuestEvent(
            event_id="evt_quest_done",
            tick=20,
            entity_id=5,
            quest_id="q_001",
            status="completed",
            source_system="quest_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert results[0].behavior_family == "complete"

    def test_quest_failed_maps_to_failure_response(self, normalizer, ctx):
        """QuestEvent with status=failed → failure_response/quest_failure."""
        event = QuestEvent(
            event_id="evt_quest_fail",
            tick=15,
            entity_id=5,
            quest_id="q_001",
            status="failed",
            source_system="quest_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert len(results) == 1
        be = results[0]
        assert be.behavior_category == "failure_response"
        assert be.behavior_family == "quest_failure"


# ---------------------------------------------------------------------------
# Trade / Economy
# ---------------------------------------------------------------------------

class TestTradeNormalization:

    def test_trade_event_maps_to_trade_behavior(self, normalizer, ctx):
        """GoldTransactionEvent → trade/buy_sell_or_reward."""
        event = GoldTransactionEvent(
            event_id="evt_gold_1",
            tick=3,
            entity_id=7,
            amount=100.0,
            transaction_kind="sell",
            source_system="economy_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert len(results) == 1
        be = results[0]
        assert be.behavior_category == "trade"
        assert be.behavior_family == "buy_sell_or_reward"


# ---------------------------------------------------------------------------
# Lifecycle / Progression
# ---------------------------------------------------------------------------

class TestLifecycleNormalization:

    def test_level_up_maps_to_progression(self, normalizer, ctx):
        event = LifecycleEvent(
            event_id="evt_lv_1",
            tick=50,
            entity_id=3,
            action="level_up",
            source_system="lifecycle_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert len(results) == 1
        be = results[0]
        assert be.behavior_category == "progression"
        assert be.behavior_family == "level_up"

    def test_spawn_maps_to_world_response(self, normalizer, ctx):
        event = LifecycleEvent(
            event_id="evt_spawn_1",
            tick=1,
            entity_id=3,
            action="spawn",
            source_system="lifecycle_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert len(results) == 1
        be = results[0]
        assert be.behavior_category == "world_response"
        assert be.behavior_family == "spawn"

    def test_despawn_maps_to_world_response(self, normalizer, ctx):
        event = LifecycleEvent(
            event_id="evt_despawn_1",
            tick=100,
            entity_id=3,
            action="despawn",
            source_system="lifecycle_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert results[0].behavior_category == "world_response"
        assert results[0].behavior_family == "despawn"

    def test_other_lifecycle_action_produces_no_output(self, normalizer, ctx):
        """Non-mapped lifecycle actions should be skipped (not produce noise)."""
        event = LifecycleEvent(
            event_id="evt_lc_age",
            tick=10,
            entity_id=3,
            action="age",
            source_system="lifecycle_system",
        )
        results = normalizer.normalize_event(event, ctx)
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Unknown / skipped categories
# ---------------------------------------------------------------------------

class TestUnknownEventPolicy:

    def test_unknown_event_policy_is_deterministic(self, normalizer, ctx):
        """
        Unknown event categories must produce an empty tuple deterministically.
        Same input must always produce same output.
        """
        unknown_event = SimulationEvent(
            event_id="evt_unknown_1",
            tick=1,
            event_type="some_unknown_type",
            event_category="anomaly",  # 'anomaly' not in category handlers
            severity="INFO",
            source_system="unknown_system",
            message="unknown event",
        )
        result_1 = normalizer.normalize_event(unknown_event, ctx)
        result_2 = normalizer.normalize_event(unknown_event, ctx)
        # Must be deterministic
        assert result_1 == result_2

    def test_event_without_category_returns_empty(self, normalizer, ctx):
        """Events with no event_category must be skipped."""
        envelope = ObservabilityEventEnvelope(
            event_id="evt_no_cat",
            run_id="run_x",
            tick=1,
            entity_id=None,
            event_type="mystery_event",
            event_category="",  # empty
            severity="INFO",
            source_system="test",
            message="no category",
        )
        results = normalizer.normalize_event(envelope, ctx)
        assert results == ()

    def test_normalize_batch_handles_mixed_events(self, normalizer, ctx):
        """Batch normalization should handle mix of known and unknown events."""
        events = [
            MovementEvent(
                event_id="evt_m_1",
                tick=1,
                entity_id=1,
                start_pos=(0.0, 0.0),
                end_pos=(1.0, 1.0),
                source_system="locomotion_system",
            ),
            SimulationEvent(
                event_id="evt_unknown_2",
                tick=2,
                event_type="unknown_event",
                event_category="anomaly",
                severity="INFO",
                source_system="sys",
                message="unknown",
            ),
            CombatKillEvent(
                event_id="evt_kill_batch",
                tick=3,
                entity_id=2,
                killer_id=3,
                source_system="combat_system",
            ),
        ]
        results = normalizer.normalize_batch(events, ctx)
        # Should produce 2 behavior events (1 movement, 1 combat; unknown skipped)
        assert len(results) == 2
        categories = {be.behavior_category for be in results}
        assert "movement" in categories
        assert "combat" in categories
