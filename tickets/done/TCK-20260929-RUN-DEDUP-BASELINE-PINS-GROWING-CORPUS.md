---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260929-RUN-DEDUP-BASELINE-PINS-GROWING-CORPUS
phase: done
date: 2026-09-29
tags: [testing, agent-monitoring, root-cause]
---

# TCK-20260929-RUN-DEDUP-BASELINE-PINS-GROWING-CORPUS

## Title
`test_real_corpus_duplicate_classification_matches_measured_baseline` asserts an exact count over a
corpus that keeps growing, so any ticket re-dispatch breaks CI

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`tests/tools/test_run_dedup.py::test_real_corpus_duplicate_classification_matches_measured_baseline`
failed CI on PR #254 (`API / tools / logging`, step `Run: tests/tools`):

```
AssertionError: expected 66 duplicate groups (measured 2026-09-15), got 67
```

The count is not wrong and the fix under test is not at fault. `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`
was legitimately dispatched twice — once ending `TESTS_FAILED`, then re-dispatched after an
owner-directed test-scope correction — and those two runs form one **progressive** duplicate group,
making 67.

**The real defect is the assertion's shape, not the pinned number.** The test's own docstring
justifies exact equality by asserting the population is closed:

> "All-time counts on `runs.jsonl`'s own history **before this date** are a closed, non-growing count
> (unlike a live ratchet) -- an exact match is the correct assertion here, not a >= ceiling."

That reasoning is sound, but the code does not implement it. `classify_duplicate_groups(all_runs)`
receives **every** run `_load_runs_and_events()` returns, including runs recorded after 2026-09-15.
So the assertion is an exact match against a **growing** population, and **every future re-dispatch
of any ticket breaks it.** We are the first to trip this, not the last.

## Scope
- Make the test measure what its docstring already claims: restrict the corpus to runs whose
  `start_ts` falls on or before the 2026-09-15 measurement date, which genuinely is closed and
  non-growing, then keep the exact-equality assertions against it.
- Keep all three pinned numbers meaningful for that window (`total_duplicate_groups == 66`,
  `progressive == 63`, `same_status_diff_end == 2`, `identical_outcome == 1`) — re-measure them
  against the scoped window and record the measured values with evidence rather than assuming the
  existing numbers still describe it.
- Update the docstring so the stated reasoning and the implemented behaviour match.

## Out of Scope
- **Blindly bumping the pin to 67.** The test's own failure message says "don't just raise it
  blindly", and doing so would leave the trap armed for the next re-dispatched ticket.
- Changing `classify_duplicate_groups()` itself, or any production monitoring code. This is a test
  scoping defect.
- Deduplicating or editing the actual run records. The two runs are legitimate history and must stay.
- Any change to `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`'s own fix, which is unrelated and
  correct.

## Acceptance Criteria
1. The test scopes its corpus to runs at or before the 2026-09-15 measurement date, so the asserted
   population is genuinely closed.
2. All pinned counts are **re-measured against the scoped window** and the measured values recorded
   in the ticket, not carried over on assumption.
3. The docstring's stated reasoning matches what the code does.
4. A new run added after the measurement date **does not** change the test's result — demonstrated,
   not asserted. The simplest demonstration: the test passes on this branch, which already contains
   the two post-date runs that currently break it.
5. `tests/tools/` passes in full, matching CI's own invocation for that step.
6. No production monitoring code changed, and no run records edited.

## Related Tickets
- `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE` — whose legitimate double dispatch surfaced
  this. Folded into the same PR #254; not a defect in that fix.

## Related Docs
- `docs/agent-monitoring/README.md` — monitoring data scope.
- `docs/testing/regression_policy.md` — baseline-drift handling.
- `CLAUDE.md` "CI Failure Triage" — the drift category this falls under: a hardcoded baseline moved
  by this session's own legitimate change gets a ticket with fresh evidence, never a silent edit.

## Related Stored Artifacts
- None. Hotfix tier; intent is self-evident from the failure message.

## Related Code Areas
- `tests/tools/test_run_dedup.py:109-125` — the failing test, its docstring, and the three pins.
- `tools/agent-monitoring/generate_retro.py::_load_runs_and_events` — returns the unscoped corpus.
- `agent-monitoring/data/*/runs.jsonl` — records carry `start_ts`, which is the field to scope on.

## Assumptions / Open Questions
- Scoping by `start_ts` is assumed sufficient; every run record inspected carries it
  (`run_id`, `execution_id`, `provider`, `ticket_id`, `start_ts`, `end_ts`, `workflow`, `tier`,
  `final_status`, `agent_count`, `duration_s`). **If any historical run lacks `start_ts`, do not
  silently drop it** — report how many and decide explicitly, since dropping records would change
  the very baseline being pinned.
- The exact boundary semantics (inclusive end-of-day 2026-09-15 vs. strictly before) may shift a
  count by one. Pick one, state it in the docstring, and re-measure — do not tune the boundary to
  make a pre-existing number fit.

## Implementation Notes

Fixed entirely inside `tests/tools/test_run_dedup.py` — no production code changed, matching Out
of Scope. Added a module-level `_start_ts_date(run) -> str | None` helper and a
`_MEASUREMENT_CUTOFF_DATE = "2026-09-15"` constant, then scoped
`test_real_corpus_duplicate_classification_matches_measured_baseline` to
`[r for r in all_runs if (date := _start_ts_date(r)) is not None and date <= _MEASUREMENT_CUTOFF_DATE]`
before calling `classify_duplicate_groups()`. Rewrote the test's docstring so its stated reasoning
(the scoped window, not the whole corpus, is closed and non-growing) matches what the code now
does (AC3).

**Boundary semantics (AC's open question, resolved).** Inclusive of the entire 2026-09-15 day —
`start_ts` date `<= "2026-09-15"` — matching the Scope/AC1 wording ("on or before" / "at or
before") rather than treating it as still undecided. Stated explicitly in the new docstring.

**Missing/unparseable `start_ts` (AC's open question, resolved with evidence, not silently
dropped).** Measured directly against the real corpus: of 1761 total runs loaded via
`_load_runs_and_events()`, **105 have no determinable `start_ts`** — mostly pre-schema-unification
records with the field entirely absent, plus 5 legacy records (`TCK-20260619-E53D*` and one
`FOLDER-*` batch record) that carry `start_ts` as a raw Unix epoch number instead of an ISO-8601
string, which `_start_ts_date()` also handles (converts epoch seconds to a UTC date) rather than
treating as "missing" — all 5 land on 2026-06-14/2026-06-22, well before the cutoff. Decision:
excluded from the scoped window (their date genuinely can't be determined, or in the epoch case
falls before the cutoff and would be included either way). This decision is **provably zero-risk to
the pinned counts**, not just assumed safe: `run_dedup.py::execution_key()` already gives every
record with a falsy `start_ts` its own forced singleton group (keyed by list position), so such a
record can *never* be part of a duplicate group under this module's own definition. Verified
empirically, not just reasoned: running `classify_duplicate_groups()` on the scoped set with vs.
without the 105 missing/unparseable records folded back in produces byte-identical results
(66/63/2/1 either way).

**Re-measured pins (AC2) — all four confirmed unchanged from the pre-existing values, not carried
over on assumption:**
- `total_duplicate_groups`: **66** (measured against the scoped window: 1522 of 1761 runs have a
  determinable `start_ts` on or before 2026-09-15; 134 fall after the cutoff — including
  `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`'s own two legitimate runs, which is exactly
  why this ticket exists)
- `progressive`: **63**
- `same_status_diff_end`: **2**
- `identical_outcome`: **1**

**AC4 (demonstration, not assertion).** This branch already contains the two post-2026-09-15 runs
(`TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`'s `TESTS_FAILED` run and its later `DONE`
re-dispatch) that broke the unscoped assertion (66 → 67) on PR #254's CI. The fixed test passing on
this exact branch, with those two runs present in `agent-monitoring/data/2026-W40/runs.jsonl`, IS
the demonstration that a new run added after the measurement date no longer changes the test's
result — not merely asserted.

**Post-close near-miss: an accidental duplicate run record, caught and removed before push, not
accommodated.** After Verify/Finalize, a `record_run.py --data` call to correct this run's own
`agent_count` (7 → 12, after backfilling some hotfix-skip events initially omitted) carelessly
reused the prior call's literal `end_ts` string instead of capturing a fresh timestamp. That
appended a second `runs.jsonl` row for the same `(run_id, execution_id, start_ts)` sharing the
identical `final_status` and `end_ts` — indistinguishable from the first — which is exactly the
`identical_outcome` shape `tools/gate_checks/duplicate_run_record_check.py`'s live ratchet exists
to catch (`IDENTICAL_OUTCOME_CEILING = 1`). Verified directly: the ratchet check and
`tests/tools/test_duplicate_run_record_check.py::test_real_corpus_is_at_or_below_the_ratchet_ceiling`
both failed (count 2 > ceiling 1) before this was fixed. **Resolved by deleting the stale
`agent_count=7` line** from the still-uncommitted, unpushed per-batch shard, keeping only the
corrected `agent_count=12` row — this was a data-entry error correcting a single real event, not a
record of two distinct events, so removing the duplicate was not a history rewrite (nothing had
been committed or published). The ratchet ceiling was deliberately left at 1, not raised — the
constant's own comment ("Raising it to paper over a newly-introduced accidental duplicate defeats
the entire point of this check") forbids exactly that move, and this incident is the precise case
it exists to prevent. Both checks re-confirmed passing at ceiling 1 after the fix. `record_run.py`
itself was not touched (silently allowing an unrequested duplicate append for an existing
`(run_id, execution_id, start_ts)` is a separate, out-of-scope tooling gap, raised by the ticket
owner elsewhere rather than fixed here).

## Test Summary
`tests/tools/test_run_dedup.py` — all 10 tests pass, including the fixed baseline test.
Full `tests/tools/` suite (matching CI's own `API / tools / logging` step invocation exactly):
**3190 passed, 53 skipped, 1 xfailed, 0 failed** in 360.96s. No new coverage gaps — this is a
test-file-only change; the fix's own correctness is what the fixed assertion verifies.

## Files Changed
- `tests/tools/test_run_dedup.py` — scoped the real-corpus baseline assertion to the closed
  2026-09-15 window instead of the whole (growing) corpus; added `_start_ts_date()` helper;
  rewrote the test's docstring to match the implemented behavior.
- `docs/REGISTRY.yaml` — regenerated (auto-regen side effect of merging the branch's own dispatch
  commit and running the done-checker CLI during Verify; no substantive content change, only the
  `Generated:` timestamp).

## Completion Summary
Fixed `test_real_corpus_duplicate_classification_matches_measured_baseline`'s unsound assertion
shape: it claimed to measure a "closed, non-growing" population but actually ran
`classify_duplicate_groups()` over the entire, ever-growing `runs.jsonl` history, so any legitimate
ticket re-dispatch (exactly what `TCK-20260928-NATURAL-AGING-DEATH-DUAL-WRITER-RACE`'s own
owner-directed re-run did) broke it. Scoped the corpus to runs with `start_ts` on or before the
2026-09-15 measurement date — a population that genuinely is closed — and kept exact-equality
assertions against it. Re-measured all four pins directly against the scoped window; all four
matched the pre-existing values (66/63/2/1), confirmed with evidence rather than carried over on
assumption. The pin was never wrong; the population it was measured against was unsound. No
production code, run records, or the natural-aging fix were touched.
