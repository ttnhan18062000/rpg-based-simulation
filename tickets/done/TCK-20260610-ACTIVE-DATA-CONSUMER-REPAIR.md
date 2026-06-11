---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260610-ACTIVE-DATA-CONSUMER-REPAIR
phase: done
date: 2026-06-10
tags: [active, data, consumer, repair]
---

# TCK-20260610-ACTIVE-DATA-CONSUMER-REPAIR

## Title
Replace YAML STATE-comment scanning in test_active_data_consumer.py with ContentUsageMatrix family-level validation

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`tests/integration/content/test_active_data_consumer.py` validates per-record content maturity by scanning YAML `# STATE:` comments, violating Option A. Replaced with family-level ContentUsageMatrix validation.

## Scope
- Remove or fully replace the YAML STATE-comment scanning logic in `test_active_data_consumer.py`
- Implement family-level validation using `ContentUsageMatrix`
- The replacement test must not depend on any YAML comment fields

## Out of Scope
- Removing STATE comments from YAML files
- Changes to ContentUsageMatrix schema
- Any change to currently passing tests unrelated to this file

## Acceptance Criteria
- [x] `test_active_data_consumer.py` contains no code that reads or parses YAML `# STATE:` comments
- [x] Replacement tests assert active content families have registered consumer paths via ContentUsageMatrix
- [x] All 3 replacement tests pass (no xfail)
- [x] STATE comments remain in YAML files as non-normative; ContentFamilyMatrixEntry docstring already states the policy
- [x] No regression in related content/catalog tests (expansion gate gate_04 confirmed passing)

## Related Tickets
- TCK-20260610-CAT-REL-099-FIX (independent; worked in parallel)

## Related Docs
- Phase 20–28 repair decision: Option A — "YAML comments are human planning notes only"
- `src/content/matrix.py` — POLICY NOTE already embedded in ContentFamilyMatrixEntry docstring

## Related Stored Artifacts
- `stored_artifacts/TCK-20260609-CONTENT-EXPANSION-GATE/`

## Related Code Areas
- `tests/integration/content/test_active_data_consumer.py`
- `src/content/matrix.py`

## Assumptions / Open Questions
ContentUsageMatrix already had `implementation_state` as the authoritative family-level status. No new API needed. STATE comments in YAML remain as human planning notes — the `ContentFamilyMatrixEntry` docstring already embeds the Option A policy statement.

## Implementation Notes
Rewrote `test_active_data_consumer.py` from scratch. Removed all STATE-comment scanning:
- `_parse_state_markers_from_file()`, `scan_state_marked_records()`, `ACTIVE_STATES`, `INACTIVE_STATES` constants, `state_marked_records` fixture and 5 comment-driven tests.

Replaced with 3 ContentUsageMatrix-driven tests:
1. `test_active_families_have_documented_consumers` — each family with `RESOLVED_PARTIALLY` or `RUNTIME_AUTHORITATIVE` state has `resolver_component` or `compile_runtime_consumer` set
2. `test_active_families_have_graph_coverage` — each such family has ≥1 record with an incoming reference graph edge (exempting implicit-consumer families and graph entry points)
3. `test_content_usage_matrix_covers_active_catalog_families` — all CANONICAL_FAMILIES file_paths appear in ContentUsageMatrix

Key implementation notes:
- ContentUsageMatrix keys use `/` separators; FAMILY_TO_SHORT uses `.` — converted with `replace("/",".")`
- ContentUsageMatrix key for `world.regions` canonical family is `world/runtime_regions` — matched by file_path, not key
- `defaults` is a graph entry point with no inbound edges by design; exempted from graph coverage check

## Test Summary
- `tests/integration/content/test_active_data_consumer.py`: 3/3 passed
- `tests/integration/content/test_expansion_gate.py::test_gate_04_no_new_dead_active_data`: PASSED

## Files Changed
- `tests/integration/content/test_active_data_consumer.py` — full rewrite

## Completion Summary
Replaced YAML STATE-comment scanning with ContentUsageMatrix family-level validation. All 3 new tests pass. Option A compliance restored: no test or tooling reads YAML comment markers for validation.
