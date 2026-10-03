---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION
artifact_type: test_plan
tags: [architecture, schema, simulation-quality]
---

# Test Plan — TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION

## Normal flow
Each scan function (`scan_atlas`, `scan_capabilities`, `scan_wiring_map_labels`) correctly finds a
status phrase in its own artifact's real prose field and reports its location.

## Edge cases
- The atlas/capabilities' own `badges`/`tier`/`tierLabel` fields must never be scanned — proven
  directly (not just asserted) with a fixture whose title and badge both carry status vocabulary
  but whose `desc` does not, confirming zero hits.
- A missing/malformed JSON block returns an empty hit list rather than raising.

## Failure modes / regression-prone paths
- **Report-only guarantee** (AC #2): `main()` must exit 0 regardless of hit count — tested by
  running the real CLI against the real corpus (98 hits) and asserting return code 0, not just
  against an empty fixture.
- **The wiring-map cleanup regresses silently otherwise**: `test_wiring_map_entity_operating_loop_
  labels_are_clean` pins zero hits against the real, committed wiring map file, so a future status
  claim re-added to a node label (the same mistake this session made once already, adding one to
  `TRM` mid-session before catching and reverting it) is caught immediately rather than
  rediscovered.

## Coverage delivered
11 tests in `tests/unit/tools/test_mechanism_status_language_check.py`. Full `tests/unit/tools/`
suite: 229 passed (228 pre-existing + this file, after the sibling `trauma` self-correction's own
pinned-test fix in the same batch).
