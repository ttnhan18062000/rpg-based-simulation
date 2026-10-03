---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261001-DELIVERY-REWORK-RATE-MEASUREMENT
phase: done
date: 2026-10-01
tags: [delivery, agent-monitoring]
---

# TCK-20261001-DELIVERY-REWORK-RATE-MEASUREMENT

## Title
Delivery rework rate: first-pass CI rate, failure class and push-after-green count

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
`delivery_cost_measurement.py` reports `gh` calls per PR and subject traceability. It does not say how often a PR needs rework. PR #270's first CI run failed on a gitignored evidence file, and #271 and #272 hit the same live-shard test class. Extend the tool to report rework, read-only.

## Scope
1. Add first-pass CI rate per PR, using `pr_status.py`'s existing CI-state detection and `ci_triage_classifier.py`'s failure classes.
2. Add pushes-after-first-green and failed-then-fixed counts per PR.
3. Keep the tool's rules: `--ref` reads, snapshot caveat, measures a baseline only and never presents an "after" claim.

## Out of Scope
- Judging whether the delivery epic succeeded.
- Any new `gh` call pattern beyond what the classifier already uses (watch the TLS-block trap).

## Acceptance Criteria
1. On a fixture of PR/CI records with one first-pass failure, the rate and class are correct.
2. Output is labelled as a snapshot with the ref and SHA.
3. Existing `delivery_cost_measurement` tests pass unchanged.

## Related Tickets
- TCK-20260924-DELIVERY-COST-MEASUREMENT (done; the tool extended here)

## Related Docs
- `docs/plans/agent_infrastructure/agent_working_direction.md` (update the matching row's status in this ticket's own batch)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/delivery/delivery_cost_measurement.py`, `tools/delivery/pr_status.py`, `tools/delivery/ci_triage_classifier.py`

## Assumptions / Open Questions
- Open: where the per-PR CI history comes from without an extra `gh` call per PR; check what `pr_status.py` already returns.

## Implementation Notes
Extended `tools/delivery/delivery_cost_measurement.py` with an opt-in `--rework` section (default report unchanged). PRs = squash subjects `(#N)` reachable from `--ref` in the week range. Per-PR CI history needs two `gh api` list calls, answering the ticket's open question: `actions/runs` (same endpoint pr_status.py uses) and closed `pulls`; a first version that relied on a run's own `pull_requests` field found 0 of 42 PRs on the real repo because GitHub empties it after the branch is deleted, so runs are matched to PRs by branch name instead. Failed runs only get job detail via `pr_status._fetch_failing_job_details` and are classified by `ci_triage_classifier.classify_failing_job` with the PR's changed files from `git show` of its merge commit; capped at 20 runs. Metrics: first-pass CI rate (first SHA passed, no re-run), failed-then-fixed PRs, pushes after first green, re-run attempts, failure classes. A re-run (run_attempt > 1) counts as rework. If `gh` fails the section says CI history is unavailable instead of reporting zeros. Known limit: REAL_REGRESSION needs the changed-files signal, which is the PR's final diff, not the failing push's.
NO real-corpus reading was obtained: two attempts at `--ref origin/main --since-week 2026-W39 --rework` both failed with the closed-PR list call timing out at 30 s (connection resets on large GitHub payloads from this network; 5-PR and 30-PR pages worked when tried by hand). The tool reported 'unavailable', as designed. The numbers exist only for fixtures.
Draft by agent-working-design; the implementer commits it.

## Test Summary
tests/tools/test_delivery_cost_measurement.py: 17 passed (11 existing unchanged, 6 new). New: one first-pass failure gives the right rate (0.5), failed-then-fixed, pushes-after-green and a class (AC1); a re-run counts as rework; output carries ref, SHA and the snapshot caveat plus the baseline-only statement (AC2); unreachable gh reports unavailable; rework is opt-in and the default report has no rework key; only the two gh api list calls are made when nothing failed. Existing tests pass unchanged (AC3).
Not started.

## Files Changed
- `tools/delivery/delivery_cost_measurement.py`
- `tests/tools/test_delivery_cost_measurement.py`
- `docs/agent-monitoring/README.md`, `docs/plans/agent_infrastructure/agent_working_direction.md`
None yet.

## Completion Summary
Rework measurement ships and is tested on fixtures; a real baseline reading is still outstanding because of network timeouts and should be retried from a healthier network.
Not started.
