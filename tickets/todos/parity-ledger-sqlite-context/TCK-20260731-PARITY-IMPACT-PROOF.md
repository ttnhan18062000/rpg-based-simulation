---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260731-PARITY-IMPACT-PROOF
phase: open
date: 2026-07-31
tags: [ai, observability, process-improvement, testing]
---

# TCK-20260731-PARITY-IMPACT-PROOF

## Title
Prove deterministic parity-index impact queries against legacy selection behavior

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add the Phase 2 read-only API and prove its behavior against both existing parity-selection
tools. The proof must preserve their legacy semantics as named compatibility output while
explicitly demonstrating the new index's all-shard, faction-inclusive behavior.

## Scope
- Implement the Phase-0-selected CLI/API's `impact`, `entry`, and `health` read operations with
  stable machine-readable schemas, sorted results, selection reasons, and explicit unknown/no-match.
- Support exact path/test/constraint/entry queries from the normalized Phase 1 data. V1 links are
  path-level only; no symbol-coverage claim is permitted.
- Build a versioned equivalence fixture corpus using the Phase 0 baseline. Compare applicable
  results to `find_p0_intersection()` and `cross_reference_touched()` / derived mapping, label each
  intentional difference, and include a faction evidence case.
- Classify malformed/missing/legacy-unstructured inputs through health output without inventing a
  relationship or changing a source/legacy tool.

## Out of Scope
- Changing, retiring, or routing live workflow gates through the index.
- Context packets, retrieval cache/events, semantic search, mutation commands, or source YAML fixes.

## Acceptance Criteria
- [ ] `impact`, `entry`, and `health` return deterministic, documented machine-readable output;
      unknown paths are explicit no-match rather than an implicit success.
- [ ] The compatibility suite captures exact current legacy results where comparable and documents
      every difference, including P0-substring versus all-priority behavior, ANY-of multi-shard
      semantics, malformed-input treatment, and faction's legacy exclusion.
- [ ] All nine shards and their IDs can be represented; faction's source/test evidence appears in
      the new read path despite its zero-P0/legacy exclusion status.
- [ ] Legacy scanner/static-gate tests remain unchanged in behavior, and every synthetic fixture
      result plus an unchanged rebuild/query is reproducible.
- [ ] Health output reports uncertainty/missing links without modifying YAML or claiming symbol-level coverage.

## Related Tickets
- TCK-20260731-PARITY-INDEX-EPIC
- TCK-20260731-PARITY-INDEX-IMPORTER (dependency)
- TCK-20260731-PARITY-READPATH-GATE (successor)
- TCK-20260705-WORKFLOW-PARITY-SKIP
- TCK-20260705-GATE-DET-PARITY-UPDATER

## Related Docs
- docs/parity_ledger/schema.json
- docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/

## Related Code Areas
- tools/parity_ledger_scan.py
- tools/gate_checks/parity_updater_static.py
- tools/gate_checks/mechanics_auditor_static.py
- tests/tools/test_parity_ledger_scan.py
- tests/tools/test_parity_updater_static.py
- expected: tests/tools/test_parity_index.py

## Assumptions / Open Questions
- The public command spelling follows Phase 0's recorded ownership decision; this ticket owns
  query semantics, not a second CLI-placement decision.

## Implementation Notes
Legacy outputs are comparison evidence, not the target all-shard semantics.

## Test Summary

## Files Changed

## Completion Summary

