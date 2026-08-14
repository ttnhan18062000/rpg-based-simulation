---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
artifact_type: investigation
tags: [agent-monitoring, data-quality, root-cause]
---

# Investigation — TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION

## Trigger

Follow-up to `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX` (search-eval harness silently reporting 0.00 due to an unverified fixture assumption). User asked whether a similar issue — a monitoring/quality signal that looks fine but was never cross-checked against ground truth — exists in agent tool-usage tracking specifically.

## Method

Direct empirical cross-check, not code reading alone: loaded every record in `agent-monitoring/events.jsonl` and `agent-monitoring/tools.jsonl`, grouped `tools.jsonl` rows by `(run_id, seq)`, and compared the actual row count against each event's recorded `tool_call_count`.

```python
import json
from collections import defaultdict

events = [json.loads(l) for l in open('agent-monitoring/events.jsonl') if l.strip()]
tools = [json.loads(l) for l in open('agent-monitoring/tools.jsonl') if l.strip()]

tool_counts = defaultdict(int)
for t in tools:
    if t.get('run_id') and t.get('seq') is not None:
        tool_counts[(t['run_id'], t['seq'])] += 1

# compare recorded event.tool_call_count against tool_counts[(run_id, seq)]
```

## Key Findings

### Finding 1 — 433/1247 (~35%) of checked events have a wrong `tool_call_count`

Of 2,708 total events, 236 have no `run_id`/`seq` at all (legacy shapes, excluded). Of the remaining 2,472, 1,247 have a non-null `tool_call_count` recorded. Comparing those 1,247 against actual `tools.jsonl` row counts: **433 mismatches**, in both directions:

```
(('TCK-20260614-CERT-SAFE-SERIAL', 9), recorded=22, actual=25)
(('TCK-20260614-WORLDSCEN-PERSPECTIVES', 8), recorded=0, actual=34)
(('TCK-20260619-FIX-PERF-BUDGETS-RESET', 1), recorded=2, actual=0)
... (430 more)
```

Both over-count and under-count cases rule out a simple monotonic explanation like "old tools.jsonl rows got pruned over time" (which would only ever produce `actual < recorded`, never `actual > recorded` or a real `recorded` value backed by zero real rows).

### Finding 2 — `tools.jsonl` itself has never been truncated or rotated

Checked out `agent-monitoring/tools.jsonl` at every commit that touched it (155 commits) and tracked line count over time — monotonically increasing throughout, no shrink event. This rules out log rotation/retention as the explanation; the file genuinely never had the "missing" rows.

### Finding 3 — traced one case to concrete cross-run attribution bleed

`TCK-20260619-FIX-PERF-BUDGETS-RESET` seq 1 event claims `tool_call_count: 2`, timestamped `2026-06-19T02:08:41Z` (event's own `ts`, and the run's `start_ts`/`end_ts` span `02:08:41`–`02:33:18`). `tools.jsonl` has **zero** rows anywhere tagged `run_id == "TCK-20260619-FIX-PERF-BUDGETS-RESET"`. Not a missing-hook explanation either — `tools.jsonl`'s earliest timestamp overall is `2026-06-13T17:23:37Z`, so the hook was already active six days before this run.

Checked what tool calls actually exist in `tools.jsonl` during that exact wall-clock window (`02:00`–`02:40` on 2026-06-19): 76 rows, **every one tagged `run_id: "TCK-20260614-WORLDMOD-PARAMS", seq: 5`** — a different ticket entirely. `TCK-20260614-WORLDMOD-PARAMS` has no corresponding `runs.jsonl` record at all (`start_ts`/`end_ts`/`final_status` all absent — matches one of the already-documented legacy shapes from `TCK-20260705-MONITORING-RUNID-JOIN`).

This is consistent with the sidecar-collision mechanism described in `docs/agent-monitoring/schema.md`'s "How tool calls are attributed to agent events": a single shared file, `.claude/current_run`, is written with `{run_id, seq}` immediately before each `agent()` call and read by the `PostToolUse` hook on every tool call. If a long-running phase (e.g. `TCK-20260614-WORLDMOD-PARAMS` seq 5, spanning at least the ~40 minutes covering `02:00`–`02:40`) is still in flight when a *different* ticket's workflow run starts and writes its own `{run_id, seq}` — or if the reverse ordering happens — tool calls occurring during the overlap get tagged to whichever sidecar value happened to be on disk at hook-execution time, not necessarily the run that actually issued them.

### Finding 4 — `cost_proxy_score` inherits the same corruption

`tools/agent-monitoring/cost_proxy.py`'s `compute_cost_proxy_score()` takes exactly the same `(run_id, seq)`-grouped `tools.jsonl` rows as input. The formula itself (`W_BASH * bash_ms + W_AGENT * agent_spawns + W_EDIT * edit_count`) is correct given its input — but since the input rows are the same corrupted grouping, any `cost_proxy_score` computed from a mismatched group is equally unreliable. Not independently re-verified numerically in this pass (would require re-deriving cost_proxy_score per event from raw tools.jsonl and diffing against the recorded value, same pattern as Finding 1) — flagged as a natural first step for the next investigation session.

## What this rules out

- **Not a hook-installation gap** — the hook was active well before the traced collision.
- **Not file truncation/rotation** — `tools.jsonl` line count only ever grew.
- **Not the already-documented legacy-schema issue** — `TCK-20260705-MONITORING-RUNID-JOIN` covered `runs.jsonl`/`events.jsonl` join completeness (is a run "missing" its end record), a different question from "is this event's derived count correct."

## Open questions carried into planning

- Is `implement-epic` (same-session ticket chaining) the dominant collision source, or do genuinely concurrent Claude Code sessions in the same working directory (two terminals, same repo) also contribute? Only one case was traced in depth; the fix shape differs materially between "in-process sequencing bug" and "true multi-process race," and this investigation did not have time to trace a second case to disambiguate.
- Sample size caveat: 1,247 events checked is the full available dataset (not a sample), so the 35% figure is exact for current data — but future runs could have a different rate depending on how often workflows overlap in practice.

---

## Addendum — root cause corrected (superseding the "concurrent sessions" hypothesis above)

The open question above was resolved by reading `.claude/workflows/implement-ticket.js` directly rather than continuing to speculate. **The "cross-run concurrency" framing above was wrong** — the real mechanisms are both fully deterministic, no concurrency required, and both traceable to specific lines:

### Mechanism 1 — Scope-phase never had sidecar coverage (confirmed pre-existing, deliberately deferred)

`tests/tools/test_current_run_sidecar_orchestrator.py`'s original docstring stated outright: "The two call sites that never had a sidecar instruction (Scope/`ticket-scoper`, and `writeMonitoring`'s own `agent()` call) must remain permanently sidecar-free by design — not oversights to 'complete' later." This was a **deliberate, already-tested decision** from `TCK-20260710-CURRENT-RUN-SIDECAR-BASH` — which itself recommended, as its own follow-up: "extend `.claude/current_run` sidecar coverage to call sites that have never had one — Scope-phase (`ticket-scoper`)..." This ticket **is** that recommended follow-up.

Consequence: every single ticket run's Scope-phase tool calls (search_docs, graphify, reading tickets/docs, drafting the new ticket) get attributed to whatever `.claude/current_run` last held — `{}`  (harmlessly null) if the previous run exited cleanly, or a **stale, wrong run_id** if the previous run crashed before reaching any `writeMonitoring` call (which is the only thing that clears the sidecar). Cross-checking mismatches by `seq`, only ~26-28 of 433 were `seq==1` (Scope) — a real but minority contributor, not the dominant one.

### Mechanism 2 — `writeMonitoring`'s own bookkeeping calls self-pollute the last tracked phase (the dominant mechanism, previously unidentified)

`writeMonitoring`'s own `agent()` call runs 5 steps: Step 1 (capture end timestamp), Step 2 (python script computing `tool_call_count`/`cost_proxy_score` from `tools.jsonl`, grouped by seq), Step 3 (write events), Step 4 (write run record), Step 5 (**clear** `.claude/current_run` to `{}`). Because Step 5 ran **last**, every one of Steps 1-4's own Bash/python invocations executed *before* the sidecar was cleared — meaning they were still tagged with whatever `(run_id, seq)` the last real phase (usually Finalize) had set. Step 2's snapshot is taken *before* Steps 3/4 run, so the recorded `tool_call_count` reflects the row count at that snapshot moment — but `tools.jsonl` keeps growing as Steps 2/3/4's own calls land under the same seq, so the *actual* count measured after the fact is always higher than what got recorded. Confirmed exactly via a real example: `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK` seq=9 (Verify) recorded=2, actual=16; seq=10 (Finalize) recorded=16, actual=0 — `recorded(seq=10) == actual(seq=9)`, an exact one-phase shift, consistent with writeMonitoring's own calls inflating whichever phase's bucket was still open when it ran.

Bucketing all 433 mismatches by date showed the rate collapsing to ~0.01-0.05 during 2026-07-08 to 2026-07-10 (post `TCK-20260708-AGENT-COST-OBSERVABILITY`, pre this fix) before regressing back to ~0.30 on 2026-07-11 — consistent with Mechanism 2 recurring on every single run regardless of concurrency, once enough runs accumulate.

### Why "concurrent sessions" was the wrong frame

The originally-traced case (`TCK-20260619-FIX-PERF-BUDGETS-RESET` cross-attributed to `TCK-20260614-WORLDMOD-PARAMS`) is explained by Mechanism 1: `TCK-20260614-WORLDMOD-PARAMS` has no `runs.jsonl` record at all (crashed before any `writeMonitoring` call ran), leaving its last sidecar value dangling indefinitely; the next run's Scope phase (`TCK-20260619-FIX-PERF-BUDGETS-RESET`) then inherited that stale value since Scope has no sidecar write of its own. No two workflows were actually running at the same time — a **crash** plus a **structural gap**, not a race.

### Fix implemented (see plan.md and the closed-out ticket's Implementation Notes for the final version)

1. Scope now writes a real `{run_id: ticketId, seq: 1}` sidecar value when resuming an existing ticket, or explicitly clears to `{}` when creating a brand-new one (ticket_id genuinely unknown at that point) — closing Mechanism 1's exposure window to zero at the top of every run.
2. `writeMonitoring`'s Step 5 (clear) was moved to Step 0 (runs first, not last) — closing Mechanism 2 entirely; its own bookkeeping calls are now correctly unattributed (`run_id: null`) instead of polluting the last real phase's count.
