# TCK-20260411-AI-FIX-SYNTAX-ERROR

## Title

Fix syntax error in `test_stuck.py`

## Status

DONE

## Request Summary

Fix Parse error: Invalid assignment target in `tests/unit/ai/test_stuck.py:L29` and subsequent ValidationError.

## Scope

- Remove lines 29 and 30 in `tests/unit/ai/test_stuck.py` which contain invalid assignment targets `{}`.

## Out of Scope

- Any other logic changes in `AIBrain` or tests.

## Acceptance Criteria

- `tests/unit/ai/test_stuck.py` passes.
- No syntax errors in the file.

## Related Tickets

- None

## Related Docs

- None

## Related Stored Artifacts

- None

## Related Code Areas

- `tests/unit/ai/test_stuck.py`

## Assumptions / Open Questions

- Assumed these lines were accidental corruptions or leftovers from a previous edit.

## Implementation Notes

- Simple removal of two lines.

## Test Summary

- Run `pytest tests/unit/ai/test_stuck.py`

## Files Changed

- `tests/unit/ai/test_stuck.py`

## Completion Summary

- Removed corrupted logic `{} = {}` from `test_stuck.py`.
- Identified and fixed missing mocks for `known_bonds` and `faction_standing` to satisfy Pydantic validation in `SocialStance`.
- Verified that all unit tests in `test_stuck.py` pass.
