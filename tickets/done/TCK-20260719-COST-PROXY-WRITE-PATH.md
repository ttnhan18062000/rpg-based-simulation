---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260719-COST-PROXY-WRITE-PATH
phase: done
date: 2026-07-19
tags: []
---

# TCK-20260719-COST-PROXY-WRITE-PATH

## Title
Move TOOL_STATS compute out of writeMonitoring's LLM step into record_events.py

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Investigation (not just an audit) found duration_s coverage is already resolved: scoped to start_ts > 2026-07-09T08:39:45Z (TCK-20260709-AGENT-MONITORING-DURATION's real landing), coverage is 114/115 = 99.13%, with the single miss being an expected IN_PROGRESS run with no end_ts yet — close as non-issue, no code change. However, cost_proxy_score/tool_call_count remain a real, confirmed, ongoing gap: scoped to ts > 2026-07-11T14:32:38Z (TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION's landing) for workflow=implement-ticket, 36.7% of 562 events are still null for cost_proxy_score and 29.5% null for tool_call_count, spanning 37 distinct tickets from 2026-07-11 through today, with 30 of 37 affected runs showing all-or-nothing nulls (consistent with a per-run compute step failing wholesale, not per-event flakiness). Root cause confirmed by direct code read: writeMonitoring (.claude/workflows/implement-ticket.js:258-320) is an LLM-executed agent() call that computes TOOL_STATS via an inline python3 -c command and substitutes values into each event before calling record_events.py --data; record_events.py itself is a dumb writer with no compute logic. This is the exact LLM-bookkeeping-determinism anti-pattern already fixed for duration_s (moved into record_run.py) and sidecar registration (moved to orchestrator bash()), but never extended to cost_proxy_score/tool_call_count. Fix moves the compute into deterministic code in record_events.py, mirroring record_run.py's compute_duration_s precedent.

## Scope
- Move TOOL_STATS computation (cost_proxy_score, tool_call_count) out of writeMonitoring's LLM-executed agent() prompt in .claude/workflows/implement-ticket.js
- Implement deterministic computation of both fields in tools/agent-monitoring/record_events.py at write time from tools.jsonl, mirroring record_run.py's compute_duration_s precedent
- Preserve fail-silent/non-blocking monitoring-write behavior per CLAUDE.md hard rule (monitoring write failure must never fail the workflow)
- Add test asserting record_events.py populates both fields correctly without relying on caller-supplied/LLM-transcribed values

## Out of Scope
- implement-epic/create-tickets — 100% missing for both fields by documented, deliberate design (no sidecar registered); this is not a bug and stays out of scope
- Historical backfill of already-written null records in agent-monitoring/events.jsonl (fix is forward-looking only, no-backfill precedent)
- duration_s — already resolved at 99.13% coverage, no action needed beyond documenting it as closed

## Acceptance Criteria
- [ ] Ticket body records duration_s as already resolved: 114/115 = 99.13% coverage scoped to start_ts > 2026-07-09T08:39:45Z, single miss is an expected in-progress run; no code change made for duration_s
- [ ] Ticket body records the confirmed real gap: 36.7% null cost_proxy_score, 29.5% null tool_call_count across 562 implement-ticket events scoped to ts > 2026-07-11T14:32:38Z, spanning 37 tickets, with an all-or-nothing per-run null pattern
- [ ] TOOL_STATS compute/substitution logic removed from writeMonitoring's agent()-executed prompt in .claude/workflows/implement-ticket.js
- [ ] record_events.py computes cost_proxy_score and tool_call_count deterministically from tools.jsonl at write time instead of relying on caller-supplied values
- [ ] New test in tests/tools/test_record_events.py asserts deterministic computation (not passthrough) of both fields
- [ ] Regression test confirms implement-epic/create-tickets events remain unaffected (fields stay absent/null as documented, no sidecar)
- [ ] Monitoring write failure still never fails the workflow (fail-silent behavior preserved end to end)

## Related Tickets
- TCK-20260708-AGENT-COST-OBSERVABILITY
- TCK-20260709-AGENT-MONITORING-DURATION
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
- TCK-20260710-CURRENT-RUN-SIDECAR-BASH

## Related Docs
- docs/agent-monitoring/schema.md
- docs/plans/archive/agent_infrastructure/idea_agent_bookkeeping_determinism.md
- CLAUDE.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/cost_proxy.py
- tests/tools/test_record_events.py
- tests/tools/test_record_run.py

## Assumptions / Open Questions
- Fix only benefits future runs — the historical 2026-07-11-to-today null gap in already-written records is permanent and will not be backfilled
- Sample size is modest (562 events / 37 runs) but the all-or-nothing per-run pattern was directly observed via code read, not statistically inferred, so root cause confidence is high despite sample size

## Implementation Notes
Added `record_events.py::compute_tool_stats(records)` — reads `agent-monitoring/tools.jsonl` once
per batch, builds `{(run_id, seq): (tool_call_count, cost_proxy_score)}` for every `(run_id, seq)`
pair whose `run_id` belongs to the `implement-ticket` workflow (via `vocabulary.py`'s
`infer_workflow`), reusing `cost_proxy.py::compute_cost_proxy_score` unchanged. Wired into `main()`
right before the write block: for each record whose `(run_id, seq)` key is in the computed stats,
`tool_call_count`/`cost_proxy_score` are always overwritten — mirrors `record_run.py`'s
`compute_duration_s` "always overrides any caller-supplied value" precedent exactly. Records for
any other workflow (or an implement-ticket record with no matching key, which can't happen since
every implement-ticket `(run_id, seq)` is included) are left completely untouched — no key added
if not already present, preserving `implement-epic`/`create-tickets`'s documented "100% missing,
no sidecar" behavior.

`.claude/workflows/implement-ticket.js`'s `writeMonitoring` prompt: removed the old Step 2 (an
inline `python3 -c` TOOL_STATS compute + substitution instruction), renumbered the remaining steps
0→3, and added an explicit "do NOT compute tool_call_count/cost_proxy_score yourself" instruction
to the new Step 2 (build and write events) so an agent following this prompt doesn't try to
re-derive what `record_events.py` now computes deterministically.

**Found but explicitly out of scope**: `.claude/workflows/simq-audit.js` has its own, separate
inline TOOL_STATS-style compute step (its own "Step 2 — compute tool_call_count per agent seq from
tools.jsonl") — the exact same anti-pattern, but not touched here since this ticket's Related Code
Areas and root-cause investigation are scoped to `implement-ticket` workflow events specifically.
`compute_tool_stats()`'s `infer_workflow(...) == "implement-ticket"` gate means simq-audit run_ids
(`SIMQ-AUDIT-...` prefix) are never touched by this change — zero regression risk to that workflow,
but its own LLM-computed TOOL_STATS step remains unfixed. Worth a future ticket.

`docs/agent-monitoring/schema.md` updated: `tool_call_count`/`cost_proxy_score` field descriptions,
the cost_proxy_score formula section, the create-tickets/implement-epic phase-values note, and the
"How tool calls are attributed to agent events" prose all corrected from "computed by
`writeMonitoring`" to "computed deterministically by `record_events.py`" — a real doc-accuracy fix,
not just new-field documentation, since the compute location genuinely moved.

**Existing test updated, not just left to coincidentally pass**:
`tests/tools/test_record_events.py::test_cost_proxy_score_field_written_to_events_jsonl` asserted
the OLD pass-through behavior (a caller-supplied `cost_proxy_score=42.5` written unchanged) — that
is precisely the anti-pattern this ticket fixes, so it was replaced with
`test_cost_proxy_score_and_tool_call_count_computed_from_real_tools_jsonl_not_passthrough`, which
supplies a deliberately wrong caller value (999999.0) alongside real `tools.jsonl` fixture rows and
asserts the written value is the hand-computed real one (3.0), not the caller's.
`tests/tools/test_current_run_sidecar_orchestrator.py::test_writeMonitoring_step0_sidecar_clear_precedes_steps_1_to_4`
hardcoded the old "Step 2 — compute tool_call_count"/"Step 4 — write run record" literal strings —
renamed to `test_writeMonitoring_step0_sidecar_clear_precedes_other_steps` and updated for the new
4-step (0-3) numbering, plus added assertions that the old TOOL_STATS-compute text is genuinely
gone, not just renumbered around.

## Test Summary
- `python3 -m pytest tests/tools/test_record_events.py -q` — 19/19 passing (4 new: deterministic
  compute overriding a wrong caller value, absent-tools.jsonl zero-fallback, implement-epic/
  create-tickets non-interference via `compute_tool_stats()` directly, mixed-batch workflow
  targeting).
- `python3 -m pytest tests/tools/test_current_run_sidecar_orchestrator.py -q` — 12/12 passing (1
  renamed/updated for the new step numbering).
- `python3 -m pytest tests/tools/test_record_run.py tests/tools/test_cost_proxy.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_generate_retro.py tests/tools/test_step0_ts_orchestrator.py -q`
  — 86/86 passing, unmodified (regression guard — none of these should have been affected).
- `python3 -m pytest tests/tools/ -q -k "monitoring or record_events or record_run or cost_proxy or sidecar or agent_ops_dashboard"` — 137/137 passing.

## Files Changed
- tools/agent-monitoring/record_events.py (`compute_tool_stats()` + wiring into `main()`)
- .claude/workflows/implement-ticket.js (`writeMonitoring` prompt: TOOL_STATS step removed, steps
  renumbered, Step 0 comment updated for accuracy)
- docs/agent-monitoring/schema.md (compute-location descriptions corrected in 4 places)
- docs/parity_ledger/infrastructure.yaml (new entry INFRA-282)
- tests/tools/test_record_events.py (1 test replaced, 3 new)
- tests/tools/test_current_run_sidecar_orchestrator.py (1 test renamed/updated, 1 comment fixed)

## Completion Summary
`cost_proxy_score`/`tool_call_count` are now computed deterministically inside
`record_events.py::compute_tool_stats()` at write time, from real `agent-monitoring/tools.jsonl`
ground truth — always overriding any caller-supplied value for `implement-ticket` workflow records,
exactly mirroring `record_run.py`'s `compute_duration_s` precedent that already fixed the same
anti-pattern for `duration_s`. This closes the confirmed ~30-37% null-rate gap for events written
since 2026-07-11 (root cause: `writeMonitoring`'s old inline LLM-executed `python3 -c` compute step
failing wholesale per-run, not per-event flakiness) — going forward only, no historical backfill.
`duration_s` itself was confirmed already resolved (99.13% coverage) and required no code change.
`implement-epic`/`create-tickets` records remain completely unaffected (no sidecar, fields stay
absent, verified by a direct regression test). A second, separate instance of the same anti-pattern
was found in `simq-audit.js` but deliberately left unfixed — outside this ticket's stated scope.
