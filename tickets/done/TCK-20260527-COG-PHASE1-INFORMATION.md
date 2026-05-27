# TCK-20260527-COG-PHASE1-INFORMATION

## Title

Implement Phase 1 InformationProvider System

## Status

DONE

## Request Summary

Implement the structured InformationProvider system that allows entities to query knowledge sources (guide, guild, blacksmith) dynamically. Ensure that queries for secret materials (like moon_resin) return partial hints or rumor-based leads rather than full world truth, preventing omniscient global scanning.

## Scope

- Implement query/response dataclasses and provider classes under `src/world/providers/information.py`.
- Support Guide, Guild, and Blacksmith scoped information queries.
- Add comprehensive unit tests under `tests/unit/strategic/test_information.py`.

## Out of Scope

- Implementing the resource or service opportunity providers (Tasks 6 & 7).

## Acceptance Criteria

- Guide provider returns partial answers for secret resources like `moon_resin` directing them to `north_ruin`.
- Asking information can incur gold costs and yields structured leads.
- Unit tests under `tests/unit/strategic/test_information.py` pass.

## Related Tickets

- None

## Related Docs

- `entity_enhance_phase1.md` (Task 5)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/world/providers/information.py`
- `tests/unit/strategic/test_information.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- None

## Test Summary

- Information provider unit tests pass successfully: `pytest tests/unit/strategic/test_information.py`.

## Files Changed

- `tickets/inprogress/TCK-20260527-COG-PHASE1-INFORMATION.md`
- `src/world/providers/information.py`
- `tests/unit/strategic/test_information.py`

## Completion Summary

- Implemented state-free `GuideInformationProvider`, `BlacksmithInformationProvider`, and `GuildInformationProvider` under `src/world/providers/information.py`. Connected Guide queries to `ResourceRegistry` with custom logic for secret Phase 1 `moon_resin` resources returning partial `LeadState` clues targeting `north_ruin`. Added unit tests test_information.py validating cost checks and lead formatting. All tests pass successfully!
