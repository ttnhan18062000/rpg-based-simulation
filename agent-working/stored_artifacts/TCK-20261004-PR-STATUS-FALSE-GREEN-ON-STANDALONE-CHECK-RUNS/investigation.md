---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-PR-STATUS-FALSE-GREEN-ON-STANDALONE-CHECK-RUNS
artifact_type: investigation
tags: [ai, process-improvement]
---

# Investigation

- Cause confirmed in `compute_pr_status`: the only CI source was `actions/runs?head_sha=` partitioned to one workflow path, so a standalone check run (`ruff`) was never read.
- Reproduced live: replaying PR #291's reported head `65731e0c9b72` against the real API with only `pr view` overridden. Old code: GREEN. New code: FAILING naming `ruff (check-run)`, annotations at `src/ai/goals/scorers.py:105-106` ("`import` should be at the top-level of a file").
- `gh pr checks` on gh 2.45: no `--json`; tab-separated text `name, bucket, duration, url`; exits 1 while anything fails or is pending, so stdout is parsed regardless of exit code. `--required` prints "no required checks reported" here (no branch protection), so that branch is verified by tests only.
- A second false-green path found while polling CI by hand: an empty `gh pr checks` output caused by a TLS block on `api.github.com` read as "settled". The tool's cross-check treats an empty/unparseable result as an error, never as no failures.
- `commits/<sha>/status` with zero statuses reports `state: pending, total_count: 0`; only individual statuses vote, never the combined state.
