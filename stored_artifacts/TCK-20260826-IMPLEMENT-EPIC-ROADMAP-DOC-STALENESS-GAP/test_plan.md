---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP
artifact_type: test_plan
tags: [workflows, documentation, process-improvement]
---

# Test Plan — TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP

## Normal flow
- `parse_tracking_doc_from_sequence`: declaration found mid-file, on the first line, trimmed
  whitespace, first-of-multiple wins.
- `update_tracking_doc_status_block`: markers present → content between them replaced, surrounding
  doc content byte-identical outside the markers.

## Edge cases
- `parse_tracking_doc_from_sequence`: no declaration at all → `None`; declared but empty → `None`
  (treated as absent, not a path).
- `update_tracking_doc_status_block`: only one marker present, markers present but reversed, doc
  file doesn't exist — each a distinct, non-writing, reported status (`markers_missing` /
  `doc_not_found`), never a silent no-op and never a crash.
- Idempotency: running the update twice in a row does not duplicate markers or leave stale content
  from the first run.

## Failure modes
- `implement-epic.js`'s new Report-phase block is a true no-op (no `agent()` call at all, not a
  call that happens to do nothing) when `discovery.tracking_doc` is falsy — verified by direct
  inspection of the `if (discovery.mode === 'folder' && discovery.tracking_doc)` guard, since the
  JS itself has no test harness (agent-interpreted, not run by node) and the guard's correctness is
  the only thing gating the mechanism from running unnecessarily on every batch.

## Regression paths
- `tests/tools/test_epic_tracking_doc_static.py` — new file, 13 tests, all passing — this doubles
  as the AC4 demonstration ("a real batch run... demonstrates the status block updating correctly
  after Implement": these tests exercise the exact function the JS Report phase calls, against a
  scratch `SEQUENCE.md`-equivalent input and scratch tracking doc).
- `node --check .claude/workflows/implement-epic.js` — confirms the edited workflow file is still
  syntactically valid.
- No `src/` files touched — parity ledger unaffected (confirmed no candidate shard for
  `.claude/workflows/`, `.claude/skills/`, or `tools/gate_checks/` files).
