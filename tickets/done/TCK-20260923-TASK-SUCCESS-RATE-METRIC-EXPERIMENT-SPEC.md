---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC
phase: done
date: 2026-09-23
tags: [ai, agent-monitoring, governance]
---

# TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC

## Title
Task-success-rate metric closing the improvement loop — Experiment Specification (Bucket-C item 19)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`bucket_c_future_options.md`'s "Task-success-rate metric closing the improvement loop" entry was
blocked on `agent_evaluation_foundation_experiment.md` (item 13) proving its scoring approach
repeatable — that pilot completed with all 3 Exit Criteria MET
(`TCK-20260907-FILTERED-REPLAY-EVAL-PILOT`, done 2026-09-07), so item 19 is now unblocked per the
doc's own "When it clears" note: "extend `tools/agent-monitoring/cost_proxy.py`'s existing
before/after comparison pattern (already used for cost-proxy weight changes) to agent-prompt
changes generally." This ticket writes that Experiment Specification document — a spec, not a
`cost_proxy.py` change.

## Scope
- Read `tools/agent-monitoring/cost_proxy.py` and `tools/agent-monitoring/weight_sensitivity_check.py`
  (the actual existing before/after comparison tool — computes `cost_proxy_score` under two weight
  sets, compares spend-by-phase/spend-by-agent rank order via Spearman correlation) before writing
  the spec, so the Method section matches what the existing pattern really does rather than an
  assumed shape.
- Write a new Experiment Specification at
  `docs/plans/agent_infrastructure/ai_first_hardening_epics/task_success_rate_metric_experiment.md`,
  following the same six-section shape `agent_evaluation_foundation_experiment.md` (item 13) used:
  header (Tracking ticket / Source / Roadmap / Priority), Hypothesis, Baseline, Method, Metrics,
  Exit Criteria, Kill Criteria, Out of Scope, References.
- The Method must extend `weight_sensitivity_check.py`'s baseline-vs-candidate comparison pattern
  from cost-proxy weight changes to agent-prompt changes generally: baseline = task outcomes
  (gate-failure rate, defect-class flag rate per item 13's own metric vocabulary) under the current
  agent prompt; candidate = the same outcomes under a changed prompt, over a comparable sample of
  real or replayed tickets. Reuse item 13's replay infrastructure (`tools/agent_replay/`) as the
  sampling/replay mechanism where it fits, rather than inventing a second one.
- Update `bucket_c_future_options.md`'s item-19 entry to link the new spec doc.

## Out of Scope
- Any change to `tools/agent-monitoring/cost_proxy.py` itself — this ticket writes a spec that
  extends its comparison *pattern*, not its formula or weights.
- Any change to `tools/agent-monitoring/weight_sensitivity_check.py` — read for reference only.
- Building the actual task-success-rate metric or scoring code — that is later, separate work once
  this spec is reviewed.
- Scoping item 18 (model routing) — sibling ticket
  `TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC` in this same batch.
- Re-deriving or second-guessing item 13's own Hypothesis/Metrics/Exit/Kill Criteria — this spec
  extends the pattern item 13 established, it does not re-litigate it.

## Acceptance Criteria
- [x] `docs/plans/agent_infrastructure/ai_first_hardening_epics/task_success_rate_metric_experiment.md`
      exists with all six sections (Hypothesis/Baseline/Method/Metrics/Exit/Kill), plus Out of
      Scope and References, matching item 13's spec shape.
- [x] The Method section accurately describes `weight_sensitivity_check.py`'s real
      baseline-vs-candidate comparison mechanism (verified by reading the tool, not assumed) and
      explains concretely how it extends to agent-prompt changes generally (task outcomes in place
      of weight-derived scores).
- [x] `bucket_c_future_options.md`'s item-19 entry links to the new spec doc.
- [x] `## Related Tickets` links back to `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC`.

## Related Tickets
- `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC` (`tickets/todos/`, `EPIC_SCOPED`) — the Bucket
  B/C tracking epic this item (roadmap item 19) is enumerated under.
- `TCK-20260907-FILTERED-REPLAY-EVAL-PILOT` (done) — the eval pilot (item 13) whose scoring
  approach this spec extends.
- `TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE` (done) — built
  `tools/agent-monitoring/weight_sensitivity_check.py`, the existing before/after pattern this spec
  extends.
- `TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON`,
  `TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC` (this batch, `tickets/todos/`) —
  sibling tickets, independent of this one.

## Related Docs
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md` — item 19's
  existing blocked entry, the source this spec is written from.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/agent_evaluation_foundation_experiment.md`
  — the six-section shape template and the scoring vocabulary (gate-failure rate, defect-class flag
  rate) this metric extends.
- `docs/agent-monitoring/schema.md`'s `cost_proxy_score` section — the formula/interpretation
  context for the existing pattern being extended.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` — item 19's roadmap
  placement.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/` — the scoring approach this spec
  extends.

## Related Code Areas
- `tools/agent-monitoring/cost_proxy.py`, `tools/agent-monitoring/weight_sensitivity_check.py` —
  read-only reference for the Method section; neither is modified.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/` — new spec doc lands here.

## Assumptions / Open Questions
- None — item 13's exit criteria are already MET per its own recorded Results/Decision section,
  and `weight_sensitivity_check.py` is real, shipped code available to read directly rather than
  inferred from the doc's summary.

## Implementation Notes
Read `tools/agent-monitoring/weight_sensitivity_check.py` in full before writing the spec, per this
ticket's own Scope requirement. Its real mechanism compares RANK ORDER of `cost_proxy_score` under
two weight sets across real `(run_id, seq)` groups, because `cost_proxy_score` is a unitless proxy
with no ground truth. Task success has ground truth (a ticket either did or didn't trigger a gate
failure), so the spec explicitly distinguishes what it reuses from the existing pattern — the
baseline-vs-candidate comparison STRUCTURE over real event data, bucketed and reported per
phase/agent — from what it does not reuse verbatim — the rank-correlation-only comparison itself,
replaced with a direct before/after rate comparison since ground truth is available.

Also identified, and stated explicitly in the spec, a structural difference the source doc's
one-line "extend the pattern" instruction doesn't call out: a cost-proxy weight change re-scores
already-recorded `tools.jsonl` rows under new weights (no re-execution), while a prompt change
alters agent OUTPUT — there is no way to re-score old output under a new prompt. The spec's Method
therefore requires re-running/replaying the sample under both prompts, reusing item 13's
`tools/agent_replay/` infrastructure for that re-execution rather than `weight_sensitivity_check.py`'s
own no-re-execution trick.

Linked the new spec doc from `bucket_c_future_options.md`'s item-19 entry, and updated
`roadmap.md`'s item-19 row (unblocked, links the new spec) alongside item 18's own row (both edited
in this ticket's turn since they sit in the same table and were both cleared by the same underlying
event — item 13's exit criteria being MET).

## Test Summary
No automated tests apply — documentation-only diff. Verified per `test_plan.md`'s manual checklist:
all six sections present, the reuse/non-reuse distinction from `weight_sensitivity_check.py` stated
explicitly, the re-execution requirement explained, `bucket_c_future_options.md` links to the new
doc — confirmed by direct read-through and grep after writing.

## Files Changed
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/task_success_rate_metric_experiment.md`
  — new, the Experiment Specification.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md` — item-19
  entry updated with a link to the new spec doc.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` — item 19's row updated
  from "H3, blocked" to unblocked, linking the new spec doc (item 18's row updated in the same
  edit, attributed to the sibling ticket's Files Changed).
- `staging_artifacts/TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC/` — new:
  `investigation.md`, `plan.md`, `test_plan.md`.
- `tickets/todos/TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC.md` — deleted (superseded
  by this file).

## Completion Summary
Wrote the Bucket-C item 19 Experiment Specification per `bucket_c_future_options.md`'s own "When it
clears" guidance, now that item 13's eval pilot exit criteria are MET. The spec correctly extends
`weight_sensitivity_check.py`'s comparison structure rather than assuming its rank-correlation
statistic transfers unchanged — task success has ground truth, `cost_proxy_score` deliberately does
not, so the spec compares before/after rates directly. It also identifies and states plainly a
structural gap the source doc's brief instruction didn't cover: a prompt change requires
re-execution, unlike a pure weight re-scoring, so the Method reuses item 13's replay infrastructure
for that re-run. No `cost_proxy.py` or `weight_sensitivity_check.py` changes were made — the spec
only.
