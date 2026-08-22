---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD
phase: open
date: 2026-08-22
tags: [agent-monitoring]
---

# TCK-20260822-CODEBASE-HEALTH-SNAPSHOT-SCORECARD

## Title
Historical codebase-health snapshot mechanism and multi-dimension scorecard

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants a persistent, append-only mechanism — following the same pattern agent-monitoring/runs.jsonl already uses — that snapshots codebase-health metrics over time, plus a multi-dimension scorecard view over those snapshots. The scorecard must show trend arrows across dimensions, not collapse everything into a single aggregate score; the author is explicit that a single health score is out of scope, per the source audit's own guidance (docs/audits/D24_codebase_health_observatory.md §J/§M and docs/plans/codebase_health_observatory_tooling_epic.md "Out of scope"). Today there is no mechanism at all that persists these metrics across runs.

## Scope
- New module that calls tools/codebase_health_baseline.py::build_report() and serializes its dict as one JSON line appended to a new history file, following the agent-monitoring/runs.jsonl append-only pattern (no in-place rewrite of history).
- New scorecard reader/renderer that reads N historical snapshots and renders per-dimension trend arrows (up/down/flat), mirroring tools/personality_audit.py's Δ/↑↓→ pattern — no aggregate/combined score field anywhere in the output.
- Decide and document the scorecard's dimension set drawn from build_report()'s existing fields, and freeze/version the snapshot schema explicitly (or import the dict directly) so a future change to build_report() is a visible breaking change, not silent drift.
- Graceful degradation when only one historical snapshot exists: label metrics as having no trend data yet, do not crash or compute a spurious trend from a single point.
- New tests under tests/tools/ covering: two-invocation append-only persistence, per-dimension trend-arrow rendering, single-snapshot degradation, and schema freeze/versioning.
- Explicit, documented decision on Makefile wiring (on-demand target like the sibling codebase-health-baseline/codebase-health-impact targets, or state why not) — not CI-wired by default unless explicitly justified.

## Out of Scope
- PR / AI change-impact report generator — tracked separately as TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR.
- Any change to build_report()'s existing metric computation in tools/codebase_health_baseline.py — this ticket only consumes its dict output, never re-derives or duplicates metric logic.
- CI wiring of the new snapshot command as a required/blocking gate.
- A single aggregate/combined health score in any form, at any layer of the output.

## Acceptance Criteria
- [ ] Running the new snapshot command twice appends two separate JSON-line records to the new history file without truncating or rewriting the first record — verified by re-reading the file after each invocation and asserting both records are present.
- [ ] The scorecard view, given two or more historical snapshots, renders a directional trend indicator (up/down/flat) per individual metric/dimension, and its output contains no aggregate/combined 'score' field — verified by asserting absence of an aggregate field and presence of a per-dimension directional indicator.
- [ ] Given only one historical snapshot, the scorecard renders without crashing and labels each metric as having no trend data yet, rather than computing a trend from a single data point.
- [ ] The snapshot payload is built by calling tools/codebase_health_baseline.py's existing build_report() dict directly — no re-implementation/re-derivation of the underlying metrics computation and no parsing of format_report()'s printed text.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC
- TCK-20260819-STANDARD-CODEBASE-HEALTH-BASELINE-TARGET
- TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC

## Related Docs
- docs/audits/D24_codebase_health_observatory.md
- docs/plans/codebase_health_observatory_tooling_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/codebase_health_baseline.py
- tools/code_health_impact.py
- agent-monitoring/runs.jsonl
- docs/agent-monitoring/schema.md
- tools/personality_audit.py
- tests/tools/test_codebase_health_baseline.py
- tests/tools/test_code_health_impact.py
- Makefile
- expected: tools/codebase_health_snapshot.py
- expected: tests/tools/test_codebase_health_snapshot.py

## Assumptions / Open Questions
- build_report()'s exact dict schema (tools/codebase_health_baseline.py lines 233-253) is treated as the de facto snapshot payload contract; this ticket freezes/versions the snapshot schema explicitly (or imports the dict directly) so a future change there is a visible breaking change rather than silent drift.
- This ticket decides the scorecard's dimension set (which of build_report()'s ~13 fields become dimensions) and how many historical points define a "trend" — the epic's own AC only requires "at least two runs" and nothing else will make this decision, so it is treated as in-scope here.
- No existing generic JSONL-append utility exists in tools/ (each JSONL writer inlines its own append logic); this ticket may add a small shared append helper or continue the repo's existing inline-append pattern at the implementer's discretion.
- TCK-20260822-CHANGE-IMPACT-REPORT-GENERATOR is explicitly sequenced after this ticket and may depend on this ticket's snapshot output shape — this ticket's scope must not creep into that ticket's report-generator surface.
- `layer: observability` was chosen (registered note: "Agent monitoring, dashboards, event bus, telemetry") since this ticket builds a dashboard/telemetry-style scorecard over codebase-health metrics and explicitly reuses the agent-monitoring append-only pattern; flagged for reviewer judgment since the code itself lives in tools/, not src/observability/.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
