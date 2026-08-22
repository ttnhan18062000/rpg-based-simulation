---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2
phase: open
date: 2026-08-22
tags: [testing]
---

# TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2

## Title
"Slow regression" CI job (push-to-main only) has failed with exit code 2 on 4 of the last 7 runs

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`.github/workflows/test.yml`'s `slow` job ("Slow regression", `if: github.ref ==
'refs/heads/main' || github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'`
— runs only on push to `main`, never on PR checks, which is why this was not caught by any of
this session's PR-gated CI checks) has failed with **exit code 2** on 4 of the last 7 push-to-main
runs over the past 2 days (run ids 32396405501, 32519599280, 32551803106, 32561870598 — all
"Process completed with exit code 2" per the GitHub check-run annotations, no further detail
visible via `gh api .../annotations` alone). Exit code 2 (vs. 1) suggests a deterministic/systemic
error — e.g. a pytest collection failure, an internal `make` target failure, or an environment
setup problem — rather than ordinary flaky test assertions, though this has not yet been confirmed
by an actual full local reproduction (the job runs 3 heavy steps totaling an estimated 45-90
minutes: `make simq-corpus-diversity-slow-isolated`, `pytest tests/ -m "slow or extra_slow"
--resource-budget large --tb=short -q --ignore=tests/unit/worldassembly/test_corpus_diversity.py`,
and `make lane-legacy-regression`).

**Confirmed NOT caused by any of this session's own changes**: the failure reproduces identically
on commit `5894f8bb` (2026-08-21, predates this session's work) and recurs on the current `main`
tip after this session's own PRs merged cleanly on every job that actually gates PR mergeability.
Both `simq-corpus-diversity-slow-isolated` and `lane-legacy-regression` are confirmed to still
exist as valid `Makefile` targets (not a broken/renamed reference) — the root cause is genuinely
unknown, not yet diagnosed to which of the 3 steps or which specific test/assertion is failing.

## Scope
- Reproduce the job's exact 3-step sequence locally (or via a scoped `workflow_dispatch` run) to
  identify exactly which step and which test/assertion produces exit code 2.
- Fix the real root cause once identified.
- If the root cause turns out to be genuine environment-dependent flakiness (not a real bug),
  document it in `docs/testing/regression_policy.md` as a known category, matching the existing
  precedent for other documented flaky-test categories (e.g. live-server subprocess tests) — do
  not leave it undocumented either way.

## Out of Scope
- Changing the job's trigger conditions (push-to-main-only, per
  `TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH`'s deliberate decision to keep this off the
  PR-blocking path) — that decision is not being revisited here.
- Fixing any other CI job's unrelated flakiness (e.g. `API / tools / logging`'s separate,
  already-known live-server/websocket/CLI-subprocess/knowledge-gateway environment-noise
  category — different job, different symptom, not this ticket's scope).

## Acceptance Criteria
- [ ] Root cause identified: which of the 3 steps (`simq-corpus-diversity-slow-isolated`, the main
      `pytest tests/ -m "slow or extra_slow"` invocation, or `lane-legacy-regression`) produces
      exit code 2, and the specific underlying error.
- [ ] Either a real fix lands (if a genuine bug), or the failure category is documented in
      `docs/testing/regression_policy.md` as known environment-dependent noise (if that's what
      investigation reveals) — not left silently unresolved either way.
- [ ] The next several push-to-main "Slow regression" runs are confirmed green (or, if
      environment-dependent, behave consistently with the newly-documented policy).

## Related Tickets
None — discovered as a byproduct of monitoring CI health during
TCK-20260821-WORLD-RENDER-CORE's PR merge flow, not tied to any prior ticket.

## Related Docs
- docs/testing/regression_policy.md
- .github/workflows/test.yml

## Related Stored Artifacts
None yet.

## Related Code Areas
- .github/workflows/test.yml (the `slow` job definition)
- Makefile (`simq-corpus-diversity-slow-isolated`, `lane-legacy-regression` targets)

## Assumptions / Open Questions
- Whether this is a real, fixable bug or genuine environment-dependent flakiness under CI's
  specific resource constraints (45-90 min heavy suite) is the central open question this
  ticket's own investigation must resolve — not assumed either way here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
