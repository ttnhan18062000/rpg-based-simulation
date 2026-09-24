---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260924-RECORD-HAND-ORCHESTRATED-CLOSURE-AGENT-FIELD-VALIDATION-GAP
phase: open
date: 2026-09-24
tags: [agent-monitoring, data-quality]
---

# TCK-20260924-RECORD-HAND-ORCHESTRATED-CLOSURE-AGENT-FIELD-VALIDATION-GAP

## Title

`record_hand_orchestrated_closure.py --events` accepts an arbitrary `agent` override with no
validation against the canonical `WORKFLOW_AGENTS` vocabulary

## Status

OPEN

## Tier

hotfix

## Type

bug

## Priority

P2

## Request Summary

Confirmed real, not hypothetical: while closing `TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW`
by hand-orchestration, a `record_hand_orchestrated_closure.py --events` call used a per-event
`agent` override of `"rpg-feature-planning"` (a peer session's *name*, used to attribute which
session scoped the ticket) instead of a canonical agent *role* from
`tools/agent-monitoring/vocabulary.py::WORKFLOW_AGENTS["implement-ticket"]`. The tool accepted it
silently — no warning, no rejection — and wrote it straight into
`agent-monitoring/data/2026-W39/events.jsonl`.

This single non-canonical literal pushed the corpus-wide `vocabulary_drift` ratchet check
(`tools/gate_checks/monitoring_anomaly_validator.py`, `AGENT_DRIFT_CEILING = 162`) from 162 to
163, failing `tests/tools/test_monitoring_anomaly_validator.py::test_real_corpus_is_at_or_below_every_ratchet_ceiling`
and `::test_cli_prints_marker_output_not_merely_a_return_code` in CI on PR #245 — a real,
reproducible CI failure caused entirely by this validation gap, not by the ticket's own
Combat/Territory mapping work. Fixed for that one row by hand (`agent: "claude"`, peer attribution
moved into the event's `summary` text, matching existing corpus convention) — this ticket is the
follow-up for the tool's own missing guard, deliberately not fixed inside PR #245's scope.

## Scope

- `tools/agent-monitoring/record_hand_orchestrated_closure.py`'s per-event `agent` override (and/or
  `record_events.py`'s own `agent` field validation, whichever is the right layer) should reject or
  at minimum hard-warn-and-require-confirmation when an `agent` value is not in
  `WORKFLOW_AGENTS["implement-ticket"]` — the same vocabulary `record_events.py` already checks
  elsewhere via `warn_vocabulary_drift`, but this path let it through into the real corpus.
- Confirm whether `record_events.py`'s own `warn_vocabulary_drift` was ever invoked for this
  specific call path, and why it didn't catch (or didn't block) this value.

## Out of Scope

- Re-litigating whether `warn_vocabulary_drift` should hard-fail vs. warn in general — scope this
  to the specific hole that let a session *name* (never a role) through unchallenged.
- Any other historical non-canonical agent literal already in the corpus (e.g. `claude-sonnet-4-6`,
  `claude-fork-direct`, `scope-agent`, `plan-fixer`) — those are pre-existing drift, not this gap.
- Lowering `AGENT_DRIFT_CEILING` back down — it already correctly ratcheted to reject growth; this
  ticket is about the emitter, not the gate.

## Acceptance Criteria

1. `record_hand_orchestrated_closure.py --events` with an `agent` value outside
   `WORKFLOW_AGENTS["implement-ticket"]` (plus the existing "claude"/"orchestrator" exceptions) is
   rejected with a clear error, or requires an explicit opt-in flag — never silently accepted.
2. A regression test proves a session-name-shaped `agent` value (e.g. a hyphenated peer session
   name, not a role) is caught before it reaches `events.jsonl`.
3. Existing legitimate hand-orchestration usage (`agent: "claude"`) continues to work unchanged.

## Related Tickets

- `TCK-20260924-M4-COMBAT-SLICE-CROSS-DOMAIN-VIEW` — where this was found and hand-fixed for the
  one affected row.
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` — introduced
  `record_hand_orchestrated_closure.py` itself.

## Related Docs

- None yet identified beyond the tool's own docstring.

## Related Stored Artifacts

- None yet — ticket not yet started.

## Related Code Areas

- `tools/agent-monitoring/record_hand_orchestrated_closure.py`
- `tools/agent-monitoring/record_events.py::warn_vocabulary_drift`
- `tools/agent-monitoring/vocabulary.py::WORKFLOW_AGENTS`
- `tools/gate_checks/monitoring_anomaly_validator.py` (the ratchet this gap fed)

## Assumptions / Open Questions

- Whether the right fix is a hard rejection or a required `--allow-noncanonical-agent` opt-in flag
  is an implementation call for whoever picks this up.

## Implementation Notes

_To be completed by the implementer._

## Test Summary

_To be completed by the implementer._

## Files Changed

_To be completed by the implementer._

## Completion Summary

_To be completed by the implementer._
