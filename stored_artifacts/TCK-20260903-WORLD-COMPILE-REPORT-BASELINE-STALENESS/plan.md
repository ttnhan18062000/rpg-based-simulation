---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS
artifact_type: plan
tags: [content, determinism]
---

# Plan — TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS

## Decision (see investigation.md for full rationale)

Pursue Scope's **Option 2** only (add a process/CI gate) for the `grade_anchors.json` half — per
explicit user choice. Reject batch-regenerating all 81 anchors in this ticket: 61/81 are already
known-drifted, and per this ticket's own Assumptions section, curated grade/score thresholds
deserve per-anchor human review of the biggest swings before being accepted as new baselines, not
a blind batch copy. Regeneration is left as a separate, explicitly-deferred follow-up.

The gate itself reuses fully-existing tooling (`tools/evaluate_simq.py`, `make
simq-full-audit-full`) — zero new Python code needed. The only real gap was that nothing in CI ever
invoked it, so `test_grade_regression.py`'s own anchor tests have silently skipped in every real CI
run to date (confirmed empirically, not assumed — see investigation.md).

## Implementation steps

1. **`.github/workflows/test.yml`**: new `simq-grade-drift` job, mirroring the existing "Type check
   (informational)" job's `continue-on-error: true` pattern and the existing "Slow regression"
   job's push-to-main-only trigger condition (`github.ref == 'refs/heads/main' || schedule ||
   workflow_dispatch`). Runs `make simq-full-audit-full`. **Status: done.**
2. **`tests/simulation_quality/test_grade_regression.py`**: fix the module docstring's broken
   `make calibrate` reference (target doesn't exist — confirmed via `grep` against `Makefile`) and
   point at the real `make evaluate-full`/`tools/calibrate_simq.py` invocations instead; add a CI
   note explaining the new job's purpose so a future reader isn't confused about why this file's
   own tests silently skip locally but a separate CI job exists for the same data. **Status: done.**
3. **AC #1 ("all 81 run_keys confirmed either stale or current")**: satisfied via a real, live
   `tools/evaluate_simq.py` run against current `main` (read-only — diffs against, never mutates,
   `grade_anchors.json`), run locally after confirming the machine was genuinely idle (per this
   session's own established contention-avoidance discipline from the profile-sweep ticket). See
   Test Summary for the confirmed fresh breakdown, superseding the ticket's own 2-day-old sweep
   numbers.
4. **Ticket closure**: update AC checkboxes to reflect what's actually done under the "gate only"
   direction (AC #3, "if regenerated," is N/A; AC #1 and #2 and the conditional #5 "if a gate is
   added" are satisfied).

## Explicitly out of scope for this implementation (per investigation.md + user's chosen direction)
- No `grade_anchors.json` mutation — the 61 confirmed-drifted anchors stay as-is, tracked not fixed.
- No change to the existing PR-gating "Simulation quality" job (adding a real engine re-run there
  would immediately block every PR on already-known drift).
- No investigation into *why* specific pillars/scenarios drifted (M2/M3 behavior changes) — out of
  scope per the ticket's own text, a much larger investigation.
- The 2 `RUN_FAILED` probe run_keys (naming/invocation mismatch, unrelated to staleness) — already
  explicitly out of scope per the ticket.

## Acceptance-criteria map
| AC | Satisfied by |
|---|---|
| All 81 run_keys confirmed either stale or current | Fresh, real `tools/evaluate_simq.py` run (Test Summary) |
| A decision recorded on fix direction | investigation.md + this plan.md (gate only, batch regen deferred) |
| If regenerated: every anchor reproduces... | N/A — not regenerating in this ticket |
| If a gate is added: wired into the After Work/CI pattern | New `simq-grade-drift` CI job (step 1) |
