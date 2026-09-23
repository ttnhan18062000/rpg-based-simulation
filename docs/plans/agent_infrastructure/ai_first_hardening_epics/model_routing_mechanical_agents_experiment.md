---
status: active
layer: ai
authority: P1
audience: agent
date: 2026-09-23
tags: [ai, agent-monitoring, governance]
---

# Experiment Specification — Model-Based Routing for Mechanical Agents

**Tracking ticket**: none — Bucket-B items never convert directly to production implementation
tickets. Per the freeze verdict's handoff boundary, this is the correct deliverable shape:
`Frozen Architecture Proposal → Experiment Specification → Hypothesis / Baseline / Method /
Metrics / Exit Criteria / Kill Criteria → Run Experiment → Decision`. Scoped into a spec document
by `TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC`.
**Source**: `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` Rev.3, Bucket C item 18 — "Model-based
routing for mechanical agents (done-checker, ticket-scoper)". Was blocked on
`agent_evaluation_foundation_experiment.md` (item 13) producing a trusted baseline; that pilot
completed 2026-09-07 (`TCK-20260907-FILTERED-REPLAY-EVAL-PILOT`) with all 3 Exit Criteria MET, no
Kill Criterion fired — the prerequisite is cleared.
**Roadmap**: `roadmap.md` — Horizon 2, "C — Future option", listed as blocked pending item 13; now
unblocked, still not implemented (this doc is the Experiment Specification step, not the pilot
run).
**Priority**: P2 — a routing efficiency/cost question for two rule-following agents, not a
structural correlated-failure risk like the shadow-reviewer work (item 16/`review_independence_epic.md`).

## Why this is an experiment, not an epic

No agent behavior changes as a result of writing or even running this. The entire output is
evidence: does routing `done-checker`/`ticket-scoper` to a candidate model produce verdicts
consistent with the current model, at potentially lower cost/latency? If yes, a later cutover
ticket can follow. If no — or if the comparison can't reliably detect a regression — routing stays
unbuilt and the negative result is itself the useful outcome, same posture item 13 took.

## Hypothesis

A `model:` frontmatter override on exactly two mechanical agents — `.claude/agents/done-checker.md`
and `.claude/agents/ticket-scoper.md` — evaluated against item 13's own eval-pilot baseline scoring,
can be shown to preserve verdict quality (DoD-condition verdicts for `done-checker`; ticket-format/
conflict-flagging verdicts for `ticket-scoper`) within an explicit tolerance, on a sample large
enough that a real quality regression would be visible rather than masked by sample noise.

This is deliberately narrower than "does model routing work for agents in general" — per
`bucket_c_future_options.md`'s own scoping, the pilot targets exactly these two mechanical,
rule-following agents, not the open-ended judgment agents (`architecture-reviewer`,
`security-reviewer`) that `review_independence_epic.md`'s separate M1/M2 work already covers.

## Baseline (item 13's real, already-executed results — no new pilot baseline needed)

- **Source**: `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/results.md` and
  `agent_evaluation_foundation_experiment.md`'s own appended `## Results`/`## Decision` sections.
- **Sample**: 27 tickets sampled (hard-bounded 20-40) from the live `tickets/done/` corpus; 5
  converted to real replay fixtures (22 excluded with logged reasons, mostly hotfix-tier tickets
  with no Investigate/Plan/Review phase events — `done-checker`'s own verification phase is part of
  what's missing there, a relevant caveat for this pilot's own sample availability, see Method
  step 1).
- **Metric vocabulary already established**: Primary (repeatable flag/detection rate on 2 known
  recurring defect classes across 2 independent runs — both MET), Safety (replay isolation
  contamination check — MET), Efficiency (wall-clock/tool-call volume — informative only).
- **Replay infrastructure already built**: `tools/agent_replay/sampler.py`,
  `fixture_converter.py`, `defect_detectors.py`, `pilot_isolation.py`, `metrics.py`, `run_pilot.py`
  — this pilot reuses these modules rather than building a second sampling/replay harness.

## Method

1. **Sample, reusing item 13's infrastructure, not a new harness**: use
   `tools/agent_replay/sampler.py`'s existing stratified sampler to select a comparable slice of
   `tickets/done/` tickets that actually exercise `done-checker` (has a Verify-phase event with a
   real DoD-condition verdict) and `ticket-scoper` (has a Scope-phase event with a real ticket
   produced). Note from item 13's own execution: the largest exclusion reason was hotfix-tier
   tickets lacking phase events entirely — this pilot's eligible pool may be smaller than item 13's
   for that reason; report the real eligible count rather than assuming parity with item 13's 27.
2. **Apply the pilot mechanism named in the source doc**: a `model:` frontmatter override, added
   only to `done-checker.md` and `ticket-scoper.md` — the per-agent-file field that already governs
   each agent type's model today (confirmed: 0 of 16 agent files currently declare one). This is
   distinct from `implement-ticket.js`'s own `agent()` call-level `model:` parameter (used today
   only by the shadow-reviewer's advisory second call) — the frontmatter mechanism is a standing
   per-agent-type default, not a one-off call override, and is the mechanism this pilot must use to
   match what a real eventual cutover would look like.
3. **Replay in isolation, twice**: same isolation technique item 13's Method step 3 used
   (`tools/agent_replay/pilot_isolation.py`) — an isolated worktree, session-scoped sidecar only,
   never the shared `.claude/current_run` path. Run the sample once under the current model, once
   under the candidate, using the same fixtures for both so any verdict difference is attributable
   to the model change alone.
4. **Score against the baseline, not a new rubric**: compare candidate verdicts to baseline
   verdicts (current-model item 13 results, where the same tickets overlap; otherwise the
   candidate's own current-model replay run from step 3) using the item-13 metric vocabulary
   (gate-outcome match rate). This is the concrete regression-detection mechanism the named risk
   requires: a material verdict-match-rate drop on either agent is the fail signal, computed and
   reported before any cutover is considered — never assumed absent because the pilot "seemed
   fine."
5. **Periodically refresh**, same posture as item 13's own Method step 5 — this pilot's eligible
   pool grows as more tickets close with real `done-checker`/`ticket-scoper` phase events.

## Metrics — three tiers, matching item 13's shape

- **Primary**: verdict-match rate between candidate-model and current-model runs on the same
  sample, for `done-checker`'s DoD-condition verdicts and `ticket-scoper`'s conflict-flagging
  verdicts separately (not pooled — the two agents do structurally different jobs).
- **Safety**: same replay-isolation contamination check item 13 already built and validated
  (`pilot_isolation.py`) — no write to any live/shared session state during this pilot's own
  execution.
- **Efficiency**: wall-clock/cost difference between candidate and current model on the sample —
  informative for the eventual cutover decision, not a pass/fail bar for this pilot.

**Terminology discipline**, inherited from item 13's own freeze-pass correction: only claim what's
directly observed (verdict-match rate on the actual sampled tickets) or repeatable (score
consistency if the pilot is run more than once). Do not claim a general "regression rate" beyond
what the sample actually measured.

## Exit criteria (what "the pilot worked" means)

1. Verdict-match rate is measured and reported for both agents separately, with a real sample size
   stated (not assumed to match item 13's 27).
2. No material verdict-match-rate drop on either agent — "material" defined concretely at
   implementation time from the measured baseline variance, not left as a vague qualitative call.
3. Replay isolation held (same requirement, same evidence shape as item 13's own Exit Criterion 3).

Meeting all three produces a decision recommendation (route or don't route) — it does not itself
apply a `model:` override to either agent file in production; that is separate, later work gated on
this pilot's own result being positive.

## Kill criteria (when to stop investing)

- A material verdict-match-rate drop on either agent that cannot be explained as a legitimate
  model-quality difference — this is exactly the named risk ("model-routing pilot masking a real
  quality regression") firing, and must be reported as a negative finding, not quietly re-scoped
  into a smaller claim or silently retried with a different candidate model.
- The eligible sample pool (tickets with real `done-checker`/`ticket-scoper` phase events) turns
  out too small to produce a trustworthy comparison — same "small trusted sample beats a large
  untrusted one" principle item 13's own spec cited (§69), but if the pool is too small even for
  that bar, the pilot should pause and report rather than proceed on an under-powered sample.

If either kill criterion fires, the result is reported as a negative finding — not silently
abandoned.

## Out of scope

- Applying a `model:` override to `done-checker.md` or `ticket-scoper.md` in production — this spec
  describes the pilot; running it and any resulting cutover decision are separate, later work.
- Any routing dispatcher, config toggle, or new orchestrator plumbing — the pilot reuses the
  existing per-agent-file `model:` frontmatter mechanism as-is.
- Extending the pilot to any other agent — scoped to exactly the two named mechanical agents, per
  the source doc's own scoping.
- Choosing the specific candidate model — deferred to implementation time, informed by whatever
  model diversity is available then, same deferral pattern `review_independence_epic.md` used for
  its own candidate-model choice.
- Building a new sampling/replay harness — this pilot reuses `tools/agent_replay/` as-is.

## References

- `bucket_c_future_options.md` — item 18's original blocked entry and "When it clears" guidance,
  the direct source this spec is written from.
- `agent_evaluation_foundation_experiment.md` — the six-section shape template and the scoring
  baseline this spec A/Bs against.
- `roadmap.md` — item 18's Horizon-2 placement and dependency notes.
- `review_independence_epic.md` — the sibling shadow-mode-diversity work for the two judgment
  agents (`architecture-reviewer`/`security-reviewer`), explicitly a different mechanism (call-level
  `model:` override) and a different agent scope from this item.
- `tools/agent_replay/` — the sampling/replay/scoring infrastructure this pilot reuses.
- `.claude/agents/done-checker.md`, `.claude/agents/ticket-scoper.md` — the two pilot targets.
- `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/results.md` — the real baseline data
  this spec's Method and Metrics sections cite.
