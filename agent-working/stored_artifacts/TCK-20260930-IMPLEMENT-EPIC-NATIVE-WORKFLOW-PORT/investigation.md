---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT
artifact_type: investigation
tags: [ai]
---

# Investigation

## The 11 sites (all bookkeeping, none decides a verdict)
| line | purpose | route |
|---|---|---|
| 34 | timestamp for the INVALID_ARGS record | args.start_ts |
| 37 | INVALID_ARGS run record | runMonitoringCommand (fail-open) |
| 87 | `captureTs()` before Discover | args.start_ts |
| 125 | `writeSidecar` (5 call sites) | runCommand + `WRITESIDECAR_EXIT:` marker, warn on failure |
| 148 | `clearSidecar` | runCommand + `CLEARSIDECAR_EXIT:` marker |
| 279, 305 | timestamps for the EPIC_CREATED / NOTHING_TO_DO records | args.start_ts |
| 283, 286, 310, 313 | event + run records on those two early exits | runMonitoringCommand |

## Nested workflow() (measured, zero-agent probe `wf_df41616a-229`, user opt-in 2026-10-01)
`workflow({scriptPath}, args)` works from a top-level script and passes args; inside that child `workflow()` throws "nesting is limited to one level". So implement-epic may call `workflow('implement-ticket', ...)`, but implement-ticket.js still has 38 `bash(` call sites and fails acorn at lines 182 and 1753, so the call cannot succeed today. Smallest viable fallback, implemented: the script reports `WORKFLOW_ERROR` for the child with an explicit instruction to dispatch children from the top-level session, and the SKILL keeps hand-translation as the primary path for epics with pending children until `TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT`.

## Real native run (user opt-in 2026-10-01; run `wf_18d6fbaa-844`)
`Workflow({scriptPath: '.claude/workflows/implement-epic.js', args: {folder: 'tickets/todos/zz-native-run-probe/', start_ts: '2026-10-01T02:53:44Z'}})` against a scratch folder holding one already-done ticket id (NOTHING_TO_DO path; folder removed afterwards).
- Result `{"status":"NOTHING_TO_DO","already_done":[...]}`, 5 agents (Discover + 4 runCommand: writeSidecar -1, two record writes, clearSidecar), 234,551 subagent tokens, 50.7 s, 11 tool uses.
- Records: run record `workflow:"implement-epic"`, `"execution_mode":"workflow"`, `final_status` NOTHING_TO_DO (shard `agent-monitoring/data/2026-W40/`).
- Attribution: 9 `tools.jsonl` rows at `seq -1` / `Discover` / `discover`, same session id as the orchestrating session, so the sidecar mechanism works under native execution. 5 rows are unattributed (`run_id: null`), the runCommand agents' own calls, as in the pilot.
- **Finding (fixed):** the event written for this early exit sits at `seq 1` and read `tool_call_count 0` / `cost_proxy_score 0.0` although Discover made 9 calls at `seq -1`: a false zero of the same class the cost-proxy confirmation found on child rows. `record_events.compute_tool_stats` now omits any positive-seq implement-epic row without tool rows (null), the old early-exit pin that asserted (0, 0.0) was wrong and is replaced.
- **Cost:** about 234k tokens for a run that did no implementation; the runCommand tax here is 4 dispatches on a path with 1 real agent.
- Not exercised: Implement (child loop), folder-cleanup, epic-close and tracking-doc agents; those need a child to run natively.
