---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-DUPLICATE-RUN-RECORDS
phase: done
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-DUPLICATE-RUN-RECORDS

## Title
60 runs are written twice with identical `run_id`, `execution_id` and `start_ts` — every run-count metric, including the retro's own headline, is inflated by an unknown amount

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Sweeping `agent-monitoring/data/*/runs.jsonl` (1,609 records) found **142 `run_id`s with more than
one run record**. Splitting them by whether the duplicates are distinguishable:

- **82 carry a distinct `execution_id` or `start_ts`** — legitimate re-runs of the same ticket. Not
  a defect.
- **60 carry an identical `execution_id` AND an identical `start_ts`** — the same run recorded
  twice, with nothing to tell the copies apart.

Sample of the ambiguous-looking group (distinct starts, so *not* in the 60): `TCK-20260606-DOCSITE-
SCHEMA` has two DONE records at `01:06:18` and `01:13:36`; `TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH`
at `13:36:07` and `13:44:38`. Those are re-runs. The 60 are the ones where even that distinction
is absent.

**Consequence, and the reason this is first in the epic:** every count derived from `runs.jsonl`
is inflated. The 2026-09-15 two-week review reports 249 runs and a 93% DONE rate; neither figure
can be trusted until the size of the duplication inside the window is known. Nothing currently
flags this — `agent-monitoring-validate` checks that records *exist*, not that they are unique.

## Scope
- Determine whether this is a write-path defect (something appends a run record twice) or an
  expected consequence of some workflow re-entry pattern that reuses `run_id` and `execution_id`.
  Start from `tools/agent-monitoring/record_run.py` and the `writeMonitoring` path in
  `.claude/workflows/implement-ticket.js`.
- Measure how many of the 60 fall inside recent windows (7/14/28 days) versus historical, so the
  retro can state a corrected figure or an explicit uncertainty.
- Decide the disposition: dedupe on read, prevent on write, or accept-and-document. All three are
  legitimate; silently leaving it is not.

## Out of Scope
- Rewriting or deleting historical `runs.jsonl` rows. If dedupe-on-read is chosen, the corpus stays
  as-is.
- The 82 legitimate re-runs.
- `seq` duplication inside events — that is `TCK-20260915-EVENT-SEQ-INTEGRITY`.

## Acceptance Criteria
- [x] The cause is identified, or explicitly recorded as not-determinable with the evidence
      available. (Two causes, not one: 95% of "duplicates" are legitimate multi-checkpoint
      continuations, confirmed via direct event-log correlation; 1 all-time instance is a
      confirmed genuine accidental duplicate from a hand-typed CLI invocation.)
- [x] The count inside the last 14 days is measured, so the retro's run count can be corrected or
      caveated. (249→247 runs, 233→232 DONE, 93.6%→93.9% — see RETRO-LAST14D.md's new note.)
- [x] A disposition is recorded (prevent / dedupe-on-read / accept), with its reason.
      (Dedupe-on-read, wired into `generate_retro.py`.)
- [x] If a detector is added, it ratchets and does not assert zero. (Ratchets on the narrow
      "identical outcome" bucket, ceiling **1** — not the raw 60/66, which conflates healthy
      continuations with real accidents; see Completion Summary for why.)

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)
- `TCK-20260915-MONITORING-ANOMALY-VALIDATOR` — the capstone detector, scoped after this

## Related Docs
- `agent-monitoring/retro/RETRO-LAST14D.md`
- `docs/agent-monitoring/schema.md`

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/record_run.py`
- `.claude/workflows/implement-ticket.js` (the `writeMonitoring` path)
- `agent-monitoring/data/*/runs.jsonl`

## Assumptions / Open Questions
- Whether `execution_id` is *supposed* to be unique per run record is itself unconfirmed — check
  `docs/agent-monitoring/schema.md` before treating identical values as proof of duplication.
- The 60/82 split was computed on the whole corpus, not the recent window. Re-derive.

## Implementation Notes
Reproduced with a direct scan of the shards, not `monitoring.db` — confirmed the ticket's own
142/82/60 split exactly.

**The single most important finding**: the "60 identical duplicates" figure is not one defect —
directly correlating a sample group's shared `execution_id` against its own `events.jsonl` timeline
showed a perfectly coherent, continuously-progressing single execution (Investigate → Plan →
Review:failed → Implement:fix → ... → Finalize), matching the 3 `runs.jsonl` records for that
execution exactly. `writeMonitoring()` fires at every gate exit within one continuous execution by
design; a session continuing past a gate failure (fixing it, carrying on) legitimately produces
multiple checkpoint rows. This is real audit-trail data, not noise. Classified all 66 all-time
duplicate-key groups: 63 progressive (this shape), 2 ambiguous-but-plausible epic-batch
continuations, 1 confirmed genuine accidental duplicate (hand-typed `record_run.py` invocation,
non-standard `-final`-suffixed `execution_id`, most likely a copy-pasted repeat).

**A real hazard hit and reverted mid-investigation**: `generate_retro.py --days 14` (run once to
sanity-check the corrected numbers) unconditionally overwrites
`agent-monitoring/retro/RETRO-LAST14D.md`, which has a large hand-authored "Deep review" section
from `agent-working-design`. Caught via `git status` immediately after, reverted before any other
work touched the file, and used the importable `_load_runs_and_events()`/`compute_retro_metrics()`/
`generate()` functions directly for every subsequent measurement — never the CLI, on this file,
again.

## Test Summary
- `tests/tools/test_run_dedup.py` (new, 10 tests) — grouping correctness including a real
  false-positive this module's own first draft produced (two unrelated pre-schema-unification
  records both missing `start_ts`, caught by inspecting the group's content before shipping the
  ratchet baseline) and fixed before committing; a real-corpus pin of the measured 66/63/2/1
  classification.
- `tests/tools/test_generate_retro.py` — extended with 3 new tests (dedup note rendering,
  note omission when counts match/unset, end-to-end `main()` dedup via monkeypatched
  `RETRO_DIR`/`_load_runs_and_events`). Full file: 152 passed (149 pre-existing + 3 new).
- `tests/tools/test_duplicate_run_record_check.py` (new, 7 tests) — ratchet pass/fail, the
  progressive-continuation-never-flagged property (the whole point of the narrow ratchet), ceiling
  pin, real-corpus check, Makefile wiring.
- `make duplicate-run-record-check` confirmed end-to-end against the real corpus: PASS.

## Files Changed
- `tools/agent-monitoring/run_dedup.py` (new) — grouping/dedup/classification utility.
- `tools/agent-monitoring/generate_retro.py` — wired dedup into `main()`'s three report branches;
  `generate()` gained optional `raw_run_count`/`deduped_run_count` params and renders an inline
  note when they differ.
- `tools/gate_checks/duplicate_run_record_check.py` (new) — ratchet check, ceiling 1.
- `tests/tools/test_run_dedup.py` (new), `tests/tools/test_generate_retro.py` (extended),
  `tests/tools/test_duplicate_run_record_check.py` (new).
- `Makefile` — `duplicate-run-record-check` target + `.PHONY` entry.
- `agent-monitoring/retro/RETRO-LAST14D.md` — additive note with corrected figures (per the
  epic's own AC #3: written back into the retro, not left in this ticket body alone).

## Completion Summary
Disposition: dedupe-on-read, not prevent-on-write, not accept-and-ignore. The 60/66-group "identical
duplicate" figure conflates two unrelated mechanisms: 95% (63/66) is legitimate, by-design
multi-checkpoint continuation behavior (confirmed via direct event-log correlation, not assumed),
and only 1/66 is a genuine accidental duplicate. A ratchet on the raw 60/66 would have been the
wrong invariant — it would need raising every time a normal gate-failure-then-fix pattern occurred,
exactly the "gate maintenance is diff-indistinguishable from gate weakening" trap named in
`docs/plans/agent_infrastructure/reachability_verification_findings.md` Finding 8. Instead ratcheted
the narrow bucket (`identical_outcome`, ceiling 1) that a legitimate continuation structurally
cannot produce. Wired the dedup into `generate_retro.py` so every future report reflects real
execution counts automatically, and corrected `RETRO-LAST14D.md`'s own headline in place (249→247
runs, 233→232 DONE) — a real but small correction, since only 2 of 66 all-time duplicate groups
fall inside the 14-day window.
