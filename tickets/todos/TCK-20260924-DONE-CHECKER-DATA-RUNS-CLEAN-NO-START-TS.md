---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS
phase: open
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

1. **Where a hand-orchestrated `start_ts` should come from.** Candidates, roughly in order of
   preference:
   - the ticket's own run record in `agent-monitoring/data/YYYY-Www/runs.jsonl`, which
     `record_hand_orchestrated_closure.py` writes and which already carries a start timestamp;
   - the author date of the ticket's first commit (`git log` filtered by the ticket ID, matching
     the convention `mechanism_registry_changed_code_check.py` already uses to find "this ticket's
     own commits");
   - the `tickets/inprogress/{ticket_id}.md` file's own creation/mtime, weakest and last resort.
   The first is the most semantically correct but requires the monitoring record to exist *before*
   the check runs; CLAUDE.md's documented ordering runs the closure recorder and the static checker
   as separate steps, so the implementer must confirm the ordering actually holds rather than
   assume it.
2. **How to represent "indeterminate".** The precheck returns `(status, evidence)` pairs where
   status is `PASS`/`FAIL` today. Adding a third value touches every consumer of that contract, so
   the implementer should check what reads these tuples before introducing one; a `PASS` with an
   explicit "not measured — no start point" evidence string may be the smaller, safer change, but
   risks reading as a clean bill of health. This is the main design decision in the ticket and
   should be settled in `plan.md` with the consumer list as evidence, not chosen by feel.
3. Whether the shared-worktree case needs anything beyond a correct `start_ts`. Provisionally no:
   with a real start point, another session's older `data/runs/` output is already excluded by
   mtime. Worth confirming during investigation before adding any worktree-aware logic.

## Implementation Notes

_To be filled during implementation._

## Test Summary

_To be filled during implementation._

## Files Changed

_To be filled during implementation._

## Completion Summary

_To be filled during implementation._
