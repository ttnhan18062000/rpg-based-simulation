---
status: idea
layer: observability
authority: P2
audience: developer
maturity: idea
date: 2026-07-28
tags: [idea, agent-monitoring, observability, data-quality, root-cause, bug]
---

# Idea: Pause/Resume Seq-Counter Collision Silently Corrupts `tool_call_count`/`cost_proxy_score`

## Problem

`agent-monitoring/tools.jsonl` groups tool calls by `(run_id, seq)` only. `seq` is a per-*session*
phase counter maintained inside `.claude/workflows/implement-ticket.js` — it starts at 1 every time
the workflow is invoked. When a ticket's run is paused mid-pipeline (user request, gate failure the
user walks away from, etc.) and later resumed in a **separate session** under the same `run_id`,
the new session's phase counter also starts at 1 — so its phases silently alias onto whichever
`(run_id, seq)` buckets the *original* session already wrote to `tools.jsonl`.

**Confirmed on real data** — `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` was paused mid-Implement
(`"PAUSED by user request mid-Step-7"`) and resumed in a later session
(`"resuming mid-implementation at Step 7"`), both under the same `run_id`. Comparing
`agent-monitoring/events.jsonl`'s reported `tool_call_count` against `tools.jsonl` ground truth:

| seq | `tools.jsonl` ground truth | 1st-session phase (reported) | 2nd-session phase (reported) |
|---|---|---|---|
| 2 | 61 | Investigate: 61 | **Implement: 61** |
| 3 | 19 | Plan: 19 | **Architecture-Verify: 19** |
| 4 | 25 | Review (failed): 25 | **Test: 25** |
| 5 | 10 | Review (ok): 10 | **Parity: 10** |
| 6 | 114 | Implement (paused): 112 | **Verify (failed): 114** |

Every resumed-session phase from seq 2 onward reports the *exact same* `tool_call_count` and
`cost_proxy_score` (bit-for-bit — e.g. `28601.745` shows up twice, once under `Investigate` and
once under a completely different phase, `Implement`) as the first session's phase at that same
seq. The resumed session's real work (a genuine 76-anchor grade-regression scan during its
`Implement` step) received **zero** authentic tool-call attribution — it just echoed stale data
left over from the pre-pause session. This is what produced the retro's ~450-470x cost-proxy
"outliers" for this ticket — not real cost, a monitoring artifact.

**Blast radius (this repo's monitoring corpus, checked directly)**: 8 `run_id`s show more than one
`seq=1` `Scope`-phase entry — the signature of a multi-invocation/resumed run and therefore a
candidate for this collision: `TCK-20260719-LIVE-PHASE-AGENT-LABEL` (4 invocations),
`TCK-20260623-DEAD-CODE-REMOVAL`, `TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION`,
`TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT`,
`TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING`, `TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME`,
`TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`, and
`TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` (2 each, `LIVE-PHASE-AGENT-LABEL` had 4). Bounded —
roughly a few percent of runs in the sampled window — but real, silent, and it directly undermines
retro cost-ranking conclusions for exactly the runs a reviewer would most want to trust (anything
that needed a pause is often already the more complex/notable ticket).

## Relationship to `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` (already fixed)

That ticket (closed 2026-07-11, before this ticket's own run happened) fixed two **within-session**
mechanisms: a `Scope`-phase sidecar gap, and `writeMonitoring`'s own bookkeeping calls polluting the
last tracked phase before clearing the sidecar. Both are deterministic single-session bugs — no
concurrency, no cross-session state involved, and that ticket's own investigation explicitly ruled
out a concurrency/interleaving hypothesis in favor of those two gaps.

This is a **third, distinct mechanism** that ticket did not cover: it fires only when a ticket is
paused and resumed as **two separate workflow invocations** sharing one `run_id`, each with its own
independently-reset `seq` counter. Same failure class (silent `tools.jsonl` attribution collision
feeding corrupted `tool_call_count`/`cost_proxy_score` into `events.jsonl`), same root document
(`docs/agent-monitoring/schema.md`'s "How tool calls are attributed to agent events" section) — but
a genuinely new gap, not a regression of the fixed one.

## Idea

Give `seq` (or the `tools.jsonl` attribution key derived from it) resume-safety: before a resumed
session starts writing its own sidecar values, it needs to know the *last real seq* already used
for this `run_id` in `tools.jsonl`/`events.jsonl` and continue **past** it, rather than restarting
at 1. Candidate approaches (not pre-decided — for the ticket's own Investigate/Plan phase to weigh):

- On `Scope`-phase "load existing ticket, resume mid-pipeline" branch, compute
  `next_seq = max(existing seq for this run_id across events.jsonl) + 1` and start the resumed
  session's counter there instead of at 1.
- Alternatively, make the `tools.jsonl` attribution key a genuinely unique per-invocation token
  (e.g. `{run_id}:{session_start_ts}` or a short nonce) instead of relying on `seq` alone to be
  globally unique per `run_id` — closer to what `TOOLCOUNT-SIDECAR-COLLISION`'s original
  (later-disproven) concurrency hypothesis assumed, but this time for a case where the assumption
  is actually true (two real, separate invocations).
- Whichever approach is chosen, extend `tools/agent-monitoring/validate.py`'s
  `compute_tool_count_drift_report()` (already built by the sibling ticket) to specifically flag
  multi-invocation `run_id`s, since today it can only detect *that* recorded ≠ actual, not *why* —
  this pattern deserves its own named check so a future recurrence is diagnosed immediately instead
  of requiring another manual investigation like this one.

**Out of scope for this idea**: backfilling/correcting historical corrupted records — same
append-only precedent the sibling ticket already established (`docs/agent-monitoring/schema.md`'s
Known Limitations). Prevention-only, same as the sibling fix.

## Natural Integration Points

| Existing component | How this idea attaches |
|---|---|
| `.claude/workflows/implement-ticket.js` — Scope-phase sidecar write (added by `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`) | Needs resume-awareness: read prior max seq for the run_id before writing the first sidecar value of a resumed session |
| `tools/agent-monitoring/validate.py` — `compute_tool_count_drift_report()` | Natural home for a dedicated multi-invocation/resume-collision check, distinguishing this mechanism from the two already-fixed ones |
| `docs/agent-monitoring/schema.md` — "How tool calls are attributed to agent events" | Should document this third mechanism once fixed, alongside the two the sibling ticket already added |
| [`idea_agent_monitoring_active_duration.md`](idea_agent_monitoring_active_duration.md) | Sibling finding from the same investigation session — that idea covers wall-clock duration contamination from session pauses; this one covers a *different* corruption (tool-call attribution) triggered by the *same* underlying pause/resume behavior. Worth fixing in awareness of each other since both touch resume handling, but they are independent bugs with independent fixes. |
| `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` (done) | Direct precedent — same failure class, same fix location, same validation-tooling home; read its Implementation Notes before starting Investigate on this one |

## Open Questions

- Is `max(seq) + 1` sufficient, or can a resumed session's phases still collide with a *third*
  future resume of the same ticket if the max-seq lookup itself races with a stale sidecar read?
  (Given the sibling ticket already ruled out true concurrency as a real-world occurrence, this may
  be a non-issue in practice — worth confirming, not assuming.)
- Should `implement-epic`'s per-child-ticket dispatch be checked for the same resume pattern, or is
  epic-level resume structurally different (new child dispatch = always a fresh `run_id`, not a
  resume of an existing one)?
- Does this warrant extending sidecar coverage the same way the Scope-phase gap was closed, or is a
  purely additive "look up max prior seq" read sufficient without changing the sidecar-write
  mechanism itself?

---

*Raised: 2026-07-28, from the same session that investigated `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`
as a reported ~450-470x cost-proxy outlier in the 28-day retro — the outlier turned out to be this
bug, not real cost.*
