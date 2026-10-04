---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-PR-STATUS-FALSE-GREEN-ON-STANDALONE-CHECK-RUNS
artifact_type: plan
tags: [ai, process-improvement]
---

# Plan

Hand-orchestrated; written after the investigation, kept in step with what shipped.

1. Keep the workflow-runs verdict as stage 1 (unchanged).
2. Stage 2 `_evaluate_contexts`: paginate `commits/<sha>/check-runs` and `commits/<sha>/status` by hand (`gh api --paginate` emits concatenated JSON documents); short or over-cap pagination is an error.
3. Check runs whose `details_url` run id belongs to another workflow's run keep the existing "reported separately, does not vote" rule.
4. Cross-check and required-check read via `gh pr checks` text output (gh 2.45 has no `--json` there; parsed regardless of exit code).
5. `_apply_contexts` only makes the verdict stricter: failing context -> FAILING (named, annotations fetched); fetch error / unexamined required / gh-only context -> UNKNOWN; pending -> PENDING.
6. Print `contexts_examined`; document the completeness rule in `docs/guides/delivery_process.md`.

Out of scope held: no write call, no change to which checks are required, no CI workflow edit.
