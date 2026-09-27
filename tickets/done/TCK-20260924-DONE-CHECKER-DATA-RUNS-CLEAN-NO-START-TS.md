---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS
phase: done
date: 2026-09-24
tags: [workflows, process-improvement, agent-monitoring]
---

# TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS

## Title

`done_checker_static.py`'s `data_runs_clean` always FAILs on a hand-orchestrated close, because the
CLI has no way to supply `--start-ts`

## Status

OPEN

## Tier

standard

## Type

bug

## Priority

P2

## Request Summary

CLAUDE.md instructs an agent closing a ticket by hand to run
`python3 tools/gate_checks/done_checker_static.py --ticket-id <TCK-ID>`. On that path the
`data_runs_clean` precheck condition **cannot pass**, regardless of how clean the repo actually is.

The mechanism, confirmed by reading the source:

- `--start-ts` is declared with `default=None` (`done_checker_static.py:1213`) and is threaded
  straight into `check_data_runs_clean(start_ts)` (`:799`).
- `_find_flagged_data_run_files()` flags a file when
  `start_epoch is None or f.stat().st_mtime >= start_epoch` (`:227`) — so when `start_ts` is
  absent, **every** file under `data/runs/` and `reports/release_proof/` is flagged.

This is a deliberate fail-closed choice, documented in the module's own words as *"unparsable
start_ts is not evidence of cleanliness"* (`:448`), and it is correct for the pipeline path, where
`implement-ticket.js` supplies a real `start_ts`. The gap is that the hand-orchestrated CLI —
added by `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` precisely so this
check would be reachable by hand — has no source for that value, so the condition it made reachable
is one that path can never satisfy.

Observed live on 2026-09-24 during `TCK-20260924-DELIVERY-STATUS-TOOL`'s hand-orchestrated close:
`data_runs_clean` FAILed against ~100 `data/runs/` directories whose mtimes all predated that
ticket's work, in a worktree shared with two other active sessions. The closing agent correctly
declined to `rm -rf data/runs/*` to clear it — that data was not attributable to its ticket and may
have been another session's live output — and reported the FAIL truthfully rather than routing
around it. That was the right call, and it is the behaviour this ticket should keep possible.

A gate that always fails on a supported path trains agents to ignore it, which is the more expensive
failure than the missing cleanup it is trying to catch.

## Scope

- Give the hand-orchestrated CLI path a real `start_ts` (see Open Questions for candidate sources),
  so `data_runs_clean` evaluates the same question the pipeline path evaluates.
- If no `start_ts` can be established for a given invocation, report that condition as explicitly
  **indeterminate** rather than as a `FAIL` that reads identically to a genuine dirty-repo finding —
  a closing agent must be able to tell "you left run data behind" apart from "this check had nothing
  to measure against."
- Tests covering: a resolvable `start_ts` on the CLI path, an unresolvable one, and the existing
  pipeline path with an explicit `--start-ts` (which must not change behaviour).

## Out of Scope

- Weakening the fail-closed rule for the **pipeline** path. When `implement-ticket.js` passes an
  explicit `start_ts` that is present but unparsable, flagging everything stays correct.
- Auto-deleting anything. This ticket must not add a cleanup that could remove a concurrent
  session's live `data/runs/` output — the shared-worktree hazard above is the reason.
- `clean_data_runs_early()`'s own post-Test behaviour on the pipeline path.
- The other `done_checker_static.py` conditions.

## Acceptance Criteria

1. `done_checker_static.py --ticket-id <TCK-ID>` with no `--start-ts` no longer reports
   `data_runs_clean: FAIL` purely because `start_ts` was absent.
2. A genuinely dirty `data/runs/` — files written after the resolved start point — still FAILs.
3. When no start point can be resolved, the condition's status is distinguishable from a real
   failure in both the human output and the exit code semantics, and the evidence string says why.
4. Passing an explicit `--start-ts` produces byte-identical behaviour to today.
5. `_find_flagged_data_run_files()` remains the single shared walk for both callers — the
   no-divergence rule from `TCK-20260708-DATA-RUNS-CLEANUP-TIMING` is not broken.
6. Existing `tools/gate_checks/` tests pass unchanged.

## Related Tickets

- `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` — added the CLI this gap
  lives on.
- `TCK-20260708-DATA-RUNS-CLEANUP-TIMING` — introduced the shared walk and the early-clean
  checkpoint.
- `TCK-20260714-DATA-RUNS-VERIFY-REGEN` — added `done-checker`'s Step 0a static precheck.
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` — the same class of gap
  (pipeline-only assumption leaking into a hand-orchestrated path).
- `TCK-20260924-DELIVERY-STATUS-TOOL` — the close that surfaced this.

## Related Docs

- `docs/ai/ticket-lifecycle.md` — Verify / Definition of Done, Step 0a.
- `CLAUDE.md` — "After Work", which tells agents to run this CLI by hand.

## Related Stored Artifacts

_None yet._

## Related Code Areas

- `tools/gate_checks/done_checker_static.py` — `_find_flagged_data_run_files()`,
  `check_data_runs_clean()`, `run_static_precheck()`, the `--start-ts` argument
- `.claude/workflows/implement-ticket.js` — the pipeline caller that does supply `start_ts`
- `tests/tools/` — existing gate-check tests

## Assumptions / Open Questions

1. **Where a hand-orchestrated `start_ts` should come from.** — **RESOLVED, see
   investigation.md/plan.md.** The ordering assumption (closure recorder runs before the static
   checker) **was confirmed, not assumed**: `record_hand_orchestrated_closure.py` sets
   `run_id == ticket_id`, and `check_monitoring_write_recorded` already reads exactly that shape.
   But reading `record_hand_orchestrated_closure.py`'s own source found the first candidate's
   ranking was too confident: its `start_ts` defaults to **closure time** (`start_ts or now`)
   unless the closer explicitly passed a real one to *that* command — which nothing in this
   session's own several closures this batch did. Used as the sole fallback anyway (still the only
   candidate with a real, already-`start_ts`-shaped field and a shared reader to reuse — the other
   two candidates collapse toward the same closure-adjacent moment under this repo's actual
   hand-orchestration pattern, confirmed by reading, not assumed either), but the evidence string
   now discloses that caveat inline whenever it's used, rather than presenting a resolved value as
   unconditionally trustworthy.
2. **How to represent "indeterminate".** — **RESOLVED: new `INDETERMINATE` value, not a `PASS`.**
   Checked every real consumer before introducing it (investigation.md's full list):
   `_render_results`/`classify_checklist_failure` only ever special-case the literal string
   `"FAIL"`, and `NA` already exists safely in this exact contract for a different reason
   (`check_staging_artifacts_complete`'s hotfix case) — proving a third value is already a safe
   pattern here, not a novel risk. The pipeline's LLM done-checker agent reads the raw JSON
   directly rather than doing a rigid string match, so a self-explanatory evidence string is
   sufficient without a new prompt rule, mirroring how `NA` already works there.
3. Whether the shared-worktree case needs anything beyond a correct `start_ts`. — **Confirmed
   provisionally-no, unchanged**: no worktree-aware logic added.

## Implementation Notes

Full reasoning in `staging_artifacts/TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS/
{investigation,plan}.md`. `check_data_runs_clean` gained an optional `ticket_id` parameter (kept
`start_ts` first and positional so all 5 existing real-`start_ts` call sites are untouched — AC4).
Resolution order: explicit `start_ts` (unchanged, including the unparsable-flags-everything case) →
this ticket's own run record via the already-shared `_jsonl_rows_for_run_id_across_weeks` (reused,
not reimplemented) → `INDETERMINATE`. `run_static_precheck` now passes `ticket_id` through.
Corrected a stale module-docstring claim ("no new status vocabulary here") that `NA`'s own
pre-existing addition had already invalidated before this ticket, found while reading the header
to scope the change.

## Test Summary

- `tests/tools/test_done_checker_static.py::check_data_runs_clean` section: renamed the one test
  whose expected outcome changes (absent `start_ts`, no ticket context → `INDETERMINATE`, was
  `FAIL`), added 4 new tests (present-but-garbage `start_ts` still `FAIL`; run-record fallback
  `PASS`/`FAIL` sub-cases; `ticket_id` given but no matching run record → `INDETERMINATE`). All 5
  pre-existing real-`start_ts` tests unchanged. `/home/u24desktop/Working/rpg-based-simulation/
  .venv/bin/python3 -m pytest tests/tools/test_done_checker_static.py -v` — **137 passed**
  (confirmed the 11 `data_runs_clean`-scoped tests individually too).
- Full regression: `tests/tools/ -m "not slow and not extra_slow"` — **3055 passed**, 25 skipped,
  28 deselected, 1 xfailed, 0 failed.

## Files Changed

- `tools/gate_checks/done_checker_static.py` — `check_data_runs_clean()` gained `ticket_id`/
  `data_root` params and the run-record fallback + `INDETERMINATE` path; `run_static_precheck()`
  passes `ticket_id` through; module docstring's stale "no new status vocabulary" claim corrected.
- `tests/tools/test_done_checker_static.py` — 1 test renamed/re-asserted, 4 new tests.
- `staging_artifacts/TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS/
  {investigation,plan,test_plan}.md` (new).
- `docs/REGISTRY.yaml` — regenerated as part of ticket close (routine, unconditional per the
  Finalize rule).

## Completion Summary

`data_runs_clean` no longer FAILs purely because the hand-orchestrated CLI path has no source for
`start_ts` — it now falls back to the ticket's own run record (reusing the existing shared reader,
not a new one) and, failing that, reports a new `INDETERMINATE` status that is explicitly not a
`FAIL` and not a `PASS`, distinguishable in both the human CLI output and exit-code semantics
(only the literal string `"FAIL"` triggers non-zero, confirmed against every real consumer, not
assumed). The genuinely-dirty and explicit-unparsable pipeline paths are both byte-identical to
before.

Two things the ticket's own Open Questions got right to flag as uncertain and which investigation
corrected rather than confirmed as stated: the ordering assumption *does* hold, but the top-ranked
`start_ts` candidate is weaker evidence than "most semantically correct" implied — it defaults to
closure time, not true session start, in this repo's actual observed hand-orchestration pattern.
The evidence string now says so inline rather than presenting a resolved value as unconditionally
trustworthy. No known material gap.
