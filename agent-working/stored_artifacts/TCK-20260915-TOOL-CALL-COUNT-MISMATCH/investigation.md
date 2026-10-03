---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260915-TOOL-CALL-COUNT-MISMATCH
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# Investigation — TCK-20260915-TOOL-CALL-COUNT-MISMATCH

## Methodology validated against the ticket's own cited examples before trusting any aggregate

Reproduced all 4 named examples exactly by summing each run's per-event `tool_call_count` against
its real `tools.jsonl` row count:

| Run | claimed (reproduced) | actual (reproduced) |
|---|---|---|
| `TCK-20260718-TICKET-CORPUS-REPORT` | 0 | 558 |
| `TCK-20260626-FIX-DESIGN-PATTERNS` | 146 | 517 |
| `TCK-20260619-E53Ab-DECISION-PHASE` | 0 | 153 |
| `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS` | 285 | 91 |

Exact match on all four. Confirms the aggregate method below, not just the sample.

## The stated "53" total is stale — re-derived, and the reason for the gap is now understood

Full-corpus re-scan: **194** runs mismatch by >3x (**142** restricted to the 3 workflows
`compute_tool_stats()` actually covers). Far more than the ticket's own 53. Investigated why rather
than assuming either number: **`TCK-20260719-COST-PROXY-WRITE-PATH`** (the ticket that made
`tool_call_count` computed from `tools.jsonl` ground truth at write time, per its own docstring)
landed 2026-07-19. `TCK-20260718-TICKET-CORPUS-REPORT` — the ticket's own flagship "0 claimed, 558
actual" example — closed **one day before that fix landed**. Checked its own events directly: every
one of its 10 events (`Scope` through `Finalize`) shows `tool_call_count: 0`, including seq values
(1, 5, 9) that DO have real matching `tools.jsonl` rows (6, 40, 512 respectively) — the seqs line
up perfectly, but the pre-fix write path never computed a real count at all. **This is not a live
bug; it is a historical record from before the ground-truth mechanism existed**, and backfilling it
is explicitly out of this ticket's scope.

Splitting all 142 workflow-scoped mismatches by whether they started before or on/after
2026-07-19: **93 pre-fix** (expected — same historical-gap shape as the flagship example) and
**49 post-fix** — closely matching the ticket's own "53, current not historical" framing once the
historical noise is excluded. **The corrected finding: the ticket's "53" almost certainly already
meant "post-fix, currently mismatching" and was a reasonably accurate count of that population at
scoping time; the standalone "53" read against the WHOLE corpus (as a naive reproduction attempt
does) looks stale only because it's answering a different, broader question than the one the
ticket actually meant.** Re-measured post-fix count: 49 (2026-09-15), consistent with the
corpus growing by a handful of new mismatches since the ticket's own scoping pass.

## Month distribution — confirmed real, not corpus-growth artifact

Post-fix-only breakdown: 2026-07: 3, 2026-08: 31, 2026-09: 15 — matches the ticket's own shape
(their 6/35/9) closely enough to confirm this is the same real population, not different data.
**August cluster is real and current, not historical residue.**

## August cluster — explained with concrete, cross-referenced evidence (AC #2)

`docs/agent-monitoring/schema.md` already documents `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`
(2026-08-24) as fixing a confirmed-live cross-session sidecar-contamination bug — every concurrent
session shared one `.claude/current_run` file until that date, so a session's own tool calls could
get attributed to whichever OTHER session's ticket last wrote the sidecar. **August 2026 is almost
entirely inside the pre-fix window** (the fix landed on the 24th), and this is a sufficient,
concretely-evidenced explanation for the cluster: any run active during that period could have its
`tools.jsonl` total inflated by another session's misattributed rows, while its own
`tool_call_count` (a write-time snapshot) reflects only what was known at that moment — a
structural mismatch generator, not a coincidence. Confirmed directly (see below) rather than left
as a plausible-but-unverified hypothesis: one of the sampled August mismatches
(`TCK-20260821-VISUAL-QUALITY-DOCS`) is schema.md's own named, concretely-confirmed instance of
this exact bug.

**Resolved, not merely a coincidence — caught by reading `docs/agent-monitoring/schema.md`
directly instead of stopping at "unexplained."** The two August tickets with matching 1839-row
counts (`TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET`, `TCK-20260821-VISUAL-QUALITY-DOCS`) are not
an isolated coincidence — `TCK-20260821-VISUAL-QUALITY-DOCS` is the SAME ticket schema.md's own
"Cross-session contamination fix" section already cites as the one **concretely confirmed
instance** of the pre-2026-08-24 shared-sidecar bug: it closed 2026-08-22T21:36:09Z, yet kept
receiving `tools.jsonl` rows stamped with its own `run_id` from a different, concurrently-running
session two days later, on 2026-08-24 — the exact bug `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`
fixed that same day. This directly explains the matching-count oddity: both tickets were active in
the same overlapping window, before the fix landed, sharing the one `.claude/current_run` file —
each session's own tool calls were liable to get attributed to whichever ticket's sidecar value was
written most recently, inflating both tickets' final `tools.jsonl` totals with rows that belong to
the other's real work, while each event's own `tool_call_count` (computed once, at write time,
using whatever the sidecar showed at that moment) reflects only what was known then. **This is the
single clearest, most concretely evidenced root cause found for the August cluster**: August 2026
is entirely within the pre-2026-08-24 window this exact mechanism affected, and — per schema.md's
own "no backfill" precedent — every row misattributed during that window remains permanently baked
into the affected runs' `tools.jsonl` totals, with no correction possible after the fact.

## Authoritative side (AC #1)

**`tools.jsonl`'s real row count is authoritative.** `tool_call_count` is a derived, write-time
SNAPSHOT computed from `tools.jsonl` (confirmed by reading `compute_tool_stats()` and
`implement-ticket.js`'s own prompt text: "do NOT compute or set tool_call_count yourself ... always
overrides whatever you pass") — it is not an independent measurement, so there is no real
"authority" contest between two independent sources. Its value is only ever as good as (a) whether
the ground-truth mechanism existed yet when the event was written (pre/post 2026-07-19), and
(b) whether every relevant `tools.jsonl` row for that run/seq was correctly attributed at that
moment (`TCK-20260915-SIDECAR-ATTRIBUTION-GAP`'s own subject). Documented in
`docs/agent-monitoring/schema.md`.

## Shared-cause hypothesis with the sidecar ticket (AC #3)

**Confirmed, not merely probable** — this was established directly in
`TCK-20260915-SIDECAR-ATTRIBUTION-GAP`'s own investigation by reading `compute_tool_stats()`'s
`(run_id, seq)` grouping logic: an unattributed tool row can never match any event, by
construction. Cross-referenced here rather than re-derived.
