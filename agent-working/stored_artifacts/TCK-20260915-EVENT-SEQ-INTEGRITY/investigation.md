---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260915-EVENT-SEQ-INTEGRITY
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# Investigation — TCK-20260915-EVENT-SEQ-INTEGRITY

## Re-derived baseline

Direct shard scan confirms the ticket's own figures exactly: **71** runs have a duplicate `seq`,
**46** have gaps (a `seq` value missing below the run's own max).

## Duplicate `seq` — mostly the same mechanism ticket 1 already confirmed, at two different grains

Cross-referenced against `TCK-20260915-DUPLICATE-RUN-RECORDS`'s own definition of "legitimate
re-run" (a `run_id` with more than one `runs.jsonl` record, distinguishable by `execution_id`/
`start_ts`):

- **51 of 71 (72%)** duplicate-`seq` run_ids also have more than one `runs.jsonl` record — directly
  explained: each separate closure invocation for the same `run_id` restarts its own local `seq`
  numbering at 1 (`record_hand_orchestrated_closure.py`'s own docstring: "seq (1-indexed, in array
  order)" — per-invocation, not per-`run_id`-across-all-time). Not a new mechanism; the same one
  ticket 1 already characterized as legitimate, viewed from the event side.
- **1 of 71**: a genuinely different, pre-modern event schema. Direct inspection of
  `TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG`'s 5 "duplicate `seq=5`" events shows fields
  (`detail`, `event`) that don't exist in the modern schema at all (`phase`/`agent`/`status`/
  `summary`) — this is `generate_retro.py::_is_legacy_event()`'s own discriminator
  (`agent is None`), confirmed to apply here. `seq` in that older shape was never a strict
  per-event ordinal to begin with.
- **19 of 71**: a finer-grained instance of the SAME hand-orchestration-continuation mechanism,
  found by sampling one concretely: `TCK-20260805-SIMQ-GRADE-ORDER-F-BAND-GAP` has two `seq=9`
  events, both `phase: Parity`, 38 seconds apart, sharing one `execution_id` — one `status:
  skipped` ("No src/ changes, no P0 intersection"), one `status: ok` (a real parity-ledger
  disposition). Reading `implement-ticket.js`'s own Parity phase confirms the skip-path and
  full-run path are written as a genuine `if/else` — mutually exclusive within one continuous JS
  execution. Both firing, sharing one `execution_id`, is consistent with a hand-orchestrating
  session initially concluding "skip-eligible," pushing that event, then continuing the same
  conceptual execution in a later turn and deciding to actually do the parity work — correctly
  preserving the shared `execution_id` (per ticket 1's own confirmed convention) but recomputing
  `seq`/`events.length` independently each turn, occasionally producing a genuine collision when
  that recomputation doesn't account for the earlier turn's own push. This is the same underlying
  behavior ticket 1 characterized (a session correctly continuing past a gate outcome rather than
  hard-stopping), manifesting here as a within-phase `seq` collision rather than a whole extra
  `runs.jsonl` row.

## Gaps — at least two distinct, mostly-benign mechanisms; one instance left honestly unresolved

- **19 of 46** gap run_ids also have >1 `runs.jsonl` record — the same multi-invocation shape as
  above.
- **A documented, already-fixed mechanism accounts for at least one large-gap case directly**:
  `TCK-20260619-E33C-GOLD-SINK` shows only 3 events, numbered 789-791, nothing lower — reading
  `tools/agent-monitoring/seq_offset.py` (`TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`)
  confirms this exact shape: a resumed run's `seq` is deliberately offset to continue past
  whatever `seq` this `run_id` already reached, rather than restarting at 1 and colliding with the
  pre-pause session's own `(run_id, seq)` buckets. **Not fully closed**: `compute_seq_offset()`
  looks up the max prior `seq` for the SAME `run_id` in `events.jsonl`, but no earlier
  `TCK-20260619-E33C-GOLD-SINK` events exist anywhere in the current corpus to have produced an
  offset of 788 — the specific origin of that number is not determinable from the data available
  today (its source events may predate the current shard retention, or the mechanism computed it
  against a different corpus state at the time). Recorded honestly as not-determinable for this
  specific instance, rather than assumed resolved because the general mechanism is known and
  documented.
- **Remaining gap cases not individually traced** — a full per-case classification of all 46 was
  not completed given this ticket's practical scope; the two confirmed mechanisms above account for
  a meaningful share and are the best-supported explanation for the population as a whole.

## What `seq` actually guarantees — documentation was overclaiming (AC #3)

`docs/agent-monitoring/schema.md`'s existing `seq` row states "1-based call order within the run.
Monotonically increasing," with disjoint exceptions only for shadow-call sites. **This overclaims**
— confirmed directly against the real corpus: `seq` is unique and contiguous only within one
continuous execution/invocation of the writing script. A `run_id` spanning multiple invocations
(legitimate re-runs, resumed pauses, or a hand-orchestrating session continuing past a gate outcome
across turns) can show duplicate or non-contiguous `seq` values, by design in most cases. Consumers
must not assume `seq` is globally unique or gap-free per `run_id` — only that it orders events
*within* one continuous invocation.

## Shared cause with `TCK-20260915-DUPLICATE-RUN-RECORDS` — confirmed, not merely plausible

The ticket's own Related Tickets note flags this as a "possible shared cause, worth checking."
Confirmed directly above: 51 of 71 duplicates and 19 of 46 gaps are explained by the identical
multi-invocation mechanism ticket 1 already characterized as legitimate. This is the SAME
underlying behavior observed from a different artifact, not a coincidental correlation.
