---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260411-AI-FIX-SYNTAX-ERROR
artifact_type: test_plan
tags: [ai, fix, syntax, error]
---

# Test Plan: TCK-20260411-AI-FIX-SYNTAX-ERROR

## Regression Testing
- Run `pytest tests/unit/ai/test_stuck.py`

## Acceptance Criteria
- File is parsable by Python.
- `test_perception_tracks_position_history` passes.
- `test_appraisal_detects_stuck` passes.
