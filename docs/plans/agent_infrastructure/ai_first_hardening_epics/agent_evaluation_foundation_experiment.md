---
status: active
layer: ai
authority: P1
audience: agent
date: 2026-09-04
tags: [ai, agent-monitoring]
---

# Experiment Specification — Agent Evaluation Foundation

**Tracking ticket**: none — Bucket-B items never convert directly to production implementation
tickets. Per the freeze verdict's handoff boundary, this is the correct deliverable shape for this
work: `Frozen Architecture Proposal → Experiment Specification → Hypothesis / Baseline / Method /
Metrics / Exit Criteria / Kill Criteria → Run Experiment → Decision`.
**Source**: `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` Rev.3, epic grouping "Agent Evaluation
Foundation" — filtered replay eval pilot + dataset stratification/holdout split + safety/
optimization metric design, treated as one inseparable unit (the corpus, its split, and the
scoring rule cannot be designed apart without risking a pilot that can't be trusted even if it
runs).
**Roadmap**: `roadmap.md` — Horizon 1. Unblocks the largest number of downstream Bucket-C items
(model routing, task-success-rate metric, full eval platform) — see the roadmap's dependency
notes.
**Priority**: P1 — this is the single highest-leverage piece of evidence-generating work in the
frozen proposal: every quality-sensitive future initiative is gated behind it.

## Why this is an experiment, not an epic

No agent behavior changes as a result of running this. Its entire output is evidence: does a small
replay of historical tickets produce a repeatable, trustworthy signal at all? If yes, later work
(model routing, a task-success-rate metric, a fuller eval platform) can build on it. If no, those
downstream items stay blocked and this experiment's negative result is itself the useful outcome.

## Hypothesis

A small, stratified sample of historical closed tickets, replayed through `implement-ticket.js`'s
investigation/plan/implement phases in isolation, can be scored against known recurring defect
classes with **repeatable** results (the same configuration scores the same way across 2
independent runs) — even though it cannot yet be scored for **absolute accuracy** against every
possible defect type, because no adjudicated ground-truth labels exist for that broader claim.

## Baseline (Level A data, already available — no new measurement needed to start)

- **Corpus size**: `tickets/done/` holds 1,752 top-level ticket files (1,331 standard-tier, 292
  hotfix-tier, 45 epic-tier).
- **Artifact coverage**: 1,099 of the 1,331 standard-tier tickets (82.6%) have a complete matching
  `stored_artifacts/{id}/` directory (investigation.md/plan.md/test_plan.md) — this is the eligible
  pool, not the pilot sample size.
- **Real failure-rate baseline**: `agent-monitoring/runs.jsonl` (1,388 total records) shows a 6.3%
  baseline gate-failure rate (DOD_BLOCKED, NEEDS_HUMAN_INPUT, NEEDS_CHANGES, CONFLICTS_DETECTED,
  TESTS_FAILED, and related terminal statuses combined).
- **Two known, independently-confirmed recurring defect classes** to check replay detection
  against (both read in full from real retro reports this session): the doc-update self-report gap
  and the test-scoper background-hang pattern (see `guardrail_enforcement_epic.md` for the full
  evidence trail on both).

## Method

1. **Sample, deliberately small** (§69 of the source proposal — a small trusted benchmark beats a
   large untrusted one): 20–40 tickets, not the full 1,099-ticket eligible pool. Stratify across:
   - Tier (already known from ticket frontmatter).
   - `layer` (a real proxy for architecture-heavy vs. test-heavy vs. retrieval-heavy work).
   - Success/failure (the ~88 known-failed runs in `runs.jsonl` give a real "failed tasks" stratum
     to sample from, alongside successful DONE tickets).
2. **Dataset hygiene**: split the sample into development (used while building/tuning the scoring
   approach), validation (held aside during tuning, checked once), and an untouched holdout (never
   touched until the pilot is declared trustworthy) — roughly 60/20/20 or similar, adjusted to the
   final sample size.
3. **Replay in strict isolation**: an isolated worktree, using `implement-ticket.js`'s
   session-scoped sidecar exclusively — never the shared unscoped `.claude/current_run` path (see
   `workflow_reliability_epic.md`'s M1 for why that matters; do not run this experiment before that
   milestone lands, or schedule the replay to strictly avoid overlapping live sessions in the
   meantime).
4. **Score for repeatability first**: run the same configuration twice against the same sample;
   compare scores. Repeatability, not absolute accuracy, is this pilot's bar.
5. **Periodically refresh**: add newer closed tickets to the eligible pool over time so the
   benchmark doesn't stagnate against a fixed corpus snapshot.

## Metrics — three tiers, not one global number

Per the frozen proposal's evaluation design (§65, preserved through the freeze pass):

- **Primary**: does the replay correctly flag the 2 known recurring defect classes, consistently,
  across 2 independent runs?
- **Safety**: does the pilot's own execution avoid contaminating any concurrent live session's
  sidecar state (a real, named risk, not hypothetical — see Method step 3)?
- **Efficiency**: wall-clock time and tool-call volume for the replay itself — informative for
  scaling decisions later, not a pass/fail bar for this pilot.

**Terminology discipline** (per the freeze pass's evaluation-terminology correction): only claim
what's directly observed (block/flag rate on the 2 known classes) or repeatable (score consistency
across runs). Do not claim a "false-pass" or "false-block" rate for anything beyond the 2 known
classes — that would require adjudicated ground truth this pilot does not produce for the general
case.

## Exit criteria (what "the pilot worked" means)

1. Repeatable scoring established — the same configuration scores the same on 2 independent runs.
2. Sample quality accepted for the 2 target defect classes specifically (not claimed for defect
   classes beyond those two).
3. Replay contamination risk is understood and demonstrably controlled in the pilot's own
   execution (Method step 3's isolation actually held, not just planned).

Meeting all three unblocks the Bucket-C items gated on this experiment (see `roadmap.md` and
`bucket_c_future_options.md`) — it does not itself implement them.

## Kill criteria (when to stop investing)

- Scores are noisy/non-repeatable even on this clean, filtered, small sample — the signal isn't
  real at this scale, and scaling up first (a larger benchmark) would only compound an unproven
  method, per §69's own warning against exactly that trap.
- Worktree isolation cannot fully eliminate the shared-sidecar contamination risk in practice —
  if `workflow_reliability_epic.md`'s M1 fix doesn't hold up under real replay conditions, this
  experiment should pause rather than proceed on a known-contaminated state path.

If either kill criterion fires, the result is reported as a negative finding — not silently
abandoned, and not quietly rescoped into a smaller claim without saying so.

## Out of scope

- Widening sample coverage or building a general eval platform before this pilot's exit criteria
  are met — see `bucket_c_future_options.md`'s "Full agent-behavior eval platform" entry.
- Deriving a task-success-rate metric for the retro loop from this pilot's results — that's a
  separate, larger Bucket-C item gated on this one succeeding, not a byproduct this experiment
  produces automatically.
- Any change to `implement-ticket.js`'s production behavior — this experiment replays through it
  in isolation; it does not modify it.

## References

- `roadmap.md` — Horizon-1 placement and downstream dependency notes.
- `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` — §"Evaluation design" (full three-level model,
  dataset hygiene, start-small guidance), Reassessment §3 ("Agent evaluation... Insufficient →
  Ready to Pilot" — the evidence basis for running this now rather than deferring further).
- `guardrail_enforcement_epic.md` — source of the 2 known recurring defect classes this pilot
  scores against.
- `workflow_reliability_epic.md` — the sidecar-isolation prerequisite this experiment's Method
  depends on.
- `tickets/done/`, `stored_artifacts/`, `agent-monitoring/runs.jsonl` — the real corpus and
  baseline data this spec cites.

## Results

Executed by TCK-20260907-FILTERED-REPLAY-EVAL-PILOT (2026-09-07T08:37:37.538526+00:00). Full report: `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/results.md`.

1. **Repeatable scoring established** — MET
2. **Sample quality accepted for the 2 target defect classes** — MET
3. **Replay contamination risk is understood and demonstrably controlled** — MET

- **Scores are noisy/non-repeatable** — NOT FIRED
- **Worktree isolation cannot fully eliminate the shared-sidecar contamination risk** — NOT FIRED

## Decision

All 3 Exit Criteria met, no Kill Criterion fired — item 13's downstream Bucket-C dependency notes (items 18-20) are unblocked per roadmap.md's Eval-pilot exit gate.
