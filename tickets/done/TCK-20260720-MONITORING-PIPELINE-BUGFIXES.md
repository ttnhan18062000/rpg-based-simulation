---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-MONITORING-PIPELINE-BUGFIXES
phase: open
date: 2026-07-20
tags: [agent-monitoring, data-quality, workflows]
---

# TCK-20260720-MONITORING-PIPELINE-BUGFIXES

## Title
Fix live monitoring-pipeline bugs found by the 2026-07-20 agent-orchestration audit

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
A deep audit of all agent-orchestration logic in this repository (5 parallel investigations
covering agents/workflows, skills/hooks, gate-checks/monitoring pipeline, CLAUDE.md/docs
consistency, and legacy `.agents/`/dead-code) surfaced 3 live, reproducible bugs in the
monitoring/workflow pipeline, all violating this project's own hard rule that every workflow run
must record a monitoring entry, and one crashing on real production data. Fixing all three in one
consolidated hotfix per user direction (minimize distinct tickets, hotfix tier for small,
self-evident fixes).

## Scope
- `tools/agent-monitoring/generate_retro.py`: `--days N` crashed with `TypeError: '>=' not
  supported between instances of 'float' and 'str'` — 105 of 684 real `runs.jsonl` records have a
  legacy/non-string/missing `start_ts`. Added `_record_since_cutoff()`, mirroring the existing
  `iso_week()` fail-to-`"unknown"` defensive pattern for the `--week` path, excluding unparseable
  records from the window instead of crashing the comparison.
- `.claude/workflows/implement-ticket.js`: the Scope phase dereferenced
  `ticketInfo.ticket_id` with no null-guard — a null/malformed `ticket-scoper` response would
  throw before `events`/`pushEvent`/`writeMonitoring` are even defined, meaning zero monitoring
  record could be written for that failure. Added a null-guard immediately after the Scope
  `agent()` call that writes a minimal, self-contained monitoring record directly via `bash()`
  (new terminal status `SCOPE_AGENT_FAILED`), deliberately not depending on any
  later-in-file helper (`captureTs`/`writeSidecar`/`writeMonitoring`).
- `.claude/workflows/implement-epic.js`: 3 early-return exit paths (`INVALID_ARGS`,
  `EPIC_CREATED`, `NOTHING_TO_DO`) returned before the batch-monitoring-write `agent()` call,
  silently skipping monitoring — contradicting `docs/ai/workflows.md`'s own claim that
  `runs.jsonl`/`events.jsonl` are always-produced artifacts for this workflow. Added a minimal,
  self-contained monitoring write (via direct `bash()` calls, not agent-interpolated text, to
  avoid this file's own documented shell-quote-corruption risk) to each of the 3 paths.

## Out of Scope
- The 16 other findings from the same audit — batched separately per user direction (CLAUDE.md/
  docs self-consistency corrections, docs/ai/*.md + schema.md accuracy, gate-check wiring
  decisions, skills/docs orphan cleanup).
- `simq-audit.js`'s 3 missing agent files and the broken `Makefile` profiling targets — also from
  the same audit, but not monitoring-pipeline bugs; tracked separately.
- The `.agents/`/`WorkflowRegistry` test-dependency finding — feeds into the provider-agnostic
  orchestration discovery epic's `.agents/` disposition ticket, not this batch.

## Acceptance Criteria
- [x] `python3 tools/agent-monitoring/generate_retro.py --days 7` runs to completion against the
      real `agent-monitoring/` corpus without raising.
- [x] `_record_since_cutoff()` excludes non-string, `None`, and empty `start_ts` values instead of
      comparing them, verified by dedicated unit tests.
- [x] `implement-ticket.js`'s Scope phase has a null-guard positioned before the unguarded
      `ticketInfo.ticket_id` dereference, verified by a static source-text regression test; the
      guard block writes a run record before returning and does not call any helper defined later
      in the file.
- [x] `implement-epic.js`'s `INVALID_ARGS`, `EPIC_CREATED`, and `NOTHING_TO_DO` paths each write a
      run record (the latter two also an event record) before returning, verified by static
      source-text regression tests; the new code uses fixed literal summary strings, never raw
      agent-returned text, in the shell-interpolated JSON payloads.
- [x] No regression in existing test coverage: `tests/tools/test_generate_retro.py` (37/37),
      `tests/tools/test_monitoring_bypass_fix.py` (7/7, new), and the broader
      monitoring/workflow/sidecar-scoped suite (119/119) all pass.

## Related Tickets
- TCK-20260718-AGENTOPS-STATS-API (discovered the same `generate_retro.py --days` crash during
  its own testing and explicitly deferred fixing it as out-of-scope; this ticket closes that gap)
- TCK-20260706-MONITORING-REASON-CODE (established the shell-quote-corruption precedent this
  ticket's `implement-epic.js` fix deliberately avoids by using fixed literal summaries)
- TCK-20260711-EPIC-SCOPE-ORPHAN-FIX (prior art for orchestrator-side, non-agent-interpolated
  monitoring/bookkeeping writes in these same two workflow files)

## Related Docs
- docs/agent-monitoring/schema.md (Known Limitations — 5+ legacy schema generations, the source
  of the non-string/missing `start_ts` values this fix defends against)
- docs/ai/workflows.md (claims `runs.jsonl`/`events.jsonl` are always-produced artifacts for
  `implement-epic` — this ticket makes that claim true for all 3 previously-silent exit paths)

## Related Stored Artifacts
None (hotfix — self-evident intent captured in this ticket).

## Related Code Areas
- tools/agent-monitoring/generate_retro.py
- tests/tools/test_generate_retro.py
- .claude/workflows/implement-ticket.js
- .claude/workflows/implement-epic.js
- tests/tools/test_monitoring_bypass_fix.py

## Assumptions / Open Questions
- `implement-ticket.js`'s new `SCOPE_AGENT_FAILED` terminal status is not yet added to
  `docs/agent-monitoring/schema.md`'s `final_status` enum table or `docs/ai/workflows.md`'s
  Return-values table — deferred to the TCK-C batch (docs/ai/*.md + schema.md accuracy), which is
  already scoped to fix exactly this class of drift in the same pass rather than touching those
  docs piecemeal across two different tickets.
- `implement-epic.js`'s `INVALID_ARGS` path writes a monitoring record using a synthesized
  `EPIC-INVALID-ARGS-{timestamp}` run_id, since no folder/epic_id/request was ever provided to
  construct a real identifier from — consistent with `create-tickets.js`'s own precedent of
  synthesizing a run_id when no ticket_id exists yet.

## Implementation Notes
All 3 fixes are minimal, targeted, self-evident bug fixes — no design ambiguity, no behavior
change beyond "write the monitoring record the hard rule already requires" and "don't crash on
legacy data the schema doc already documents as existing." Implemented directly (audit already
did the investigation) rather than via the full multi-agent `implement-ticket` workflow, per user
direction to move fast on this consolidated batch.

## Test Summary
- `tests/tools/test_generate_retro.py`: 37/37 passing (33 pre-existing + 4 new:
  `test_record_since_cutoff_true_for_iso_string_at_or_after_cutoff`,
  `test_record_since_cutoff_false_for_iso_string_before_cutoff`,
  `test_record_since_cutoff_excludes_non_string_start_ts_instead_of_raising`,
  `test_generate_retro_days_flag_does_not_raise_on_legacy_start_ts`).
- `tests/tools/test_monitoring_bypass_fix.py`: 7/7 passing (new file, static source-text
  regression tests over the 2 workflow `.js` files — no JS test runner exists in this repo for
  `.claude/workflows/*.js`, matching this repo's established test convention for these files).
- Broader scoped regression (`monitoring or retro or workflow or sidecar or step0 or
  scope_orphan`): 119/119 passing, 0 regressions.
- Live verification: `python3 tools/agent-monitoring/generate_retro.py --days 7` run directly
  against the real `agent-monitoring/` corpus — completed without error (80 runs, 646 events).

## Files Changed
- tools/agent-monitoring/generate_retro.py
- tests/tools/test_generate_retro.py
- .claude/workflows/implement-ticket.js
- .claude/workflows/implement-epic.js
- tests/tools/test_monitoring_bypass_fix.py (new)

## Completion Summary
Fixed 3 live monitoring-pipeline bugs found by the 2026-07-20 agent-orchestration audit: a
reproducible crash in `generate_retro.py --days` on legacy production data, a Scope-phase
null-guard gap in `implement-ticket.js` that could bypass monitoring entirely on agent failure,
and 3 silent monitoring-skip exit paths in `implement-epic.js` that contradicted its own
documented artifact guarantees. All fixes are minimal and self-contained; no design decisions
deferred except doc-enum updates, explicitly routed to the already-planned TCK-C batch rather than
duplicated here. 44 tests (37 existing + 7 new) pass; live-verified against the real
`agent-monitoring/` corpus.
