---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260731-PARITY-INDEX-BASELINE
phase: open
date: 2026-07-31
tags: [ai, documentation, process-improvement, testing]
---

# TCK-20260731-PARITY-INDEX-BASELINE

## Title
Capture the parity-ledger baseline and decide v1 index boundaries

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Before implementing an index, create reproducible evidence for the current ledger and legacy tools, then make the v1 architecture decisions that later tickets must follow. The legacy tools hard-code eight shards and exclude `faction.yaml`; the baseline must expose rather than erase that distinction.

## Scope
- Produce a deterministic, versioned baseline manifest from dynamically enumerated `docs/parity_ledger/*.yaml`, including sorted files/content hashes, entries/IDs, status/priority counts, parser/schema coverage, and source/test-reference parse coverage.
- Capture fixed changed-path fixtures and exact outputs of `parity_ledger_scan.py` and `parity_updater_static.py`, including faction exclusion and malformed/unmapped/multi-shard behavior.
- Record v1 decisions for ownership, discovery/IDs, normalized schema, FTS fallback, atomic lifecycle, path-only links, output convention, and CLI/module ownership; `parity-record` stays deferred.

## Out of Scope
- Creating an index/database or changing `.gitignore`/Make targets.
- Changing YAML fields, legacy tools, context assembly, workflows, FTS/query commands, or a mutation CLI.

## Acceptance Criteria
- [ ] Unchanged source inputs yield byte-identical baseline output and all nine shards are represented; source hashes are unchanged.
- [ ] Manifest records the historical 1,936-entry snapshot and the legacy eight-shard/faction comparison gap.
- [ ] Fixture inputs and expected legacy outputs are versioned for faction, unmapped, and multi-shard cases.
- [ ] A v1 decision artifact resolves each Scope boundary including CLI ownership and FTS-independent fallback.
- [ ] No DB, workflow/config/context integration, source rewrite, or mutation command is introduced.

## Related Tickets
- TCK-20260731-PARITY-INDEX-EPIC
- TCK-20260731-PARITY-INDEX-IMPORTER
- TCK-20260705-GATE-DET-PARITY-UPDATER

## Related Docs
- docs/parity_ledger/schema.json
- docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/

## Related Code Areas
- docs/parity_ledger/
- tools/parity_ledger_scan.py
- tools/gate_checks/parity_updater_static.py
- tests/tools/test_parity_ledger_scan.py
- tests/tools/test_parity_updater_static.py

## Assumptions / Open Questions
- Historic schema-field gaps are classified for health/reporting later; this ticket must not coerce source status or repair source data.

## Implementation Notes
The legacy tools are compatibility fixtures only. They are not the desired all-shard v1 behavior.

## Test Summary

## Files Changed

## Completion Summary
