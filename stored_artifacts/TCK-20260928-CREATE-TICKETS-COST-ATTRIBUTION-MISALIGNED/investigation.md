---
status: active
layer: observability
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED
date: 2026-09-28
tags: [agent-monitoring, data-quality]
---

# Investigation — TCK-20260928-CREATE-TICKETS-COST-ATTRIBUTION-MISALIGNED

## Method

Read `create-tickets.js`'s current source directly (writeSidecar, pushEvent, all 4 wired call
sites, writeMonitoring), compared it against `implement-ticket.js`'s own established sidecar
patterns (writeSidecar dual-write, the writeMonitoring "Step 0" sidecar clear), and read
`post_tool_hook.py`'s sidecar-resolution order. Cross-checked against `git log`/`git diff` for
`create-tickets.js` and `post_tool_hook.py` to date the relevant fixes relative to the two real
runs' own dates (2026-09-13, 2026-09-23).

## Anomaly 1 — 09-13 run: Structure attributed to seq 2, a phantom "Write/ticket-scoper" at seq 3

**Stale-script-version lead: RULED OUT.** `git diff 6ffeddcca..6441c9767 -- .claude/workflows/
create-tickets.js` (the only two commits touching this file between #141 2026-09-07 and #236
2026-09-22, spanning the 09-13 run) shows the *only* change to this file's sidecar/event logic is
a cosmetic summary-truncation-marker rewrite (`TCK-20260915-SIBLING-WORKFLOW-SUMMARY-TRUNCATION-
MARKERS`). The `events.length + 1` seq-numbering formula, and all 4 `writeSidecar()` call sites,
are byte-identical before and after 09-13. The code that ran on 09-13 computed seq exactly the
same way the current code does.

**Cross-session/cross-workflow contamination: CONFIRMED as the class, exact mechanism
UNCONFIRMABLE.** The agent literal `"ticket-scoper"` at seq 3 is unambiguous: `create-tickets.js`
never writes that agent name to any sidecar (grep-confirmed — its own 4 `writeSidecar()` calls use
`'comprehend'`/`'structure'`/`'write-sequence'`/`'link-epic'`). `"ticket-scoper"` is
`implement-ticket.js`'s own Scope-phase sidecar agent name (`implement-ticket.js`:70,
`'agent': 'ticket-scoper'`). This is direct evidence that a *different* workflow's own sidecar
write landed in the file `create-tickets.js`'s own tool calls were being attributed against,
during this run's window.

`post_tool_hook.py` prefers the session-scoped sidecar (`.claude/current_run.<session_id>`) over
the shared unscoped file specifically to prevent this class of contamination
(`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`, PR #68, landed 2026-08-24 — well before this 09-13
run). Since that isolation predates the run, contamination from a genuinely *separate* Claude Code
session (a different `session_id`) should not have reached this run's own scoped sidecar file. The
only way this specific contamination signature survives that isolation is if it happened *within
the same session_id* — e.g. the same interactive session that ran `create-tickets` in this window
also ran (or hand-invoked) an `implement-ticket.js` Scope-phase step under that same session_id, in
the gap between `create-tickets.js`'s own `writeSidecar('Structure', ...)` call and its own
Structure `pushEvent()`. This is the same class of race `create-tickets.js`'s own code comment
already documents for the deliberately-unwired `investigate`/`write` `pipeline()` fan-out sites
(concurrent writers sharing one mutable sidecar file) — just extended to a same-session,
cross-*workflow* case neither file defends against, since neither has any way to know another
workflow shares its session.

This cannot be confirmed further: the historical intermediate states of
`.claude/current_run.<session_id>` are not durable or logged anywhere — only the resulting
`tools.jsonl` rows persist, and they show the *effect* (misattribution) but not which other
workflow/session caused it, or the exact timing. Per the ticket's own Out-of-Scope instruction,
this is recorded as the known, separately-tracked concurrent-contamination class and not
re-solved here.

## Anomaly 2 & 3 — 09-23 run: no rows at seq 9/10, 94 rows stuck at seq 8 for 4 hours

**Both anomalies share one confirmed root cause: `writeSidecar()` swallows every failure
unconditionally, and nothing ever resets the sidecar.**

1. `writeSidecar()`'s shell command ended in `2>/dev/null || true` — this redirects the inner
   `python3 -c` script's stderr to `/dev/null` *and* forces the whole shell command to exit 0
   regardless of whether the Python write actually succeeded. If the write-sequence or link-epic
   `writeSidecar()` call failed for any reason, the failure was completely invisible: no warning,
   no changed exit code, nothing. The sidecar file would simply keep whatever value the *previous*
   successful write left it at (Structure's own `seq: 8`).
2. `create-tickets.js` has no equivalent of `implement-ticket.js`'s sidecar-clear. Grepping this
   file for `current_run` writes outside `writeSidecar()` itself returns nothing. Its own
   `writeMonitoring()` docstring comment claims "No writeSidecar() call here, by design... mirrors
   implement-ticket.js's own permanent exclusion" — but that claim is incomplete:
   `implement-ticket.js`'s own `writeMonitoring` agent prompt does not merely *omit* a
   `writeSidecar()` call, it actively *clears* the sidecar as an explicit "Step 0" before its own
   `record_events.py`/`record_run.py` invocations (`implement-ticket.js` lines 396-404, citing
   `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`). `create-tickets.js`'s own
   `writeMonitoring()` had no equivalent clear — so even on a run where every real
   `writeSidecar()` call succeeded, `writeMonitoring`'s own two tool calls would still inherit
   and inflate whatever the last real phase's sidecar said.

Combined, these explain the 09-23 run precisely: once Structure's sidecar write set `seq: 8`, any
silent failure downstream (write-sequence and/or link-epic) left it stuck there. Every subsequent
tool call — real work from those later phases, `writeMonitoring`'s own bookkeeping calls, and (per
the code's own missing-reset gap) any *unrelated* later tool call in the same session before the
next real `writeSidecar()` write from any workflow — kept inheriting `seq: 8`, accounting for both
the 94-row inflation and the 4-hour tail.

**A third, independent, directly-confirmed defect found in the same pass:** `write-sequence`'s own
`writeSidecar()` call (inside the `if (hasIntraDeps) { ... }` block) has *no* matching `pushEvent()`
call anywhere in that block — grep-confirmed zero occurrences of `pushEvent('Write', 'write-
sequence'` before this fix. Even when the write succeeds, `write-sequence`'s own tool-call rows
have no event at that seq for `compute_tool_stats()` to attribute them to — permanently orphaned,
undercounting cost for every batch with intra-batch dependencies. This is separate from, and
additive to, the stuck-sidecar problem above.

## Conclusion

- Anomaly 1: confirmed as the known concurrent-session/cross-workflow sidecar-sharing class:
  unconfirmable beyond that without durable state that no longer exists. Not re-solved here, per
  Out of Scope.
- Anomalies 2 and 3: confirmed as one real code defect (silent `writeSidecar()` failure + no
  sidecar reset on any exit path), fixed in this ticket.
- A third, independently-confirmed defect (write-sequence's missing `pushEvent()`) found and fixed
  in the same pass, since it directly affects create-tickets' own cost-attribution trustworthiness
  — the same property this ticket exists to restore.

Per this ticket's own Assumptions/Open Questions: per-event attribution for the 4 wired sites
*is* still viable — nothing here shows a structural reason it can't work, only that two
implementation gaps (silent failure, no reset) were undermining it. No need to fall back to
run-level totals.
