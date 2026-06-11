---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260609-ACTIVE-DATA-CONSUMER
phase: done
date: 2026-06-09
tags: [active, data, consumer]
---

# TCK-20260609-ACTIVE-DATA-CONSUMER

## Title
Add active-data consumer gate — prove active content has a consumer path

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The review warns of a "content graveyard" risk: records marked EXISTING-LOGIC, LEGACY-EXPORT, or REDESIGNED-CORE must have a proven consumer path (resolver output, compile context, runtime registry, runtime entity construction, world/module composition, or scenario setup). Records marked ADDITIONAL or FUTURE-EXTENSION may be inactive only if explicitly excluded from strict mode. This task adds data-driven tests using the reference graph from Phase 23 to enforce this rule automatically, with failures that name the specific family, ID, and missing consumer path.

## Scope
- Add data-driven consumer gate tests in `tests/integration/content/test_active_data_consumer.py`
- Use the content reference graph (from Phase 23) to enumerate active content records
- For records with state markers EXISTING-LOGIC, LEGACY-EXPORT, REDESIGNED-CORE: assert at least one consumer path exists in resolver output, compile context, runtime registry, entity construction, composition, or scenario setup
- For records with state markers ADDITIONAL, FUTURE-EXTENSION: allow inactive status if explicitly excluded from strict mode
- Failure messages must include: family, record ID, and which consumer paths are missing
- Test must be generic (not one test per data record)

## Out of Scope
- Adding consumer paths for currently-inactive content (this gate only detects the gap)
- Modifying content YAML files
- Duplicating strict world matrix tests (see TCK-20260609-STRICT-WORLD-MATRIX)

## Acceptance Criteria
- [ ] tests/integration/content/test_active_data_consumer.py exists
- [ ] Active unused content (EXISTING-LOGIC/LEGACY-EXPORT/REDESIGNED-CORE with no consumer) fails in strict mode
- [ ] ADDITIONAL/FUTURE-EXTENSION content can be skipped only with explicit state marker
- [ ] Compatibility content must project to legacy target or be marked inactive
- [ ] Failure messages include family, ID, and missing consumer path
- [ ] Test is data-driven, not one test per data record

## Related Tickets
- TCK-20260609-STRICT-WORLD-MATRIX (dependency — matrix results are used to assess consumer paths)

## Related Docs
- docs/mechanics/06_worldbuilding_foundation.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/integration/content/test_active_data_consumer.py (new)
- src/content/reference_graph.py
- graphify-out/ (reference graph output)

## Assumptions / Open Questions
- Phase 23 reference graph is available and up-to-date in graphify-out/
- State markers are parseable from content YAML files (STATE: field in YAML comments or metadata)

## Implementation Notes
- Sticky-state YAML comment parser handles both file-level and per-record STATE markers
- `attribute`, `element`, `perspective`, `projection` exempt (implicit runtime consumers)
- 11 pre-existing content graves in KNOWN_INACTIVE_CONTENT baseline; gate fires only on NEW violations
- `test_known_gaps_are_genuinely_inactive` guards against stale baseline entries

## Test Summary
5 passed. Gate correctly identifies 11 pre-existing gaps (in baseline); finds 0 new violations.

## Files Changed
- `tests/integration/content/test_active_data_consumer.py` (new)

## Completion Summary
Active-data consumer gate implemented. Detects content graves for EXISTING-LOGIC, LEGACY-EXPORT,
REDESIGNED-CORE records with no reference graph consumer. Pre-existing gaps documented in baseline;
gate will turn red on any new unconsumable active content.
