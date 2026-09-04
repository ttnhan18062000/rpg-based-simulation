---
status: active
layer: ai
authority: P1
audience: agent
date: 2026-09-04
tags: [ai, security]
---

# Epic Plan — Review Independence

**Tracking ticket**: not yet created (planning stage — detail plan and milestones only).
**Source**: `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` Rev.3, standalone grouping "Review
Independence" — Bucket A / Horizon 1 member "Model-diverse reviewer — deploy shadow-mode
logging" plus Bucket B member "Model-diverse reviewer — shadow comparison & cutover decision".
**Roadmap**: `roadmap.md` — Horizon 1. Independently rollback-able (a 2-line frontmatter revert);
correctly not folded into a bigger epic — no shared component with Workflow Reliability or
Telemetry & Retention.
**Priority**: P1 — Known Structural Risk motivation, Level C evidence (structural: zero of 16
agent files declare a `model:` frontmatter override, confirmed by direct grep).

## Problem

`architecture-reviewer` and `security-reviewer` — the two agents whose entire job is catching what
`implementer` missed — run on the same model family as `implementer` itself. `grep "^model:"
.claude/agents/*.md` returns zero matches across all 16 agent definitions. This is exactly the
correlated-failure risk independent review exists to prevent: same model, same assumptions,
reviewing its own generation. `architecture-reviewer.md`'s own static-check backing (a deterministic
pre-flag script) partially mitigates this by not asking the LLM to re-derive the plan from
scratch — but model-family diversity is a separate, unaddressed dimension.

## Scope

### M1 — Deploy shadow-mode logging (gated on nothing; Bucket A, committed)

Wire a candidate model to run alongside the current reviewer on every diff for `architecture-
reviewer` and `security-reviewer`, logging both verdicts. **Neither blocks the workflow** — this
milestone ships the comparison *capability* only. The production verdict remains the current
model's; the candidate's verdict is recorded for comparison, not acted on.

Concretely: add a `model:` override on a shadow invocation path (implementation detail — either a
second agent-spawn using the same prompt with a different `model:` frontmatter, or an explicit
dual-call inside the Architecture-Verify/Security-Review phase — resolved during implementation,
not prescribed here) and log both verdicts to a comparable location (e.g. an `agent-monitoring/`
event field) so M2 below has real data to compare.

**Bounded and attributable, added during planning discussion**: shadow mode roughly doubles model
calls for these two phases, and given the platform's own token-forwarding gap (no real cost data
reaches `agent-monitoring/`), that cost would otherwise be structurally invisible — showing up
nowhere except as an unexplained phase-duration increase in retro reports. Two concrete
requirements, not just a caution:
- **Attributable**: log candidate-reviewer call count, review-phase wall time, workflow wall time,
  and `cost_proxy_score` — labeled by which reviewer (current vs. candidate) produced each figure,
  so the latency increase is traceable to this experiment rather than appearing as unexplained
  workflow slowdown elsewhere.
- **Bounded, not indefinite**: shadow evaluation runs only for a defined sample/window of
  review-eligible workflows, until M2 has enough comparison evidence to make the cutover decision
  — it does not run forever by default just because there's no dollar meter forcing a stop.

### M2 — Shadow comparison & cutover decision (Bucket B — experiment, not a committed ticket)

Once M1's shadow logging has run for several weeks on real live diffs, compare finding rates
between the two models: does the candidate catch anything the current model misses? Does it miss
anything the current model catches? Only then decide whether the candidate fully replaces the
current model for `architecture-reviewer`/`security-reviewer` — a decision this milestone produces,
not assumes.

This becomes an Experiment Specification (Hypothesis/Baseline/Method/Metrics/Exit/Kill Criteria)
before any cutover ticket is written — not sketched further here; see the freeze verdict's
Bucket-B handoff boundary. Baseline for the comparison: the current model's existing finding rate
on historical diffs, where recoverable from `agent-monitoring/` records.

## Out of scope

- Cutting over to the candidate model before M2's comparison data exists — M1 ships logging only,
  never a production model switch.
- Extending shadow-mode diversity to any other agent role beyond the two named reviewers — the
  frozen proposal scopes this specifically to the two adversarial gatekeeping roles where
  correlated failure matters most, not to every agent.
- Choosing a specific candidate model here — that's an implementation decision for M1, informed by
  whatever model diversity is actually available at implementation time, not fixed in this plan.

## Acceptance signal for this epic

- M1: shadow logging is live for both `architecture-reviewer` and `security-reviewer`; both
  models' verdicts are recorded per diff without either blocking the real workflow.
- M2: a comparison dataset exists covering several weeks of real diffs; a cutover decision is made
  and recorded, backed by that data rather than by intuition.

## References

- `roadmap.md` — Horizon-1 placement; confirms no shared component with sibling epics.
- `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` — §"Evaluation design" (online shadow mode,
  specifically recommended for this item in the freeze-pass revision), Automation boundary
  analysis (model-diverse review row — explicitly "not an autonomy increase," since it reduces
  risk rather than adding it).
- `.claude/agents/architecture-reviewer.md`, `.claude/agents/security-reviewer.md` — the two
  agent files this epic touches.
