---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-COST-PROXY-WRITE-PATH
artifact_type: investigation
tags: []
---

# Investigation — TCK-20260719-COST-PROXY-WRITE-PATH

## Current Behavior

`tool_call_count`/`cost_proxy_score` are populated by an LLM-executed `agent()` call —
`.claude/workflows/implement-ticket.js`'s `writeMonitoring` function (`:258-320` before this
ticket). Its Step 2 instructed the agent to run an inline `python3 -c` script scanning
`agent-monitoring/tools.jsonl` for rows matching the run's `run_id`, group by `seq`, and compute
per-seq counts/scores via `cost_proxy.py::compute_cost_proxy_score`, saving the result as
`TOOL_STATS`; Step 3 then instructed the agent to substitute those values into each event object
before calling `record_events.py --data`. `record_events.py` itself (`tools/agent-monitoring/
record_events.py`, before this ticket) was a dumb writer — `validate_record()` checks only the 7
`REQUIRED` fields (`run_id`, `seq`, `ts`, `phase`, `agent`, `summary`, `status`); `tool_call_count`/
`cost_proxy_score` were accepted as opaque additive keys and written through unchanged, whatever
the caller supplied.

Confirmed via direct live-data measurement (not assumed): scoped to `ts > 2026-07-11T14:32:38Z`
(the landing timestamp of `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`, the last prior fix
to this same subsystem) for `workflow=implement-ticket` events — **36.7% of 562 events null for
`cost_proxy_score`, 29.5% null for `tool_call_count`**, spanning 37 distinct tickets. 30 of those 37
affected runs show **all-or-nothing** nulls (every event in the run null, or none), consistent with
a per-run compute step failing wholesale (the LLM either skips/mistranscribes the whole Step 2/3
sequence for that run) rather than per-event flakiness.

`duration_s` (a sibling field, same class of bug) was checked in the same pass: scoped to
`start_ts > 2026-07-09T08:39:45Z` (`TCK-20260709-AGENT-MONITORING-DURATION`'s real landing),
coverage is **114/115 = 99.13%**, single miss is a genuinely `IN_PROGRESS` run with no `end_ts`
yet — already resolved, confirmed via `record_run.py::compute_duration_s()` already computing it
deterministically at write time (that ticket's own fix). No code change needed for `duration_s`.

## Mechanics/Engine Constraints

None — agent-monitoring is orchestration/observability tooling, not simulation gameplay. No
Mechanics Bible chapter or Engine Contract applies. `docs/parity_ledger/infrastructure.yaml` is the
correct ledger file (matches `INFRA-274`/`INFRA-281`'s precedent for orchestrator-side
`implement-ticket.js` tooling changes with no Mechanics Bible chapter).

## Parity Ledger Overlap

`INFRA-281` (just-landed sibling ticket `TCK-20260719-LIVE-PHASE-AGENT-LABEL`) touches the same
`writeSidecar`/`.claude/current_run` mechanism but a different concern (phase/agent labeling on
`tools.jsonl` rows, not `cost_proxy_score`/`tool_call_count` computation reliability) — no direct
overlap, but both entries live in `infrastructure.yaml` and both cite `implement-ticket.js`.
`INFRA-263/264/265/277/278/279/280` are the established precedent pattern for
monitoring/dashboard-tooling entries with `support_boundary: "no simulation behavior involved"`.

## Prior Work

`TCK-20260708-AGENT-COST-OBSERVABILITY` — shipped `cost_proxy_score`, `cost_proxy.py`'s formula,
and the original `writeMonitoring` LLM-computed Step 2/3 pattern this ticket now replaces.
`TCK-20260709-AGENT-MONITORING-DURATION` — fixed the exact same class of bug for `duration_s`, by
moving its computation into `record_run.py::compute_duration_s()`, always overriding any
caller-supplied value. This ticket's fix is a direct structural mirror of that precedent, applied
to `record_events.py` instead of `record_run.py`.
`TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` — fixed two upstream sidecar-attribution
bugs (Scope-phase never had sidecar coverage; `writeMonitoring`'s own bookkeeping calls ran before
its sidecar-clear step) that caused wrong `tool_call_count` even when TOOL_STATS *was* computed —
orthogonal to this ticket's finding (LLM step sometimes not computing at all, wholesale).

## Risks and Open Questions

None outstanding — the LLM-computed-step anti-pattern and its fix are unambiguous, directly
mirroring an already-shipped, already-proven precedent (`compute_duration_s`).

**Found but explicitly out of scope**: `.claude/workflows/simq-audit.js` has its own, separate
inline TOOL_STATS-style compute step (own "Step 2 — compute tool_call_count per agent seq from
tools.jsonl") — the same anti-pattern, but this ticket's Related Code Areas and root-cause
measurement are scoped to `implement-ticket` workflow events only. Not fixed here; noted as a
real, known instance for a future ticket.

## Anti-Drift Hazards

- The new deterministic compute must be gated on `infer_workflow(run_id) == "implement-ticket"`
  (via `tools/agent-monitoring/vocabulary.py`) — NOT unconditionally applied to every record, or
  `implement-epic`/`create-tickets` events (which never register a sidecar) would gain a spurious
  `tool_call_count=0`/`cost_proxy_score=0.0` instead of staying absent, silently breaking their
  documented "100% missing, no sidecar" contract.
- Must reuse `cost_proxy.py::compute_cost_proxy_score` unchanged — never re-derive the formula a
  second time in `record_events.py`.
- Must always override a caller-supplied value for implement-ticket records (never trust it, even
  partially) — the whole point is removing dependence on LLM-transcription correctness.
