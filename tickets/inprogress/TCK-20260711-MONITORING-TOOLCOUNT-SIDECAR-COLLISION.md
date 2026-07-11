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
`tool_call_count`/`cost_proxy_score` silently mis-attributed across concurrent/overlapping workflow runs via shared `.claude/current_run` sidecar

## Status
OPEN

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
- [ ] Root cause of sidecar collision confirmed for at least the traced case (`TCK-20260619-FIX-PERF-BUDGETS-RESET` / `TCK-20260614-WORLDMOD-PARAMS`) and generalized to a mechanism, not just a one-off anecdote
- [ ] A per-run attribution fix is designed and implemented so two workflow runs active in overlapping time windows cannot cross-tag each other's tool calls
- [ ] A validation check exists (script or test) that can detect `tool_call_count` drift against `tools.jsonl` ground truth for any future run, runnable on demand (e.g. `make agent-monitoring-validate` or an extension of the existing `validate.py`)
- [ ] Existing `tools/agent-monitoring/` test suite still passes; new tests cover the collision scenario directly (e.g. simulate two interleaved sidecar writes and assert correct attribution)
- [ ] `docs/agent-monitoring/schema.md` updated to document the fix and add this as a resolved Known Limitation (superseding the current undocumented gap)

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
- Assumes the traced case (cross-attribution to a temporally-adjacent different ticket) generalizes to most of the 433 mismatches; this needs confirming across a larger sample before design work locks in a fix, rather than assuming every mismatch shares one root cause.
- Open question: is `implement-epic` (which chains multiple ticket runs in the same session) the dominant source of collisions, or do fully separate/concurrent Claude Code sessions in the same working directory also contribute? The fix shape differs (in-process sequencing bug vs. true multi-process race).
- Open question: should the sidecar carry a monotonic write-timestamp or nonce so the hook can detect and discard a stale read even without full per-run isolation, as a cheaper partial mitigation if full isolation proves complex?

## Implementation Notes
(Not yet implemented — ticket scoped and opened per user request; investigation/plan captured in staging artifacts below, full implementation deferred to a future session.)

## Test Summary
(Pending implementation.)

## Files Changed
(Pending implementation.)

## Completion Summary
(Pending implementation.)
