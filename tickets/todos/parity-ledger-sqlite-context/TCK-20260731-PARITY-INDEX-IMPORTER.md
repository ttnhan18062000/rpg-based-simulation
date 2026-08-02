---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260731-PARITY-INDEX-IMPORTER
phase: open
date: 2026-07-31
tags: [ai, observability, process-improvement, testing]
---

# TCK-20260731-PARITY-INDEX-IMPORTER

## Title
Build the deterministic read-only parity-ledger SQLite importer and health index

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement the Phase 1 index following the Phase 0 architecture decision. It must load every
canonical YAML shard into a normalized, local SQLite database while preserving source bytes and
classifying—not silently correcting—historic or malformed evidence.

## Scope
- Implement the Phase-0-selected CLI/module shape and a deterministic full rebuild to local,
  Gitignored `parity-index/parity.db` (or the recorded equivalent output location).
- Dynamically import every YAML shard, populate normalized generation, entries, code/test/
  constraint/ticket reference, and ordered health data needed by later exact path-level queries.
- Store manifest/source hashes and importer/schema versions; stable ordering must be filename then
  stable entry ID. FTS5 is optional discovery only: probe it and provide exact ID/path lookup when
  unavailable.
- Build in a sibling temporary DB, validate integrity/schema/rows, close/fsync as appropriate,
  then atomically replace the old DB. A failed build must preserve the last good DB and YAML.
- Add on-demand build/ignore conventions selected in Phase 0 and isolated `tmp_path` tests.

## Out of Scope
- Any source YAML write, `parity-record`, v3 source format, context/retrieval/workflow integration,
  Graphify dependency, sqlite-vec, or `impact`/`entry` query API (Phase 2).
- Modifying the legacy scanner/static gate or treating their eight-shard list as importer input.

## Acceptance Criteria
- [ ] A rebuild imports all nine source shards (including faction), preserves YAML byte hashes, and
      exposes normalized rows sufficient for joins; no DB is committed.
- [ ] Identical inputs give the same logical generation and ordered tables/health findings;
      duplicate IDs, malformed sources, unparseable references, missing local refs/tests, and
      legacy-unstructured evidence are deterministic classified findings, never invented links.
- [ ] FTS5-present and forced-unavailable tests both pass; unavailable FTS reports disabled
      discovery while exact ID/path operations remain correct.
- [ ] An injected parse/validation/replacement failure leaves a prior good DB byte-identical and
      no usable partial DB; failed input never changes YAML.
- [ ] The old eight-shard legacy functions and their tests retain their behavior unchanged.

## Related Tickets
- TCK-20260731-PARITY-INDEX-EPIC
- TCK-20260731-PARITY-INDEX-BASELINE (dependency)
- TCK-20260731-PARITY-IMPACT-PROOF (successor)
- TCK-20260713-MONITORING-SQLITE-INDEX (lifecycle precedent, not a lifecycle template)

## Related Docs
- docs/parity_ledger/schema.json
- docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260713-MONITORING-SQLITE-INDEX/

## Related Code Areas
- docs/parity_ledger/
- tools/agent-monitoring/build_index.py
- tools/parity_ledger_scan.py
- tests/tools/test_build_index.py
- expected: tests/tools/test_parity_index.py

## Assumptions / Open Questions
- Phase 0's recorded CLI/module and fallback decisions are prerequisites; do not reopen them here
  except when an implementation contradiction requires an explicit follow-up.

## Implementation Notes
The monitoring index is useful read-only precedent, but its delete-before-build lifecycle must not
be copied: this ticket requires validated temporary build plus atomic replacement.

## Test Summary

## Files Changed

## Completion Summary

