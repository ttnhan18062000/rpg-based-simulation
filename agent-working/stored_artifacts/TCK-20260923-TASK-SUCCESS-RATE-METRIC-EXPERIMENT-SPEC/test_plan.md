---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC
artifact_type: test_plan
tags: [ai, agent-monitoring, governance, testing]
---

# Test Plan — TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC

## Scope
Documentation artifact only — no code changes, so no `pytest` coverage applies. Verification is a
structural/content review of the spec doc itself.

## Checks (manual, not automated)
1. The new doc at
   `docs/plans/agent_infrastructure/ai_first_hardening_epics/task_success_rate_metric_experiment.md`
   contains all six required sections (Hypothesis, Baseline, Method, Metrics, Exit criteria, Kill
   criteria) plus Out of scope and References, matching `agent_evaluation_foundation_experiment.md`'s
   shape — verified by direct read-through after writing.
2. The Method section accurately describes `weight_sensitivity_check.py`'s real mechanism (verified
   against the actual module source in investigation.md, not assumed) and explicitly distinguishes
   what's reused (the baseline-vs-candidate comparison structure) from what's NOT reused
   (rank-correlation-only comparison, since task success has ground truth and `cost_proxy_score`
   deliberately does not) — verified by grep for both `weight_sensitivity_check.py` and the
   distinction language in the finished doc.
3. The Method explains why re-running/replaying the sample under both prompts is required (unlike
   the weight-change pattern's re-scoring-without-re-execution trick) — verified by reading the
   finished doc's Method section for this reasoning.
4. `bucket_c_future_options.md`'s item-19 entry links to the new spec doc — verified by grep.

## Out of Scope
- No automated test file — nothing here exercises code. `make knowledge-index-update` runs at
  Finalize per the standard "docs changed" rule.
