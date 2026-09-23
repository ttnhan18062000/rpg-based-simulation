---
status: active
layer: ai
authority: P1
audience: agent
date: 2026-09-23
tags: [ai, agent-monitoring, governance]
---

# Experiment Specification — Task-Success-Rate Metric Closing the Improvement Loop

**Tracking ticket**: none — Bucket-B items never convert directly to production implementation
tickets. Per the freeze verdict's handoff boundary, this is the correct deliverable shape:
`Frozen Architecture Proposal → Experiment Specification → Hypothesis / Baseline / Method /
Metrics / Exit Criteria / Kill Criteria → Run Experiment → Decision`. Scoped into a spec document
by `TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC`.
**Source**: `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` Rev.3, Bucket C item 19 — "Task-
success-rate metric closing the improvement loop". Was blocked on
`agent_evaluation_foundation_experiment.md` (item 13) proving its scoring approach repeatable; that
pilot completed 2026-09-07 (`TCK-20260907-FILTERED-REPLAY-EVAL-PILOT`) with all 3 Exit Criteria
MET, no Kill Criterion fired — the prerequisite is cleared.
**Roadmap**: `roadmap.md` — Horizon 3, "C — Future option", listed as blocked pending item 13; now
unblocked, still not implemented (this doc is the Experiment Specification step, not the metric's
actual build).
**Priority**: P2 — closes the retro-loop measurement gap; not a structural correlated-failure risk
item.

## Why this is an experiment, not an epic

Writing or running this produces no agent behavior change by itself. The output is evidence: can a
before/after task-success-rate comparison, built from item 13's own scoring vocabulary, reliably
tell whether an agent-prompt change helped, hurt, or was neutral? If yes, this becomes a standing
tool the retro loop can reuse for future prompt changes. If no — noisy or non-repeatable at
practical sample sizes — that negative result is itself the useful outcome, same posture item 13
took for its own pilot.

## Hypothesis

A task-success-rate metric, built from item 13's own scoring vocabulary (gate-failure rate from
`agent-monitoring/*/runs.jsonl`'s terminal statuses, plus the 2 known recurring defect-class flag
rates from `tools/agent_replay/defect_detectors.py`), computed before and after a real agent-prompt
change over a comparable replayed sample, produces a real, reportable delta — not noise — that a
retro reader can act on when deciding whether to keep, revert, or iterate on a prompt change.

## Baseline (item 13's real, already-executed results — reused, not re-derived)

- **Source**: `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/results.md` and
  `agent_evaluation_foundation_experiment.md`'s own appended `## Results`/`## Decision` sections.
- **Gate-failure-rate baseline**: item 13's own real-corpus figure (freshly re-derived at that
  pilot's own execution time, per its Acceptance Criteria requirement to measure live rather than
  cite stale numbers — this spec inherits that same "measure live at execution time" discipline
  rather than hardcoding item 13's specific figure here, since it will itself be stale by the time
  this metric actually runs).
- **Defect-class flag rate baseline**: item 13's M2 (doc-update self-report gap) and M3
  (test-scoper background-hang pattern) detection results — 0/5 fired for M2 on the real converted
  sample, a real disclosed finding at n=5 (thin sample, stated as a limitation in item 13's own
  results, not smoothed over).
- **`weight_sensitivity_check.py`'s existing pattern** (`TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE`):
  the precedent this metric extends. Its real mechanism: for every real `(run_id, seq)` tool-call
  group, compute a score under a baseline and a candidate configuration, bucket by `phase`/`agent`,
  report the before/after comparison. **What transfers to this metric**: the baseline-vs-candidate
  comparison structure over real event data, bucketed and reported per phase/agent. **What does
  NOT transfer directly**: `weight_sensitivity_check.py` compares RANK ORDER (via Spearman
  correlation) because `cost_proxy_score` is a unitless proxy with no ground truth
  (`docs/agent-monitoring/schema.md`'s own `cost_proxy_score` section states this explicitly).
  Task success has ground truth (a ticket did or didn't trigger a gate failure; a defect class was
  or wasn't flagged) — this metric compares before/after rates DIRECTLY, not just their rank order.

## Method

1. **Define the metric from item 13's own vocabulary, not a new one**: task-success-rate =
   1 − gate-failure rate (DOD_BLOCKED, NEEDS_HUMAN_INPUT, NEEDS_CHANGES, CONFLICTS_DETECTED,
   TESTS_FAILED, and related terminal statuses), reported alongside the 2 known defect-class flag
   rates as a secondary breakdown — never pooled into one opaque number, per item 13's own
   "three tiers, not one global number" metrics discipline.
2. **Re-run, don't just re-score**: unlike a `cost_proxy.py` weight change (a pure re-scoring of
   already-recorded `tools.jsonl` rows under new weights, no re-execution needed), a prompt change
   alters what the agent actually produces — there is no way to re-score old output under a new
   prompt. Replay the sample twice: once under the current agent prompt (baseline), once under the
   changed prompt (candidate), reusing `tools/agent_replay/`'s existing sampler
   (`sampler.py::build_sample_manifest()`), fixture converter, and isolation infrastructure
   (`pilot_isolation.py`) rather than building a second replay harness.
3. **Isolate**, same requirement and same evidence shape as item 13's own Method step 3 — an
   isolated worktree, session-scoped sidecar only, never the shared `.claude/current_run` path.
4. **Compute before/after directly**: gate-failure-rate delta and each defect-class flag-rate delta
   between the two runs, on the SAME sample — this is the direct-comparison extension of
   `weight_sensitivity_check.py`'s structure, adapted for a metric that has ground truth.
5. **Bucket by phase/agent where sample size supports it**, mirroring
   `weight_sensitivity_check.py`'s own `by_phase`/`by_agent` breakdown shape — report per-bucket
   deltas, not only one pooled figure, so a retro reader can see which phase/agent the prompt
   change actually affected.
6. **Report a before/after summary**, structurally similar to `weight_sensitivity_check.py`'s own
   CLI report table (bucket, n, baseline value, candidate value, delta) — reused shape, new
   underlying metric.

## Metrics — three tiers, matching item 13's shape

- **Primary**: before/after gate-failure-rate delta and defect-class flag-rate delta, both overall
  and per phase/agent bucket where sample size supports it.
- **Safety**: same replay-isolation contamination check item 13 already built and validated.
- **Efficiency**: wall-clock/cost delta between the two runs — informative only, not pass/fail.

**Terminology discipline**, inherited from item 13's own freeze-pass correction: only claim what's
directly observed on the actual sample (a measured delta) or repeatable (if run more than once).
Do not claim this metric generalizes to prompt changes beyond what was actually tested.

## Exit criteria (what "the metric works" means)

1. The before/after comparison produces a real, reportable delta (not indistinguishable from noise)
   on at least one real prompt-change scenario, at a sample size stated explicitly (not assumed).
2. The metric definition proves reusable across at least 2 different prompt-change scenarios — a
   one-off number for a single change would not establish it as a standing retro-loop tool.
3. Replay isolation held (same requirement, same evidence shape as item 13's own Exit Criterion 3).

Meeting all three establishes the metric as a reusable retro-loop tool — it does not itself change
any agent prompt in production; that decision (keep/revert/iterate) is made by whoever ran the
specific prompt-change comparison, using this metric as the tool, not by this spec.

## Kill criteria (when to stop investing)

- Scores are noisy/non-repeatable even on a clean, small, isolated sample — same posture item 13's
  own Kill Criterion #1 took for the underlying scoring approach; if the vocabulary this metric
  extends can't produce a trustworthy signal here either, scaling up the sample first would only
  compound an unproven method (§69's own warning, inherited).
- Replay isolation cannot fully eliminate shared-sidecar contamination risk in practice — same
  Kill Criterion #2 item 13's own spec carried, inherited unchanged since this metric reuses the
  same replay infrastructure.

If either kill criterion fires, the result is reported as a negative finding — not silently
abandoned or quietly rescoped into a smaller claim.

## Out of scope

- Any change to `tools/agent-monitoring/cost_proxy.py` — this spec extends its comparison
  *pattern*, not its formula or weights.
- Any change to `tools/agent-monitoring/weight_sensitivity_check.py` — read for reference only.
- Building the actual metric-computation code or a CLI tool for it — that is later, separate work
  once this spec is reviewed.
- Choosing a specific real agent-prompt change to test against — deferred to implementation time.
- Any claim about which prompt change is "better" for any real agent — this spec describes how to
  measure, not a recommendation about what to change.

## References

- `bucket_c_future_options.md` — item 19's original blocked entry and "When it clears" guidance,
  the direct source this spec is written from.
- `agent_evaluation_foundation_experiment.md` — the six-section shape template, the scoring
  vocabulary (gate-failure rate, defect-class flag rate) this metric extends, and the "three tiers,
  not one number" metrics discipline.
- `tools/agent-monitoring/weight_sensitivity_check.py` — the existing before/after comparison
  pattern this metric extends the STRUCTURE of (not its rank-correlation statistic).
- `docs/agent-monitoring/schema.md`'s `cost_proxy_score` section — why the existing pattern compares
  rank order rather than absolute values, and why this metric can compare directly instead.
- `roadmap.md` — item 19's Horizon-3 placement.
- `tools/agent_replay/` — the sampling/replay/isolation infrastructure this metric's re-run step
  reuses.
- `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/results.md` — the real baseline data
  this spec's Baseline section cites.
