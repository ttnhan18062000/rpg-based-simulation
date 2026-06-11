---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260609-ACTIVE-DATA-CONSUMER
artifact_type: plan
tags: [active, data, consumer]
---


# Plan

## New file
`tests/integration/content/test_active_data_consumer.py`

## Key structures
- `FAMILIES_WITH_IMPLICIT_CONSUMERS`: exempt families from graph gate
- `KNOWN_INACTIVE_CONTENT`: baseline set of pre-existing gaps; gate fires only on NEW violations
- `scan_state_marked_records()`: scans YAML files → (short_family, record_id, state) tuples
- `_parse_state_markers_from_file()`: sticky-state line parser

## Test functions
1. `test_active_records_have_consumer_paths`: main gate — fails on NEW violations
2. `test_known_gaps_are_genuinely_inactive`: sanity — fires if a gap gains a consumer
3. `test_inactive_state_records_not_confused_with_active`: no overlap between active/inactive
4. `test_state_marked_records_are_parsed`: scanner sanity (>10 active records)
5. `test_implicit_consumer_families_are_scanned`: exemption sanity (perspective present)
