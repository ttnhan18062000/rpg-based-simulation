---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260915-DUPLICATE-RUN-RECORDS
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# Investigation — TCK-20260915-DUPLICATE-RUN-RECORDS

## Re-derived baseline (direct shard scan, not `monitoring.db`)

Reproduced the ticket's own cited figures exactly, from scratch:

- **142 `run_id`s with more than one `runs.jsonl` record.**
- **82** have at least one distinguishing `(execution_id, start_ts)` pair among their records —
  legitimate re-runs, out of scope per the ticket's own Scope.
- **60** have every record sharing one identical `(execution_id, start_ts)` pair.

## What the 60 "identical" duplicates actually are — checked via direct event correlation, not
## assumed

Grouped every `runs.jsonl` record by `(run_id, execution_id, start_ts)` — requiring BOTH
`execution_id` and `start_ts` to be truthy before treating two execution_id-less records as the
same group (a first draft of this grouping treated two records that BOTH happened to be missing
`start_ts` as "identical," which produced a false match between two totally unrelated
pre-schema-unification records for `TCK-20260629-SIMQ-EMIT-NARRATIVE` — caught by reading the
group's actual content, not shipped). Splitting the 66 real duplicate groups (a slightly different
count than "60 run_ids" — see note below) by what distinguishes their records:

| Class | Count (all-time) | Count (last 14 days) |
|---|---|---|
| **Progressive** — records differ in `final_status` | 63 | 1 |
| **Same status, different `end_ts`** — ambiguous | 2 | 0 |
| **Identical outcome** — same `final_status` AND `end_ts` | 1 | 1 |

(66 groups vs. the "60 run_ids" figure: a run_id can be scoped into more than one distinct group if
it also has an execution_id-present sub-history, so "distinct groups" and "distinct run_ids with
any duplicate" are two related-but-different countable things — both reported here rather than
picking one silently.)

**Direct event-log verification, not inference**: pulled `events.jsonl` for a sample "progressive"
group's shared `execution_id` (`claude-TCK-20260803-DOC-UPDATER-CORE-WIRING-...`). The events form
one coherent, continuously-progressing timeline: `Investigate` (14:50) → `Plan` (14:58) →
`Review: failed, NEEDS_CHANGES` (15:02) → `Implement` (fix, 15:11) → `Architecture-Verify` (15:35)
→ `Test` (15:58) → `Verify: failed, BLOCKED` (15:58) → `Verify: ok, READY_TO_CLOSE` (16:04) →
`Finalize` (16:09) — exactly matching the three `runs.jsonl` records for that execution_id
(`NEEDS_CHANGES` @ 15:05, `DOD_BLOCKED` @ 16:03, `DONE` @ 16:09). **This is not duplication — it is
one real execution correctly keeping one stable identity across every gate exit point, with
`writeMonitoring()` firing (as `implement-ticket.js` itself is written to do) at each one.** Every
`writeMonitoring()` call site in `implement-ticket.js` is followed immediately by `return` for a
gate failure — the JS itself never calls it twice in one execution — so these multi-row groups
reflect a session continuing past a gate failure within the same continuous execution (fixing the
issue and carrying on) rather than literally halting and waiting for a fresh, separately-identified
resume, which is standard, accepted practice in this repo (this session's own history this batch
does exactly this routinely) — not a defect in itself.

**The "same status, different `end_ts`" pair** (`FOLDER-tickets-todos-agent-infra-hardening`,
2 records both `DONE` but ~8 minutes apart, `agent_count` 1→2) is the epic-batch equivalent: only
one `writeMonitoring`-equivalent call site exists in `implement-epic.js`'s own batch-monitoring
step (confirmed by reading the JS directly — no second call site), so this is most plausibly the
same epic folder's batch-monitoring step being invoked again in a later session picking up
remaining folder work, using the same (deliberately omitted-`execution_id`, but omitted here too,
so `start_ts`-keyed) batch identity — consistent with the "progressive" story's mechanism, just
without `execution_id` to confirm as directly since `implement-epic.js`'s batch writer omits it by
design (confirmed in the JS's own comment).

**The one genuine "identical outcome" duplicate** —
`TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE`, two byte-identical `runs.jsonl` rows (same
`end_ts`, `duration_s`, `agent_count` down to the second) — is the real accidental duplicate the
ticket worried about. Its `execution_id` ends in the literal suffix `-final`
(`claude-TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE-1788368000000-final`), not the
`<epoch-ms>-<8-hex-chars>` shape `implement-ticket.js`'s own `secrets.token_hex(4)` generation
always produces — strong evidence this was a **hand-typed `record_run.py --data '...'` invocation**
(the sanctioned per-hand-orchestration path, not the formal pipeline's own `writeMonitoring()`),
most plausibly run twice with the same copy-pasted `--data` JSON by mistake. `record_run.py` has no
existence check before appending (`validate_record()` only checks required-field presence — read
directly, confirmed) so nothing would have caught a literal re-paste.

## Cause, stated plainly

**Not a single write-path bug.** Two distinct, unrelated mechanisms produce records that satisfy
the same surface definition ("identical run_id/execution_id/start_ts"):

1. **63 of 66 groups (95%)**: legitimate, by-design behavior — `writeMonitoring()` fires at every
   gate exit point within one continuous execution, and a session continuing past a gate failure
   (rather than a hard stop) correctly produces multiple checkpoint rows sharing one identity. This
   is accurate audit-trail data, not noise, and is not "fixed" by this ticket.
2. **1 of 66 groups**: a genuine accidental duplicate from a hand-typed `record_run.py` invocation
   run twice. `record_run.py` has no write-time guard against this (out of scope to add one here —
   see Disposition below for why dedupe-on-read is the chosen fix instead).
3. **2 of 66 groups**: ambiguous, most likely the epic-batch equivalent of (1), not independently
   confirmable without an `execution_id` to correlate against events.jsonl the same way.

## Consequence for reported metrics — measured, not assumed

`tools/agent-monitoring/generate_retro.py::compute_retro_metrics()`'s `run_summary.total` is
`len(runs)` with no deduplication (confirmed by reading the function directly). Since duplicate
rows from mechanism (1) above always add a NON-final-status row to the denominator (an intermediate
`NEEDS_CHANGES`/`DOD_BLOCKED` checkpoint is never itself counted as `DONE`), the naive `total` is
inflated and the naive DONE rate is **understated**, not overstated as one might assume from
"duplicate" framing alone.

Re-computed the actual last-14-days window (`_load_runs_and_events()` + the same
`_record_since_cutoff` window `generate_retro.py --days 14` itself uses, called directly — **never
via the CLI**, which unconditionally overwrites `agent-monitoring/retro/RETRO-LAST14D.md` and would
have destroyed the peer's own hand-added "Deep review — 2026-09-15" section; caught this before it
happened by checking `git status` immediately after a first CLI test run, reverted it, and used the
importable functions directly for every measurement after that):

| | Raw (current) | Deduplicated |
|---|---|---|
| Total runs | 249 | **247** |
| DONE | 233 | **232** |
| Gate failures | 15 | **14** |
| DONE rate | 93.6% | **93.9%** |

**The correction is real but small** — only 2 of the 66 all-time duplicate groups fall inside the
last-14-days window (1 progressive, 1 the confirmed genuine duplicate). The retro's own "249 runs"
headline was inflated by 2, not by anything close to 60 — the 60/66 figure is a whole-corpus,
multi-month count, and the ticket's own framing ("every run-count metric ... inflated by an unknown
amount") is accurate as written (the amount WAS unknown until measured) but the actual 14-day
impact turns out to be minor once measured directly.

## Disposition: dedupe-on-read

- **Not prevent-on-write**: mechanism (1)/(3) (97% of the duplicate volume) are legitimate,
  by-design behavior — adding a write-time uniqueness guard would either reject real, wanted
  continuation writes or require teaching the write path to distinguish "same execution continuing"
  from "accidental re-write," which is exactly the read-side classification this ticket's own
  `run_dedup.py` already does more cheaply.
- **Not accept-and-ignore**: the retro's own headline number was measurably wrong (by a small but
  real amount), and the mechanism was previously undocumented.
- **Dedupe-on-read, implemented**: `tools/agent-monitoring/run_dedup.py` (new) groups by
  `(run_id, execution_id, start_ts)` and keeps the record with the highest `end_ts` (chronologically
  latest — a later checkpoint has done at least as much work) per group, wired into
  `generate_retro.py`'s run/event loading so every report (weekly, `--days N`, `--all`) gets the
  deduplicated view automatically, without ever rewriting `runs.jsonl` itself (the historical
  baseline stays frozen, matching `TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` items 1/6's own
  precedent for `working_log.csv`).
- **Ratchet, on the narrow "identical outcome" bucket only, not the raw 60/66**: a hard ratchet on
  "60 duplicate run_ids" would conflate healthy continuations with real accidents and would need
  raising every time a normal gate-failure-then-fix pattern occurs — the wrong invariant to pin.
  Instead, `run_dedup.py::classify_duplicate_groups()`'s `identical_outcome` bucket (baseline: **1**,
  all-time) is the one worth watching, since it is specifically the shape a genuine accidental
  duplicate produces and legitimate continuations structurally cannot (a real continuation
  necessarily changes `final_status` or reaches a later `end_ts`, or it wouldn't represent
  additional work).
