---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260721-BASELINE-MONITORING-MANIFEST
phase: open
date: 2026-07-21
tags: []
---

# TCK-20260721-BASELINE-MONITORING-MANIFEST

## Title
Baseline monitoring manifest and legacy compatibility fixtures

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Before touching any monitoring writer or reader, capture a read-only baseline inventory of every agent-monitoring JSONL file (counts, byte sizes, SHA-256 hashes, parser/validator results, legacy-warning counts) and build a fixture corpus covering every known historical schema generation, so later migrations can prove nothing was rewritten, reordered, or lost. This matters because the epic's Phase 0 exit criteria requires a reproducible baseline manifest and passing legacy parser fixtures before any writer or .codex/ hook is touched, and the existing agent-monitoring/*.jsonl corpus is immutable historical input that must never be rewritten, reordered, or deleted.

## Scope
- Build a read-only baseline manifest tool that inventories every agent-monitoring/*.jsonl file (runs.jsonl, events.jsonl, tools.jsonl): line count, byte size, SHA-256 hash, parser/validator result, legacy-warning count, one record per file, reproducible on re-run
- Build a fixture corpus under tests/fixtures/ covering all 6 documented legacy shapes (5 runs.jsonl generations + the TCK-20260623-TYPE-CHECKER exception, plus tools.jsonl/events.jsonl null-gap variants) per docs/agent-monitoring/schema.md
- Add a legacy-reader test asserting correct parse and provenance classification for each fixture shape
- Reuse validate.py's load_jsonl and the SHA-256 snapshot pattern from tests/agent_replay/test_no_mutation_snapshot.py

## Out of Scope
- No changes to any monitoring writer (post_tool_hook.py, record_run.py, record_events.py) — this ticket is read-only inventory/fixtures only
- No historical JSONL remediation, rewriting, reordering, or backfilling
- No live .codex/ hook wiring
- Does not implement the shared writer module (owned by the monitoring-writer-unification ticket)

## Acceptance Criteria
- [ ] Manifest tool produces one record per JSONL file in agent-monitoring/ (line count, byte size, SHA-256 hash, parser result, legacy-warning count)
- [ ] Running the manifest tool twice against unchanged input produces byte-identical output (reproducibility)
- [ ] Manifest tool run causes zero git diff on agent-monitoring/*.jsonl (read-only proof, verified via hash comparison before and after)
- [ ] Fixture corpus contains one fixture per documented legacy shape (5 runs.jsonl generations + TCK-20260623-TYPE-CHECKER exception + tools.jsonl/events.jsonl null-gap variants) as enumerated in docs/agent-monitoring/schema.md
- [ ] A legacy-reader test asserts each fixture parses correctly and is classified with correct provenance (schema-generation label)
- [ ] Current Claude-written monitoring records remain readable (round-trip parse test) before and after the new reader is introduced
- [ ] Manifest tool avoids a full in-memory parse of tools.jsonl (~18MB) — parses in a streaming/bounded manner (verified by code review or a memory-bound test)

## Related Tickets
- TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC
- TCK-20260705-MONITORING-RUNID-JOIN
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260721-CODEX-REPLAY-PROOF
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR

## Related Docs
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/agent-monitoring/schema.md
- docs/ai/monitoring_writer_decision.md
- docs/ai/replay_fixture_spec.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/agent-monitoring/schema.md
- docs/ai/monitoring_writer_decision.md
- docs/ai/replay_fixture_spec.md
- tools/agent-monitoring/validate.py
- agent-monitoring/runs.jsonl
- agent-monitoring/events.jsonl
- agent-monitoring/tools.jsonl
- tests/agent_replay/test_no_mutation_snapshot.py
- tests/tools/test_validate_agent_monitoring.py
- tests/tools/test_monitoring_writer_lockfile_candidate.py

## Assumptions / Open Questions
- Assumes this ticket is Proposed Ticket Group #1 of the already-scoped epic, not duplicate work
- Assumes no tests/fixtures/ directory for legacy shapes exists yet (confirmed genuinely new work)
- Assumes tools.jsonl size (~18MB) requires a streaming/bounded manifest approach rather than full in-memory parse-repeat; exact technique left to this ticket's Plan phase

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
