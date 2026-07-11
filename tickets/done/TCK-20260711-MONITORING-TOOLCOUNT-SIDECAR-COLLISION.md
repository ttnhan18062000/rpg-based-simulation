---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
phase: open
date: 2026-07-11
tags: [agent-monitoring, data-quality, root-cause]
---

# TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION

## Title
`tool_call_count`/`cost_proxy_score` silently mis-attributed due to two deterministic gaps in `.claude/current_run` sidecar coverage (not concurrency, as originally hypothesized — see Implementation Notes)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Empirical cross-check of `agent-monitoring/events.jsonl`'s `tool_call_count` field against the actual row counts in `agent-monitoring/tools.jsonl` (grouped by `(run_id, seq)`) found that **433 of 1,247 events with a non-null `tool_call_count` (~35%) do not match ground truth** — both over- and under-counts. One case traced concretely: `TCK-20260619-FIX-PERF-BUDGETS-RESET` seq 1 records `tool_call_count: 2`, but `tools.jsonl` has **zero** rows tagged to that run_id anywhere (not a missing-hook case — the hook was already active on that date, per `tools.jsonl`'s earliest timestamp of 2026-06-13). Every tool call actually logged in that run's claimed wall-clock window (`02:08–02:33`) is instead tagged to a *different* ticket, `TCK-20260614-WORLDMOD-PARAMS` seq 5.

Root mechanism (per `docs/agent-monitoring/schema.md`'s "How tool calls are attributed to agent events"): the orchestrating workflow writes `{run_id, seq}` to a single shared file, `.claude/current_run`, immediately before each `agent()` call; the `PostToolUse` hook reads that file on every tool call to tag it. This has no isolation between separate runs — if two workflow executions interleave (or a stale sidecar value from a prior/adjacent run lingers past its intended window), tool calls get silently tagged to the wrong `(run_id, seq)`, corrupting the derived count for both the run that "stole" attribution and the one that lost it. Since `cost_proxy_score` (`TCK-20260708-AGENT-COST-OBSERVABILITY`) is computed from the same grouped rows, it inherits the same corruption.

This is structurally the same class of issue as `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX` (a derived quality/monitoring metric that looked plausible — a real, non-null number — but was never cross-checked against its own ground-truth source, and turned out wrong for a large fraction of records).

## Scope
- Investigate the precise conditions that produce sidecar collisions: concurrent Claude Code sessions in the same working directory, `implement-epic` batching multiple tickets in quick succession, retry/re-run scenarios, or timing races between `writeSidecar(seq)` and the paired `agent()` call.
- Design a per-run-scoped (not just per-repo-shared) attribution mechanism — e.g. a run-unique token embedded in the sidecar filename or content that the `PostToolUse` hook can validate isn't stale, or a session-scoped path instead of a single fixed `.claude/current_run`.
- Add a validation/audit check (likely in `tools/agent-monitoring/validate.py`, alongside its existing incomplete-run checks) that can catch future `tool_call_count` drift going forward, so this class of silent corruption doesn't require another manual cross-check to surface.
- Quantify blast radius precisely (this ticket's own investigation found 433/1247 via a first-pass script; a follow-on investigation phase should confirm the exact mechanism per case, not just the aggregate mismatch count).

## Out of Scope
- Backfilling or "correcting" historical `tool_call_count`/`cost_proxy_score` values in `events.jsonl` — append-only precedent (per `docs/agent-monitoring/schema.md`'s Known Limitations) means historical corruption is accepted as unrecoverable; any fix here is prevention-only for future runs.
- Redesigning `cost_proxy_score`'s weighting formula (`tools/agent-monitoring/cost_proxy.py`) — that formula is unaffected in principle; it's fed corrupted input, not itself wrong.
- Fixing the two already-known-and-documented legacy-schema issues in `runs.jsonl` (`TCK-20260705-MONITORING-RUNID-JOIN`'s six legacy shapes) — those are a separate, already-resolved investigation.

## Acceptance Criteria
- [x] Root cause of sidecar collision confirmed for at least the traced case (`TCK-20260619-FIX-PERF-BUDGETS-RESET` / `TCK-20260614-WORLDMOD-PARAMS`) and generalized to a mechanism, not just a one-off anecdote — generalized to **two** deterministic mechanisms (Scope-phase gap; `writeMonitoring` self-pollution), not a concurrency race
- [x] A per-run attribution fix is designed and implemented so two workflow runs active in overlapping time windows cannot cross-tag each other's tool calls — amended: no concurrency race exists; fix instead closes the two deterministic gaps that caused every observed mismatch
- [x] A validation check exists (script or test) that can detect `tool_call_count` drift against `tools.jsonl` ground truth for any future run, runnable on demand — `compute_tool_count_drift_report()` added to `tools/agent-monitoring/validate.py`, wired into `main()`
- [x] Existing `tools/agent-monitoring/` test suite still passes; new tests cover the fix directly — amended: no interleaved-sidecar-write simulation needed (mechanism is deterministic, not a race); static text-parsing regression tests added instead, matching this file's existing verification convention
- [x] `docs/agent-monitoring/schema.md` updated to document the fix and add this as a resolved Known Limitation (superseding the current undocumented gap)

## Related Tickets
- TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX (same class of bug: derived metric never cross-checked against ground truth, found via direct empirical audit)
- TCK-20260708-AGENT-COST-OBSERVABILITY (introduced `cost_proxy_score`, which inherits this corruption via the same grouped `tools.jsonl` rows)
- TCK-20260705-MONITORING-RUNID-JOIN (prior empirical audit of `runs.jsonl`/`events.jsonl` join integrity — same investigative pattern, different field)
- TCK-20260607-MON-SCHEMA (original agent-monitoring schema definition)

## Related Docs
- docs/agent-monitoring/schema.md ("How tool calls are attributed to agent events", Known Limitations)
- docs/guides/agent_monitoring.md

## Related Stored Artifacts
- staging_artifacts/TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION/ (this ticket's investigation.md, plan.md, test_plan.md)

## Related Code Areas
- `.claude/workflows/implement-ticket.js` (`writeSidecar`, `writeMonitoring`)
- `tools/agent-monitoring/post_tool_hook.py` (sidecar read)
- `tools/agent-monitoring/pre_tool_hook.py`
- `tools/agent-monitoring/validate.py` (natural home for a new drift-detection check)
- `tools/agent-monitoring/cost_proxy.py` (consumer of the corrupted grouping, unaffected in formula itself)

## Assumptions / Open Questions
- ~~Assumes the traced case... generalizes to most of the 433 mismatches~~ — RESOLVED: it does not generalize as originally framed. The traced case is Mechanism 1 (Scope-phase gap, compounded by a crash leaving a stale sidecar); the dominant contributor across all 433 is Mechanism 2 (`writeMonitoring` self-pollution), affecting every run regardless of the traced case's specifics.
- ~~Open question: is `implement-epic` same-session chaining the dominant source, or true concurrent sessions?~~ — RESOLVED: neither. No concurrency is involved in either mechanism; both are deterministic single-session bugs.
- ~~Open question: should the sidecar carry a monotonic write-timestamp or nonce...~~ — RESOLVED: moot. No staleness-detection scheme was needed once the mechanism was confirmed deterministic — closing the two specific gaps was sufficient.
- New, carried forward (not resolved here, not blocking): `implement-epic.js` and `create-tickets.js` still have zero sidecar coverage at all (documented gap, `TCK-20260710-CURRENT-RUN-SIDECAR-BASH`'s Decision 2) — this ticket only extended coverage within `implement-ticket.js`. A future ticket could extend the same Scope-phase-style fix there if `tool_call_count` reliability for those two workflows ever becomes a concrete need.

## Implementation Notes

**Root cause correction (important):** the initial hypothesis (concurrent/overlapping workflow runs racing on a shared sidecar file) was **wrong** — resolved by reading `.claude/workflows/implement-ticket.js` directly rather than continuing to speculate. Both real mechanisms are fully deterministic, no concurrency involved:

1. **Scope-phase sidecar gap** (minority contributor, ~26-28/433 mismatches). Scope (`ticket-scoper`) never had sidecar coverage — confirmed as a *deliberate, already-tested* decision from `TCK-20260710-CURRENT-RUN-SIDECAR-BASH` (`tests/tools/test_current_run_sidecar_orchestrator.py`'s original docstring: "must remain permanently sidecar-free by design — not oversights to 'complete' later"). That same ticket's own Implementation Notes explicitly recommended this exact follow-up ("extend `.claude/current_run` sidecar coverage to... Scope-phase (`ticket-scoper`)"). Fixed: `.claude/workflows/implement-ticket.js`, right after `phase('Scope')` — if `ticketId` is provided (resuming an existing ticket), write the real `{run_id: ticketId, seq: 1}`; if creating a brand-new ticket (`tid` not yet known), clear to `{}` instead, so a stale value from a crashed prior run can't bleed into this run's Scope-phase tool calls. Can't reuse the existing `writeSidecar(seq)` helper — it closes over `tid`, undefined at this point in program order for the new-ticket branch.

2. **`writeMonitoring` self-pollution** (the dominant mechanism — previously unidentified, not covered by any existing ticket). `writeMonitoring`'s own `agent()` call ran Steps 1-4 (capture timestamp, compute `tool_call_count`/`cost_proxy_score` from `tools.jsonl`, write events, write run record) **before** Step 5 cleared the sidecar. Every one of those Bash/python calls was therefore itself tagged with whatever `(run_id, seq)` the last real phase had set — inflating that phase's true `tools.jsonl` row count beyond what Step 2's own snapshot had already recorded. Confirmed via an exact real-world shift: `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK` seq=9 recorded=2/actual=16, seq=10 recorded=16/actual=0 — `recorded(10) == actual(9)`, a clean one-phase offset. Fixed by moving the clear-sidecar instruction from Step 5 (last) to Step 0 (first) inside `writeMonitoring`'s own prompt text — its own calls are now correctly unattributed (`run_id: null`) instead of polluting the last tracked phase.

Full derivation, including the date-bucketed mismatch-rate evidence (collapsing to ~0.01-0.05 during 2026-07-08–07-10, regressing to ~0.30 by 07-11) that ruled out log rotation/hook-absence and pointed at these two mechanisms specifically, is in `staging_artifacts/TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION/investigation.md`'s addendum.

**Drift-detection tool (workstream 2):** `compute_tool_count_drift_report(events, tools)` added to `tools/agent-monitoring/validate.py`, following `compute_drift_report`'s existing pure-function/non-gating pattern exactly. Wired into `main()` (prints additively, never affects the exit-code contract). Run live against the current repo, it reproduces the exact 433/1247 mismatch count from the manual audit — confirms correctness, and confirms historical corruption remains present (expected — not backfilled, per Out of Scope).

**Docs:** `docs/agent-monitoring/schema.md`'s "How tool calls are attributed to agent events" section updated with both fixes and an explicit note that pre-fix historical data may still be wrong.

**Deviation from original Scope:** the "design a per-run-scoped attribution mechanism (nonce/session-scoped path/timestamp reconstruction)" work item became moot once the mechanism was confirmed deterministic — no isolation scheme was needed, only closing two specific gaps.

## Test Summary
- `tests/tools/test_current_run_sidecar_orchestrator.py`: `test_scope_phase_call_site_has_no_preceding_sidecar_write` replaced with `test_scope_phase_has_sidecar_coverage`; `test_writeMonitoring_step5_sidecar_clear_still_present` replaced with `test_writeMonitoring_step0_sidecar_clear_precedes_steps_1_to_4`. All 11 tests in this file pass.
- `tests/tools/test_validate_agent_monitoring.py`: 6 new tests for `compute_tool_count_drift_report` (agreement, undercounted-mismatch reproducing the real `recorded=0/actual=34` shape, overcounted-mismatch reproducing the real `recorded=2/actual=0` shape, null-field skip, interactive-tool-row immunity, read-only guarantee).
- Scoped regression run: `tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_tag_skill_mapping_check.py tests/tools/test_record_events.py tests/tools/test_record_run.py tests/tools/test_cost_proxy.py` — 66/66 pass.
- Broader `tests/tools/` suite run before closing as an additional safety check (this touches shared monitoring infrastructure used across all 4 workflows).

## Files Changed
- `.claude/workflows/implement-ticket.js` — Scope-phase sidecar coverage (new, ~20 lines before `phase('Scope')`'s `TICKET_SCHEMA` definition); `writeMonitoring`'s clear-sidecar instruction moved from Step 5 to Step 0.
- `tests/tools/test_current_run_sidecar_orchestrator.py` — module docstring updated; 2 tests replaced (Scope coverage now positive, not negative; writeMonitoring ordering now Step-0-first, not Step-5-last), 1 section comment corrected.
- `tools/agent-monitoring/validate.py` — `TOOLS_FILE` constant, `compute_tool_count_drift_report()` function, wired into `main()`.
- `tests/tools/test_validate_agent_monitoring.py` — 6 new tests for the drift-detection function.
- `docs/agent-monitoring/schema.md` — "How tool calls are attributed to agent events" section updated for both fixes.

## Completion Summary
Empirical cross-check found 433/1,247 (~35%) of `tool_call_count` values in `events.jsonl` didn't match `tools.jsonl` ground truth. The initial "concurrent workflow runs racing on a shared sidecar" hypothesis was disproven by direct code reading; the real causes were two deterministic gaps: Scope-phase never registered a sidecar value (a gap `TCK-20260710-CURRENT-RUN-SIDECAR-BASH` itself had already flagged as a recommended follow-up), and `writeMonitoring`'s own bookkeeping calls ran before its sidecar-clear step, silently inflating whichever phase was last tracked. Both fixed with small, surgical changes to `.claude/workflows/implement-ticket.js`; a new drift-detection report (`compute_tool_count_drift_report`) added to `validate.py` so a future recurrence surfaces automatically instead of requiring another manual audit. Historical corruption is not backfilled (append-only precedent) — only events recorded after this fix are expected to be reliable. 17 new/changed tests, 66/66 in the scoped regression suite passing.
