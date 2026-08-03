---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260803-RETRO-TOOL-SAFETY-AUDIT
phase: open
date: 2026-08-03
tags: [agent-monitoring, retro]
---

# TCK-20260803-RETRO-TOOL-SAFETY-AUDIT

## Title
Add a retro report section auditing parity_index.py safe-usage and search-before-grep hard-rule compliance

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
While reviewing this session's own work, the user asked whether the retro/agent-monitoring system
can verify that the new parity read-path tooling (`tools/parity_index.py`) and the project's
context-search hard rule (CLAUDE.md: `search_docs` + `graphify` before any grep/raw file read) were
actually used correctly. Answering that required hand-querying `agent-monitoring/tools.jsonl`
directly — the weekly retro report (`tools/agent-monitoring/generate_retro.py`) has no section that
would have surfaced either answer on its own.

Concretely verified by hand this session, across all 7 real Investigate-phase agent calls and all 4
parity-epic ticket runs:
1. `mcp__knowledge-search__search_docs` and `graphify` (via Bash) both fired within the first 3-6
   tool calls of every Investigate phase, always before the first `grep` (which never appeared
   earlier than call #11 in any of the 7). The hard rule was genuinely honored, not just claimed.
2. Zero `Edit`/`Write` tool calls ever targeted any `docs/parity_ledger/*.yaml` file across the 4
   parity-epic runs, and every live `parity_index.py build` CLI invocation pointed at a scratch path
   (e.g. `/tmp/pi_smoke2/parity.db`), never the real repo DB path.

Both checks are real and currently only answerable by a one-off manual query. This ticket adds them
as a standing, automatically-computed retro section so future weeks don't require the same manual
`tools.jsonl` archaeology.

## Scope
- Add a new pure-computation function to `tools/agent-monitoring/generate_retro.py` (mirroring
  `compute_retrieval_metrics(events)`'s existing shape — a standalone function taking already-loaded
  data and returning a dict, no file I/O of its own) that reads `agent-monitoring/tools.jsonl` rows
  (not `events.jsonl` — `tools.jsonl` is the raw per-tool-call log this audit needs) and computes,
  per run_id/seq where a real `Investigate` phase occurred (cross-referenced against
  `events.jsonl`'s `phase` field the same way `compute_shadow_baseline_comparison` already
  cross-references event data):
  - **Search-before-grep compliance**: for each Investigate-phase seq, whether
    `mcp__knowledge-search__search_docs` (or a `graphify` Bash call) appears before the first
    `Grep` tool call or Bash call containing `grep` in its `input_summary` — a boolean per
    (run_id, seq), aggregated into a compliance rate for the period.
  - **`parity_index.py` write-safety**: across the whole period, whether any `Edit`/`Write` tool
    call's `input_summary` names a `docs/parity_ledger/*.yaml` path, and whether any
    `parity_index.py build` Bash invocation's `input_summary` targets a path under the real repo's
    `docs/parity_ledger/`-adjacent `parity-index/` location rather than a scratch/tmp path — both
    should be zero; report the actual count, never assume it's zero.
- Wire the new section into `generate()`'s markdown output, following the existing conditional-
  render convention (e.g. "Shadow vs. Baseline Retrieval Comparison"'s pattern: omitted entirely
  when there's no real Investigate-phase data in the period, never rendered as an empty table).
- Add a row to `docs/guides/agent_monitoring.md`'s "Report Sections" table describing what to look
  for in the new section, matching that table's existing terse per-row style.
- Add tests to `tests/tools/test_generate_retro.py` mirroring `TestComputeRetrievalMetrics`'s
  fixture-based structure: at minimum, a compliant-ordering fixture (search_docs before grep) that
  reports 100% compliance, a violating-ordering fixture (grep before search_docs) that reports the
  violation, a clean parity-safety fixture (zero writes to `docs/parity_ledger/`, all builds to
  scratch paths) that reports zero violations, and a synthetic violating fixture (a fabricated
  `Edit` call targeting `docs/parity_ledger/combat_movement.yaml`) that the new function correctly
  flags — do not rely solely on the real, currently-clean `tools.jsonl` data to prove the check
  works, since a check that has never seen a violation could be silently broken.

## Out of Scope
- Retroactively re-auditing or re-writing any historical `tools.jsonl`/`events.jsonl` data — this
  is a new, forward-looking read-only report section over existing append-only logs.
- Making this a blocking gate anywhere in `.claude/workflows/implement-ticket.js` — matches every
  other retro section's status as a human-reviewed report, not a workflow gate. If a future ticket
  wants to promote search-before-grep compliance or parity-write-safety into an actual blocking
  check (e.g. a new `PreToolUse` hook), that is a separate, explicitly-scoped decision, not implied
  by this ticket.
- Generalizing the "write-safety" check beyond `docs/parity_ledger/*.yaml` to any other tool/data
  path (e.g. a general "which tools touched which protected paths" audit) — scope this specifically
  to `parity_index.py`'s read-only guarantee, the concrete case that prompted this ticket. A more
  general protected-path audit is a plausible future ticket, not this one.
- Any change to `tools/parity_index.py`, `tools/context_packet_assembler.py`, or the `PostToolUse`
  hook that writes `tools.jsonl` itself (`tools/agent-monitoring/post_tool_hook.py` or equivalent) —
  this ticket only reads existing log data, it does not change what gets logged.
- Adding the shadow-`ContextPacket` mechanism's "correctness" to this ticket — that mechanism
  (`compute_retrieval_metrics`) already has its own retro section; it remains structurally empty
  today because no real retrieval pipeline is wired into its call site (a separate, already-known,
  already-out-of-scope gap — not something this ticket resolves).

## Acceptance Criteria
- [ ] A new pure-computation function in `tools/agent-monitoring/generate_retro.py`, given
      `runs`/`events`/`tools` fixture data, correctly reports search-before-grep compliance rate
      per Investigate-phase (run_id, seq) pair and a `parity_index.py` write-safety violation count,
      matching what a manual query against real `tools.jsonl` independently confirms for the same
      period.
- [ ] The new function never crashes on legacy/malformed rows (missing `input_summary`, missing
      `seq`, tool-call rows with no matching `phase`/`events.jsonl` cross-reference) — same
      graceful-skip discipline `_is_legacy_event`/`_resolve_status` already use elsewhere in this
      file.
- [ ] `generate()`'s markdown output includes the new section, conditionally rendered (omitted, not
      empty, when the period has zero real Investigate-phase tool-call data), matching the existing
      "Shadow vs. Baseline Retrieval Comparison" section's render-gating pattern.
- [ ] `docs/guides/agent_monitoring.md`'s "Report Sections" table has a new row for this section.
- [ ] New tests in `tests/tools/test_generate_retro.py` include at least one synthetic fixture that
      proves each check can detect a real violation (not just confirm today's clean data stays
      clean) — a compliance-ordering violation and a `docs/parity_ledger/` write violation, each
      with a corresponding passing/compliant fixture for contrast.
- [ ] Running `python3 tools/agent-monitoring/generate_retro.py` against this repo's real
      `agent-monitoring/*.jsonl` data produces a report whose new section's numbers match this
      ticket's own hand-verified findings (100% search-before-grep compliance across the 7 real
      Investigate phases checked, 0 `docs/parity_ledger/*.yaml` write violations across the 4 parity
      runs checked) for the equivalent time window.

## Related Tickets
- TCK-20260731-PARITY-INDEX-EPIC (built the `parity_index.py` read-only tooling this audit checks)
- TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT, TCK-20260729-RETRIEVAL-RETRO-VIEWS,
  TCK-20260729-SHADOW-BASELINE-COMPARISON (established the `compute_*_metrics(events)` /
  conditionally-rendered-section precedent this ticket's implementation should mirror)
- TCK-20260704-RETRO-LOOP-ENFORCEMENT (established the retro cadence/nudge convention this new
  section becomes part of)

## Related Docs
- docs/guides/agent_monitoring.md (Report Sections table — gets a new row)
- docs/agent-monitoring/schema.md (tools.jsonl field reference)

## Related Stored Artifacts
None yet (scoped, not yet investigated/planned).

## Related Code Areas
- tools/agent-monitoring/generate_retro.py (new function + `generate()` wiring)
- tests/tools/test_generate_retro.py (new tests)
- agent-monitoring/tools.jsonl (read-only data source — the field this audit reads that no existing
  retro computation reads)
- tools/parity_index.py (read-only reference — the tool being audited, not modified)

## Assumptions / Open Questions
- Assumes `tools.jsonl`'s existing `run_id`/`seq` fields are sufficient to cross-reference against
  `events.jsonl`'s `phase` field to identify "which tool calls happened during an Investigate
  phase" — this matches the manual query technique already proven working this session, but
  Investigate should confirm no edge case (e.g. a tool call recorded with `seq: null`, per this
  project's own documented sidecar-attribution-gap precedent) silently breaks the cross-reference
  rather than degrading gracefully.
- Whether the write-safety check should also cover `.gitignore`/Makefile paths (mirroring the
  parity-epic tickets' own protected-file lists) or stay narrowly scoped to
  `docs/parity_ledger/*.yaml` is left for Investigate/Plan to decide — this ticket's Scope
  deliberately names only the parity-ledger YAML case as the concrete, already-verified example.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
