"""
tests/unit/core/test_cognition_write.py

TCK-20260914-COGNITION-BUNDLE-SET-WHOLE-OBJECT-REPLACE-HAZARD (Option 2)

Direct unit coverage for src/core/cognition_write.py::read_through_cognition(), the shared,
mandatory-by-guardrail (tests/architecture/test_cognition_bundle_set_read_through_guard.py) entry
point every real cognition_bundle_set writer routes through.
"""
from __future__ import annotations

from src.core.cognition import CognitionModel
from src.core.cognition_write import read_through_cognition
from src.core.updates import EntityUpdate


def test_returns_fallback_when_no_candidates_have_a_write():
    fallback = CognitionModel()
    assert read_through_cognition(fallback, None, None) is fallback


def test_returns_fallback_when_no_candidates_given():
    fallback = CognitionModel()
    assert read_through_cognition(fallback) is fallback


def test_returns_fallback_when_candidate_entity_update_has_no_cognition_write():
    fallback = CognitionModel()
    empty_update = EntityUpdate(entity_id=1)
    assert read_through_cognition(fallback, empty_update) is fallback


def test_returns_first_candidates_cognition_write_when_present():
    fallback = CognitionModel()
    staged = CognitionModel()
    update = EntityUpdate(entity_id=1, cognition_bundle_set=staged)
    assert read_through_cognition(fallback, update) is staged


def test_priority_order_prefers_earlier_candidate_over_later_one():
    """Matches CombatEngagementPhase's own two-accumulator lookup: this call's own
    already-staged write takes priority over an earlier pipeline phase's write."""
    fallback = CognitionModel()
    this_call_write = CognitionModel()
    earlier_phase_write = CognitionModel()

    this_call_update = EntityUpdate(entity_id=1, cognition_bundle_set=this_call_write)
    earlier_phase_update = EntityUpdate(entity_id=1, cognition_bundle_set=earlier_phase_write)

    result = read_through_cognition(fallback, this_call_update, earlier_phase_update)
    assert result is this_call_write


def test_falls_through_to_second_candidate_when_first_has_no_write():
    fallback = CognitionModel()
    earlier_phase_write = CognitionModel()

    this_call_update = EntityUpdate(entity_id=1)  # no cognition_bundle_set staged yet
    earlier_phase_update = EntityUpdate(entity_id=1, cognition_bundle_set=earlier_phase_write)

    result = read_through_cognition(fallback, this_call_update, earlier_phase_update)
    assert result is earlier_phase_write


def test_none_candidates_are_skipped_without_error():
    fallback = CognitionModel()
    staged = CognitionModel()
    update = EntityUpdate(entity_id=1, cognition_bundle_set=staged)

    assert read_through_cognition(fallback, None, update) is staged
