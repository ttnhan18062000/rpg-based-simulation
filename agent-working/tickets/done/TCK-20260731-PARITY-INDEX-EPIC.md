---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260731-PARITY-INDEX-EPIC
phase: done
date: 2026-07-31
tags: [ai, process-improvement, testing]
---

# TCK-20260731-PARITY-INDEX-EPIC

## Title
Read-only SQLite parity-ledger index and context-read-path evidence epic

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Track the first, deliberately read-only delivery of the SQLite-backed parity-ledger
index proposed in `idea_parity_ledger_sqlite_context_integration.md`. The goal is a
rebuildable query surface that can later support concise context selection, without
changing the YAML ledger, existing workflow gates, or live context assembly.

## Scope
- Track and sequence the four child tickets in `tickets/todos/parity-ledger-sqlite-context/`.
- Limit this epic to Phase 0 (baseline and v1 decisions), Phase 1 (deterministic
  importer/index/health), Phase 2 (read-only impact equivalence), and Gate A (payoff review).
- Preserve YAML under `docs/parity_ledger/` as the Git-reviewed canonical source. The
  derived `parity-index/parity.db` is local, ignored, read-only, and rebuildable.
- Require all nine dynamically discovered YAML shards, including `faction.yaml`; do
  not silently inherit the legacy eight-shard selection.

## Out of Scope
- `parity-record`, any YAML mutation path, source-ledger normalization, or v3 schema changes.
- Context-packet integration, retrieval cache changes, workflow/hook changes, monitoring events,
  or agent guidance/skill changes.
- Retiring or altering `tools/parity_ledger_scan.py` or
  `tools/gate_checks/parity_updater_static.py`; they remain protected compatibility baselines.
- Semantic/vector/Graphify correctness dependencies, sqlite-vec, and any simulation-state change.

## Acceptance Criteria
- [x] Each child independently completes the standard ticket workflow and its stated safety checks.
- [x] The Phase 0–2 outputs prove a deterministic, all-shard, read-only index and document every
      intentional difference from the existing legacy tools.
- [x] Gate A records a reproducible GO, NO-GO, or INCONCLUSIVE decision before any later phase is scoped.
- [x] No child modifies source YAML bytes, changes legacy gate behavior, or enables a live consumer.

## Related Tickets
- TCK-20260731-PARITY-INDEX-BASELINE
- TCK-20260731-PARITY-INDEX-IMPORTER
- TCK-20260731-PARITY-IMPACT-PROOF
- TCK-20260731-PARITY-READPATH-GATE
- TCK-20260713-MONITORING-SQLITE-INDEX (derived-index precedent)
- TCK-20260705-GATE-DET-PARITY-UPDATER (legacy compatibility baseline)

## Related Docs
- docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md
- docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration_review_claude.md
- docs/parity_ledger/schema.json

## Related Stored Artifacts
None yet (scope-only epic).

## Related Code Areas
- docs/parity_ledger/
- tools/parity_ledger_scan.py
- tools/gate_checks/parity_updater_static.py
- tools/agent-monitoring/build_index.py

## Assumptions / Open Questions
- Phase 0 owns the v1 CLI/module location decision and records it before Phase 1 creates code.
- Later adoption remains contingent on Gate A; this epic does not authorize it.

## Implementation Notes
Scope-only epic. See `parity-ledger-sqlite-context/SEQUENCE.md` for dependency order.

## Test Summary
No direct tests apply to this scope-only epic.

## Files Changed
This ticket file and its child-ticket sequence only.

## Completion Summary
All four child tickets are complete: TCK-20260731-PARITY-INDEX-BASELINE (Phase 0 baseline manifest
and v1 decision record), TCK-20260731-PARITY-INDEX-IMPORTER (Phase 1 deterministic all-9-shard
SQLite importer/health index in `tools/parity_index.py`), TCK-20260731-PARITY-IMPACT-PROOF (Phase 2
read-only impact/entry/health query surface proved equivalent-or-better against legacy selection
behavior via a versioned fixture corpus), and TCK-20260731-PARITY-READPATH-GATE (Gate A payoff
review). Gate A reached an explicit **GO** verdict — recorded in
`docs/ai/parity_readpath_gate_a_decision.md` — showing 66.7% aggregate recall (14/21) for the
index's unmodified read path against real, git-pinned expected obligations, versus legacy's 4.8%
(1/21), with zero recall regression on any real case. The GO is narrowly scoped to future
ticket-*scoping* only (not implementation) and carries forward two documented limitations (a
`.claude/`-prefix blind spot and a single-shard-per-case scope limitation) for a future Phase-3
ticket to resolve. Throughout all four tickets, no `docs/parity_ledger/*.yaml` file, legacy gate
behavior, or live consumer/workflow/config/telemetry surface was modified — the entire epic
delivered a read-only, rebuildable, locally-ignored index exactly as scoped.

