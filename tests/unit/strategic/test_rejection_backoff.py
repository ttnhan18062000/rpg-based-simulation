"""
Unit tests for ProjectState rejection backoff — TCK-20260627-P1A-REJECTION-BACKOFF

Validates that evaluate_strategic_intent correctly increments project.failure_count
on consecutive intent rejections and abandons the project at _MAX_CONSECUTIVE_REJECTIONS.
STRAT-234 / docs/parity_ledger/strategic_cognition.yaml
"""
import pytest
from dataclasses import replace

from src.core.state import AuthoritativeState, IntentResult
from src.core.strategic import ProjectState, ProjectStatus, ProjectKind
from src.systems.strategic_systems.intelligence import (
    StrategicIntelligenceSystem,
    _MAX_CONSECUTIVE_REJECTIONS,
)
from src.core.updates import StrategicUpdate


def _make_entity(failure_count: int = 0, intent_results=None):
    """Build a minimal hero entity with an active project and configurable intent results."""
    from src.core.builder import V2EntityBuilder
    from src.core.state import IntentResult

    proj = ProjectState(
        id="proj_test",
        kind=ProjectKind.HARVESTING,
        status=ProjectStatus.ACTIVE,
        score=10.0,
        failure_count=failure_count,
    )

    entity = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(5.0, 5.0)
        .identity(class_id="hero")
        .combat(hp=100, max_hp=100, atk=10, def_stat=5, alive=True)
        .inventory(gold=0)
        .strategic(
            projects={"proj_test": proj},
            current_project_id="proj_test",
        )
        .build()
    )

    if intent_results is not None:
        from src.engine.apply import replace as fast_replace
        new_id = fast_replace(entity.identity, latest_intent_results=tuple(intent_results))
        entity = fast_replace(entity, identity=new_id)

    return entity


def _rejected_result():
    return IntentResult(
        transaction_id=None,
        accepted=False,
        reason="INTERACTION_RESET",
        source_kind="NODE",
        source_id=1,
    )


def _accepted_result():
    return IntentResult(
        transaction_id=None,
        accepted=True,
        reason=None,
        source_kind="NODE",
        source_id=1,
    )


def _make_state():
    return AuthoritativeState(tick=100, seed=42)


# ---------------------------------------------------------------------------
# Test 1: failure_count increments on all-rejected intents
# ---------------------------------------------------------------------------
class TestFailureCountIncrement:
    def test_increments_on_all_rejected(self):
        entity = _make_entity(failure_count=0, intent_results=[_rejected_result()])
        state = _make_state()
        upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
        # Should get back a project update with incremented failure_count
        proj_updates = [p for p in upd.projects_add_or_update if p.id == "proj_test"]
        assert proj_updates, "Expected a project update with incremented failure_count"
        assert proj_updates[0].failure_count == 1
        assert proj_updates[0].status == ProjectStatus.ACTIVE

    def test_increments_accumulate_across_calls(self):
        """Each call with all-rejected results should increment by 1."""
        entity = _make_entity(failure_count=5, intent_results=[_rejected_result()])
        state = _make_state()
        upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
        proj_updates = [p for p in upd.projects_add_or_update if p.id == "proj_test"]
        assert proj_updates, "Expected project update"
        assert proj_updates[0].failure_count == 6
        assert proj_updates[0].status == ProjectStatus.ACTIVE


# ---------------------------------------------------------------------------
# Test 2: project is abandoned at the threshold
# ---------------------------------------------------------------------------
class TestProjectAbandonmentAtThreshold:
    def test_abandons_at_max_consecutive_rejections(self):
        """At failure_count = N-1, one more rejection should trigger abandonment."""
        threshold = _MAX_CONSECUTIVE_REJECTIONS
        entity = _make_entity(
            failure_count=threshold - 1,
            intent_results=[_rejected_result()],
        )
        state = _make_state()
        upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)

        proj_updates = [p for p in upd.projects_add_or_update if p.id == "proj_test"]
        assert proj_updates, "Expected a project update"
        assert proj_updates[0].status == ProjectStatus.ABANDONED, (
            f"Expected ABANDONED, got {proj_updates[0].status}. "
            f"failure_count was {threshold - 1}, one rejection should trigger abandonment at {threshold}."
        )
        assert upd.current_project_id_set == ""

    def test_not_abandoned_one_below_threshold(self):
        """At failure_count = N-2, one rejection should NOT yet abandon."""
        threshold = _MAX_CONSECUTIVE_REJECTIONS
        entity = _make_entity(
            failure_count=threshold - 2,
            intent_results=[_rejected_result()],
        )
        state = _make_state()
        upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
        proj_updates = [p for p in upd.projects_add_or_update if p.id == "proj_test"]
        if proj_updates:
            assert proj_updates[0].status == ProjectStatus.ACTIVE


# ---------------------------------------------------------------------------
# Test 3: failure_count resets on accepted intent
# ---------------------------------------------------------------------------
class TestFailureCountReset:
    def test_resets_on_accepted_intent(self):
        entity = _make_entity(failure_count=10, intent_results=[_accepted_result()])
        state = _make_state()
        upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
        # If a project update is returned, failure_count must be 0
        proj_updates = [p for p in upd.projects_add_or_update if p.id == "proj_test"]
        if proj_updates:
            assert proj_updates[0].failure_count == 0, (
                f"Expected reset to 0, got {proj_updates[0].failure_count}"
            )


# ---------------------------------------------------------------------------
# Test 4: empty intent_results does not change failure_count
# ---------------------------------------------------------------------------
class TestNoChangeOnEmptyResults:
    def test_no_increment_when_no_intents(self):
        """Cadence skip / idle tick: empty results must not change failure_count."""
        entity = _make_entity(failure_count=5, intent_results=[])
        state = _make_state()
        upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
        proj_updates = [p for p in upd.projects_add_or_update if p.id == "proj_test"]
        # If the system returns a project update, the count should not have changed
        for pu in proj_updates:
            if pu.id == "proj_test":
                assert pu.failure_count == 5, (
                    "failure_count must not change when latest_intent_results is empty"
                )


# ---------------------------------------------------------------------------
# Test 5: boredom penalty is emitted on abandonment
# ---------------------------------------------------------------------------
class TestBoredomPenaltyOnAbandonment:
    def test_boredom_penalty_emitted(self):
        threshold = _MAX_CONSECUTIVE_REJECTIONS
        entity = _make_entity(
            failure_count=threshold - 1,
            intent_results=[_rejected_result()],
        )
        state = _make_state()
        upd = StrategicIntelligenceSystem.evaluate_strategic_intent(state, entity, force=True)
        proj_updates = [p for p in upd.projects_add_or_update if p.id == "proj_test"]
        assert proj_updates and proj_updates[0].status == ProjectStatus.ABANDONED
        # boredom_delta should have a non-zero entry for the project kind
        assert upd.boredom_delta, "Expected boredom_delta on abandonment"
        kind_key = proj_updates[0].kind
        assert upd.boredom_delta.get(kind_key, 0) > 0, (
            f"Expected positive boredom delta for {kind_key}, got {upd.boredom_delta}"
        )
