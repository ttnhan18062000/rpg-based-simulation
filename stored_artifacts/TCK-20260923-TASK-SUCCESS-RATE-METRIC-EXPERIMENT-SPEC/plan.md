---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC
artifact_type: plan
tags: [ai, agent-monitoring, governance]
---

# Plan — TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC

## Approach
Write one new doc, `docs/plans/agent_infrastructure/ai_first_hardening_epics/task_success_rate_metric_experiment.md`,
mirroring `agent_evaluation_foundation_experiment.md`'s section shape. The Method section correctly
extends `weight_sensitivity_check.py`'s STRUCTURE (baseline vs. candidate comparison over real
event data, bucketed and reported per phase/agent) rather than its rank-correlation statistic,
since task success has ground truth and cost_proxy_score deliberately does not (see
investigation.md). Update `bucket_c_future_options.md`'s item-19 entry with a link once the doc
exists.

## Steps

1. **Header block**: Tracking ticket (none), Source (item 19, cleared per item 13's MET exit
   criteria), Roadmap (Horizon 3 per `roadmap.md` — confirm exact label before writing), Priority
   (P2 — a retro-loop closing metric, not a structural risk item).
2. **Hypothesis**: a task-success-rate metric, built from item 13's own vocabulary (gate-failure
   rate + the 2 known defect-class flag rates), can be computed before/after an agent-prompt change
   over a comparable replayed sample, giving a concrete signal for whether the change helped, hurt,
   or was neutral — framed as testable.
3. **Baseline**: item 13's real gate-failure-rate figure (from `agent-monitoring/*/runs.jsonl`'s
   terminal statuses) and its own M2/M3 defect-class detection results — cite the actual numbers,
   don't re-derive a third baseline.
4. **Method**: (a) state explicitly that this extends `weight_sensitivity_check.py`'s STRUCTURE
   (baseline-vs-candidate comparison over real event data, phase/agent bucketing, a clear
   before/after report) rather than reusing its rank-correlation statistic verbatim — a metric with
   ground truth compares directly, it doesn't need rank-order-only comparison the way an
   unitless-proxy weight change does; (b) because a prompt change alters agent OUTPUT (unlike a
   weight change, which re-scores already-recorded data), re-running/replaying the sample under
   both the current and changed prompt is required — reuse `tools/agent_replay/`'s existing
   sampler/fixture-converter/isolation infrastructure for that re-execution, not a new harness;
   (c) compute gate-failure rate and the 2 known defect-class flag rates for both runs; (d) report
   the before/after delta per metric, bucketed by phase/agent where the sample size supports it.
5. **Metrics**: mirror item 13's tiered shape — Primary (before/after gate-failure-rate delta and
   defect-class flag-rate delta), Safety (same replay-isolation contamination check item 13 already
   validated), Efficiency (wall-clock/cost delta — informative only).
6. **Exit criteria**: the before/after comparison produces a real, reportable delta (not
   inconclusive/noisy) on a sample large enough to trust; the metric definition itself proves
   reusable across at least 2 different prompt-change scenarios (not a one-off).
7. **Kill criteria**: scores too noisy/non-repeatable to trust at this sample size (same posture
   item 13's own Kill Criterion #1 took) — report negative, don't silently narrow the claim.
8. **Out of scope**: no `cost_proxy.py` change; no `weight_sensitivity_check.py` change; no actual
   metric-computation code shipped by this ticket — the spec only.
9. **References**: `bucket_c_future_options.md`, `agent_evaluation_foundation_experiment.md`,
   `weight_sensitivity_check.py`, `docs/agent-monitoring/schema.md`'s `cost_proxy_score` section,
   `roadmap.md`, `tools/agent_replay/`.
10. **Update `bucket_c_future_options.md`**: item-19 entry gets a link to the new spec doc.

## Risk / Rollback
Pure documentation addition — no code path, trivially revertible via `git revert`.

## Test Plan Reference
See `test_plan.md` in this same directory.
