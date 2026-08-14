---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-LIVE-PHASE-AGENT-LABEL
phase: done
date: 2026-07-19
tags: []
---

# TCK-20260719-LIVE-PHASE-AGENT-LABEL

## Title
Live phase/agent labeling for in-progress tools.jsonl rows

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
During a live/in-progress implement-ticket workflow run, agent-monitoring/tools.jsonl rows carry only a bare seq integer — no phase, no agent name — anywhere on disk. writeSidecar(seq) in .claude/workflows/implement-ticket.js writes only {run_id, seq} to .claude/current_run, and tools/agent-monitoring/post_tool_hook.py only copies those two fields into each tools.jsonl record. events.jsonl does map seq to phase/agent but is only written once, at a run's exit point — so for a ticket passing cleanly through all phases, zero phase-level data exists on disk until the very end, meaning a live dashboard reading only currently-written files can show "a tool call just happened" but never which phase/agent produced it. phase and agent are already known as literals at every writeSidecar call site (each is immediately preceded by a phase('X') call and paired a few lines later with a pushEvent(phase, agentName, ...) call) — no new plumbing is needed, only threading these already-known values through writeSidecar(seq, phase, agent) and into post_tool_hook.py's read/write. This would unlock a live dashboard's in-progress-run indicator showing e.g. "TCK-... — Implement (implementer) running" instead of an unlabeled raw tool-call stream. It explicitly does NOT unlock phase/gate history (pass/fail per phase) before a run completes — that would require changing writeMonitoring()'s call cadence itself, a materially riskier change to the core orchestration script, and is out of scope.

## Scope
- Thread phase/agent through writeSidecar(seq) -> writeSidecar(seq, phase, agent) at all 10 call sites in .claude/workflows/implement-ticket.js. Re-locate all 10 sites by content match (a phase('X') call immediately followed by the writeSidecar( call) — do NOT trust the source idea doc's line-number citations, which are confirmed stale (8 of 10 are off by a consistent +22 lines, actual current lines are 419, 460, 541, 610, 679, 740, 889, 981, 1044, 1098, evidently from an intervening captureTs() insertion by TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH).
- Update tools/agent-monitoring/post_tool_hook.py to read phase/agent from the .claude/current_run sidecar (same try/except-wrapped read pattern already used for run_id/seq, lines 43-51) and include them in each tools.jsonl record (lines 61-70 build the record dict).
- Update tests/tools/test_current_run_sidecar_orchestrator.py for the new 3-arg writeSidecar signature: _COVERED_SITE_ADJACENCY (lines 49-60, 10 hardcoded adjacency strings), test_tid_and_seq_passed_as_argv_not_json_embedded (line 177, regexes the exact helper signature), and test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure (line 198, literal signature match) all need updating.
- Update docs/agent-monitoring/schema.md's tools.jsonl Fields table (lines 221-228) to document the two new nullable fields, following the same convention used when tool_call_count/reason_code/cost_proxy_score were added (lines 109-111).
- Make and implement an explicit decision for whether the Scope phase's separate inline sidecar-write branches (a distinct, non-writeSidecar()-helper code path added by TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION, since ticket_scoper's tid is not yet known at Scope time) should also receive phase='Scope'/agent='ticket-scoper' literals — this is a 3rd write path not counted among the idea doc's "10 call sites" and the idea doc is silent on it; investigation flagged it as a real gap that must be decided and implemented, not left open.
- Add new test coverage for post_tool_hook.py's phase/agent read+include logic — no dedicated test file exists for this module today (no tests/tools/test_post_tool_hook.py found), so this needs new tests authored from scratch, not an extension of an existing suite.

## Out of Scope
- Changing writeMonitoring()'s call cadence (e.g. flushing after every phase instead of once per run) or surfacing phase/gate *history* (pass/fail per phase, final status) before a run completes — explicitly out of scope per the source idea doc; a materially riskier change to the core orchestration script.
- Backfilling historical tools.jsonl rows with phase/agent — new fields are nullable/additive only, matching the append-only, no-backfill precedent already set by tool_call_count/cost_proxy_score/reason_code.
- Validating the new phase/agent values against tools/agent-monitoring/vocabulary.py's WORKFLOW_PHASES/is_known_agent canonical vocabulary — left unvalidated per the idea doc's minimal-plumbing intent; a candidate follow-up, not required here.
- Any dashboard-side consumption or rendering of the new fields (e.g. the Agent Ops Dashboard's live-run indicator actually displaying "Implement (implementer) running") — this ticket only produces the data; wiring a live UI to consume it is separate, follow-up work.

## Acceptance Criteria
- [ ] Calling writeSidecar(seq, phase, agent) at any of the 10 call sites writes {run_id, seq, phase, agent} to .claude/current_run, and a tools.jsonl row written by post_tool_hook.py during that phase's tool calls includes non-null "phase" and "agent" fields matching the literals passed at that call site.
- [ ] A tools.jsonl row appended for a tool call made outside any active workflow run (run_id: null) has "phase": null, "agent": null — additive/nullable, no behavior change to non-workflow tool tracking.
- [ ] A tools.jsonl row appended before this change (historical rows) remains readable by any consumer that treats missing phase/agent keys as None/absent — no backfill, no schema-breaking read failure.
- [ ] tests/tools/test_current_run_sidecar_orchestrator.py's _COVERED_SITE_ADJACENCY, test_tid_and_seq_passed_as_argv_not_json_embedded, and test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure all pass against the new 3-arg signature (updated, not just coincidentally still passing).
- [ ] docs/agent-monitoring/schema.md's tools.jsonl Fields table documents phase/agent with the same nullable/historical-null convention language used for tool_call_count/reason_code/cost_proxy_score.
- [ ] An explicit, documented decision is implemented for whether Scope phase's inline sidecar-write branches also receive phase/agent literals — not left as an unresolved open question.

## Related Tickets
- TCK-20260710-CURRENT-RUN-SIDECAR-BASH
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
- TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH

## Related Docs
- docs/plans/agent_ops_dashboard/idea_agent_monitoring_live_phase_label.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- tools/agent-monitoring/post_tool_hook.py
- tests/tools/test_current_run_sidecar_orchestrator.py
- docs/agent-monitoring/schema.md
- tools/agent-monitoring/vocabulary.py

## Assumptions / Open Questions
- Whether Scope's inline sidecar branches should also get phase/agent literals is treated as an in-scope, must-decide-and-implement item (see Scope bullet above) rather than left open, since investigation flagged it as a real gap the source idea doc is silent on.
- Field naming (phase, agent — matching events.jsonl's existing field names) is assumed correct; investigation found no conflicting vocabulary.

## Implementation Notes

**Step 1** — `writeSidecar` helper (`.claude/workflows/implement-ticket.js:202-209`) changed from
`async (seq) =>` to `async (seq, phase, agent) =>`. `phase`/`agent` are passed as two additional
individually-quoted argv elements (`"${tid}" "${seq}" "${phase}" "${agent}"`), read via
`sys.argv[3]`/`sys.argv[4]` inside the embedded `python3 -c` script and added to the `json.dumps`
dict — never JSON-embedded directly in the `-c` string, matching the existing `tid`/`seq` argv
convention. All 10 call sites updated per the investigation's Current Behavior mapping
(Investigate→investigator, Plan→planner, Review→architecture-reviewer, Implement→implementer,
Architecture-Verify→architecture-reviewer, Test→test-scoper, Parity→parity-updater,
Security-Review→security-reviewer, Verify→done-checker, Finalize→finalizer). Edits made with the
`Edit` tool (targeted string replacement) per the plan's Implementation Safety section, to keep
each call-site edit atomic while `.claude/workflows/implement-ticket.js` is the live orchestrator
script for this very run.

**Step 2 — Scope-phase decision (implemented as planned):** the Scope-phase inline sidecar write's
resume branch (`if (ticketId) { ... }`) now writes `phase: 'Scope', agent: 'ticket-scoper'` as
hardcoded string literals alongside the existing `run_id`/`seq` keys. The `else` (new-ticket) branch
is untouched — it still writes bare `{}`. Rationale: the resume branch already carries a real
`run_id` and is a direct, low-cost extension of the same JSON literal, consistent with this
ticket's live-dashboard motivation (Scope is the first phase of every run). The new-ticket branch
represents a materially different state — "no run identity known at all" — where adding
phase/agent without a run_id would create a new, undocumented partial-record shape with no
identified consumer need, and would additionally require updating
`test_scope_phase_has_sidecar_coverage`'s `printf '{}'` assertion for zero AC-mapped benefit.
`post_tool_hook.py`'s existing `.get(...) or None` read pattern already produces
`phase: null, agent: null` for the new-ticket branch's tool calls for free.

**Step 3** — `post_tool_hook.py`: added `phase = sidecar.get("phase") or None` and
`agent = sidecar.get("agent") or None` inside the existing sidecar-read `try/except Exception: pass`
block; added `"phase": phase, "agent": agent,` to the `record` dict, inserted between `"seq"` and
`"ts"`. The `fcntl.flock` locking block was not touched.

**Steps 4-6** — Updated `tests/tools/test_current_run_sidecar_orchestrator.py` (6 items: adjacency
list, call-count regex, Finalize regex, renamed argv-embedding test, single-definition literal
match, Scope-phase hardcoded string) and `tests/tools/test_post_tool_hook.py` (`_RECORD_FIELDS`,
extended no-sidecar test, 2 new tests). Documented `phase`/`agent` in
`docs/agent-monitoring/schema.md`'s `tools.jsonl` Fields table, JSON example, and attribution
prose; added `test_schema_doc_documents_tools_jsonl_phase_agent_fields`.

**Deviation from plan (documented per CLAUDE.md "never silently deviate"):** while running the
updated test suite, discovered that `tests/tools/test_step0_ts_orchestrator.py` — a third test
file neither the ticket, investigation, nor plan enumerated — also hardcodes the pre-change
`writeSidecar(events.length + 1)` bare-call shape (in `_IMPLEMENT_TICKET_ADJACENCY`, 9 of its 10
entries) and the literal `"const writeSidecar = async (seq)"` helper-signature match (in
`test_captureTs_helper_defined_once_after_writeSidecar`). Both broke under the Step 1 signature
change for the same mechanical reason Step 4's items 2/3/5 did. Fixed both — same category of
mechanical literal update, no design decision involved — and re-ran the full file
(`tests/tools/test_step0_ts_orchestrator.py`, 6/6 passing). See
`staging_artifacts/TCK-20260719-LIVE-PHASE-AGENT-LABEL/plan.md`'s Deviations section for the full
record.

**Step 7** — `behavior_changed` reported as `true` per the plan's rationale: `tools.jsonl`'s
on-disk schema gains two keys per row and `writeSidecar`'s call signature changes, which is an
observable behavior change to the monitoring data pipeline even though no `src/` file changed —
required so the Parity phase runs and creates the `INFRA-281` ledger entry.

**Review round (documented per CLAUDE.md "no important decision is undocumented"):** Review
initially returned `NEEDS_CHANGES` against the Plan's first draft. That draft's "Implementation
Safety" section (reasoning about whether editing `.claude/workflows/implement-ticket.js` mid-run,
while this very pipeline was reading/acting on it, was safe) argued from Node.js
module-caching/hot-reload semantics — a false premise, since no Node process ever executes this
file. The real execution model, per `.claude/skills/implement-ticket/SKILL.md`'s own "Action"
section, is that an orchestrating Claude session reads the file once as plain text and manually
translates each phase into tool calls; nothing "hot-reloads." The section was rewritten to reason
from that correct model instead: edits don't retroactively change phases the orchestrator already
executed from its initial read, and the one real residual risk (a context compaction/re-read
mid-pipeline picking up the new 3-arg signature partway through) was named explicitly and judged
acceptable because the signature change is purely additive/backward-compatible. Review re-ran
against the corrected plan and returned `APPROVED`; no other section of the plan changed as part of
this correction.

## Test Summary
- `tests/tools/test_current_run_sidecar_orchestrator.py` — 11/11 passing (6 updated per plan Step 4,
  1 new per Step 6, 4 pre-existing unmodified).
- `tests/tools/test_post_tool_hook.py` — 5/5 passing (2 updated, 2 new per plan Step 5, 1
  pre-existing unmodified).
- `tests/tools/test_step0_ts_orchestrator.py` — 6/6 passing (2 updated as an undocumented-gap fix,
  not in the original plan; 4 pre-existing unmodified).

## Files Changed
- `.claude/workflows/implement-ticket.js`
- `tools/agent-monitoring/post_tool_hook.py`
- `tests/tools/test_current_run_sidecar_orchestrator.py`
- `tests/tools/test_post_tool_hook.py`
- `tests/tools/test_step0_ts_orchestrator.py` (deviation — not in original plan scope)
- `docs/agent-monitoring/schema.md`
- `docs/parity_ledger/infrastructure.yaml` (INFRA-281 appended, from the Parity phase)
- `docs/REGISTRY.yaml` (regenerated, Finalize post-migration self-check)
- `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, `agent-monitoring/tools.jsonl`
  (this run's monitoring records, staged per CLAUDE.md convention)

## Completion Summary
Threaded `phase`/`agent` string literals through `writeSidecar(seq, phase, agent)` at all 10
`implement-ticket.js` call sites and the Scope-phase resume-branch inline sidecar write, so
`tools.jsonl` rows written during a live workflow run now carry non-null `phase`/`agent` fields
matching the phase/agent producing them — unblocking a live dashboard's in-progress-run indicator.
`post_tool_hook.py` reads and persists the two new nullable fields using the same fail-open
`try/except`-wrapped pattern as `run_id`/`seq`. All affected tests (across three files, one beyond
the plan's original enumeration — see Implementation Notes) pass; `docs/agent-monitoring/schema.md`
documents the new fields with the standard nullable/no-backfill convention. No Mechanics Bible
chapter applies (orchestration tooling only). The Parity phase appended `INFRA-281` to
`docs/parity_ledger/infrastructure.yaml`, status `verified`, citing the two new tests as
`test_path` evidence. All gates (Review, Architecture-Verify, Test, Parity, Security-Review,
Verify) passed. Finalize regenerated `docs/REGISTRY.yaml` via `make docs-registry`.
