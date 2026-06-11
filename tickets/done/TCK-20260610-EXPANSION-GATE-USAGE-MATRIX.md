---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260610-EXPANSION-GATE-USAGE-MATRIX
phase: done
date: 2026-06-10
tags: [expansion, gate, usage, matrix]
---

# TCK-20260610-EXPANSION-GATE-USAGE-MATRIX

## Title
Replace YAML comment scanner in expansion gate with ContentUsageMatrix shared helpers

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`test_expansion_gate.py` still scans `# STATE:` YAML comments to determine active content maturity, violating the Option A rule agreed earlier (YAML comments are human-only planning notes). It uses `_STATE_RE`, `_ACTIVE_STATES`, `_ID_RE`, and `_KNOWN_INACTIVE_CONTENT` inline. The expansion gate also duplicates logic from `test_active_data_consumer.py` with a comment saying they "must stay in sync." Both tests should use shared ContentUsageMatrix helpers and the stale CAT-REL-099 xfail docstring must be removed.

## Scope
- Remove `_STATE_RE`, `_ACTIVE_STATES`, `_ID_RE`, `_KNOWN_INACTIVE_CONTENT` from `test_expansion_gate.py`
- Remove the inline YAML comment scanner loop from gate item 04
- Replace gate item 04 with ContentUsageMatrix family coverage check
- Create `tests/helpers/content_usage_gate.py` with shared helpers used by both gate tests
- Update expansion gate docstring: remove stale CAT-REL-099 xfail language; document all gate items as hard pass
- Remove the "must stay in sync with test_active_data_consumer.py" comment

## Out of Scope
- Changing ContentUsageMatrix itself
- Changing `test_active_data_consumer.py` logic beyond adopting shared helpers
- Adding new gate items

## Acceptance Criteria
- [x] `test_expansion_gate.py` does not import `re` or `yaml` for comment scanning
- [x] No `_STATE_RE`, `_ACTIVE_STATES`, `_ID_RE`, `_KNOWN_INACTIVE_CONTENT` in expansion gate
- [x] Gate item 04 uses ContentUsageMatrix (not comment scan)
- [x] `tests/helpers/content_usage_gate.py` exists with shared helpers
- [x] Both `test_expansion_gate.py` and `test_active_data_consumer.py` call shared helpers
- [x] No "must stay in sync" comment remains
- [x] Expansion gate docstring: no stale CAT-REL-099 / xfail language; all items documented as hard pass
- [x] YAML `# STATE:` comments remain untouched (human-only notes)
- [x] All expansion gate tests still pass

## Related Tickets
- TCK-20260609-CONTENT-EXPANSION-GATE (prior work — created gate; this ticket repairs it)
- TCK-20260609-ACTIVE-DATA-CONSUMER (sister test — will use shared helpers)

## Related Docs
- `docs/testing/no_duplication_test_policy.md`
- `docs/mechanics/content_usage_matrix.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260610-EXPANSION-GATE-USAGE-MATRIX/`

## Related Code Areas
- `tests/integration/content/test_expansion_gate.py`
- `tests/integration/content/test_active_data_consumer.py`
- `tests/helpers/content_usage_gate.py` (new)

## Assumptions / Open Questions
- `tests/helpers/` already existed with `__init__.py`.
- `ContentReferenceGraph.nodes` is `Dict[str, Any]`; `is_record_used()` checks inbound edges.

## Implementation Notes
- Created `tests/helpers/content_usage_gate.py` exporting `ACTIVE_IMPL_STATES`, `GRAPH_EXEMPT_SHORTS`, `collect_family_graph_violations(ref_graph)`.
- Gate 04 signature changed from `(catalog, module_repo)` to `(ref_graph)` — now uses the module-scope fixture instead of building its own graph.
- `re` import removed; `yaml` import retained (needed for gates 08 and 12).
- `test_active_data_consumer.py` updated: local `_ACTIVE_IMPL_STATES` and `_GRAPH_EXEMPT_SHORTS` removed, imported from helper; `test_active_families_have_graph_coverage` now calls `collect_family_graph_violations`.
- Stale unused imports `FAMILY_TO_SHORT` and `Tuple` cleaned from both test files.

## Test Summary
`pytest tests/integration/content/test_expansion_gate.py tests/integration/content/test_active_data_consumer.py -v`
15/15 passed.

## Files Changed
- `tests/helpers/content_usage_gate.py` (new)
- `tests/integration/content/test_expansion_gate.py` (modified)
- `tests/integration/content/test_active_data_consumer.py` (modified)

## Completion Summary
YAML comment scanner removed from expansion gate. Gate item 04 now uses `collect_family_graph_violations` from the shared helper in `tests/helpers/content_usage_gate.py`. Both gate tests import from the helper — no sync drift is possible. All 15 gate tests pass.
