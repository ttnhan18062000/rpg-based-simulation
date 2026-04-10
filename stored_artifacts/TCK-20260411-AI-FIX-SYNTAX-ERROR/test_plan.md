# Test Plan: TCK-20260411-AI-FIX-SYNTAX-ERROR

## Regression Testing
- Run `pytest tests/unit/ai/test_stuck.py`

## Acceptance Criteria
- File is parsable by Python.
- `test_perception_tracks_position_history` passes.
- `test_appraisal_detects_stuck` passes.
