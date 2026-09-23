---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC
phase: done
date: 2026-09-23
tags: [ai, agent-monitoring, governance]
---

# TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC

## Title
Model-based routing for mechanical agents — Experiment Specification (Bucket-C item 18)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md`'s "Model-
based routing for mechanical agents (done-checker, ticket-scoper)" entry was blocked on
`agent_evaluation_foundation_experiment.md` (item 13) producing a trusted baseline — that pilot
completed with all 3 Exit Criteria MET (`TCK-20260907-FILTERED-REPLAY-EVAL-PILOT`, done
2026-09-07), so item 18 is now unblocked per the doc's own "When it clears" note: "revisit as a
Bucket-B experiment (not straight to a ticket) — pilot `model:` overrides on `done-checker.md`/
`ticket-scoper.md` only, A/B against the eval baseline's scoring." This ticket writes that
Experiment Specification document — the deliverable is a spec, not routing code or an
`.claude/agents/*.md` edit.

## Scope
- Write a new Experiment Specification at
  `docs/plans/agent_infrastructure/ai_first_hardening_epics/model_routing_mechanical_agents_experiment.md`,
  following the same six-section shape `agent_evaluation_foundation_experiment.md` (item 13) used:
  header (Tracking ticket / Source / Roadmap / Priority), Hypothesis, Baseline, Method, Metrics,
  Exit Criteria, Kill Criteria, Out of Scope, References.
- Scope the experiment to a `model:` frontmatter override pilot on exactly two agents —
  `done-checker.md` and `ticket-scoper.md` — A/B'd against item 13's own eval-pilot scoring
  baseline (`stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/results.md` and the frozen
  spec doc's appended `## Results`).
- Carry the hard sequencing rule from `bucket_c_future_options.md` into the spec explicitly: a
  routing pilot must be detectable against that baseline, because the named risk is "a
  model-routing pilot masking a real quality regression" — the Method and Metrics sections must
  make that detection concrete (what would a masked regression look like, and how the pilot's own
  design catches it), not just restate the warning.
- Update `bucket_c_future_options.md`'s item-18 entry to link the new spec doc once it exists
  (mirroring how item 13's own entry was updated once its pilot ticket landed).

## Out of Scope
- Any `.claude/agents/*.md` edit — no `model:` override is actually applied to `done-checker.md` or
  `ticket-scoper.md` by this ticket. Running the pilot is separate, later work once this spec is
  reviewed.
- Any routing code, dispatcher logic, or config mechanism for selecting a model per agent — the
  spec describes the pilot design, it does not build the pilot.
- Scoping item 19 (task-success-rate metric) or item 20 (full eval platform) — item 19 is the
  sibling ticket `TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC` in this same batch; item
  20 stays untouched per the source proposal's own sequencing warning.
- Choosing a specific candidate model for the routing pilot — informed by whatever model diversity
  exists at implementation time, not fixed in this spec (same deferral pattern
  `review_independence_epic.md` used for its own candidate-model choice).

## Acceptance Criteria
- [x] `docs/plans/agent_infrastructure/ai_first_hardening_epics/model_routing_mechanical_agents_experiment.md`
      exists with all six sections (Hypothesis/Baseline/Method/Metrics/Exit/Kill), plus Out of
      Scope and References, matching item 13's spec shape.
- [x] The spec scopes the pilot to exactly `done-checker.md` and `ticket-scoper.md`, A/B'd against
      item 13's own eval-pilot scoring baseline — no other agents named as pilot targets.
- [x] The spec makes the "detectable against baseline" sequencing rule concrete: Method and/or
      Metrics describe how a masked quality regression from routing would actually be caught, not
      just restate the source warning.
- [x] `bucket_c_future_options.md`'s item-18 entry links to the new spec doc.
- [x] `## Related Tickets` links back to `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC`.

## Related Tickets
- `TCK-20260904-AI-FIRST-HARDENING-FOLLOWON-EPIC` (`tickets/todos/`, `EPIC_SCOPED`) — the Bucket
  B/C tracking epic this item (roadmap item 18) is enumerated under.
- `TCK-20260907-FILTERED-REPLAY-EVAL-PILOT` (done) — the eval pilot (item 13) this spec's baseline
  and detectability requirement both depend on.
- `TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON`,
  `TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC` (this batch, `tickets/todos/`) — sibling
  tickets, independent of this one.

## Related Docs
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md` — item 18's
  existing blocked entry, the source this spec is written from.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/agent_evaluation_foundation_experiment.md`
  — the six-section shape template and the scoring baseline this spec A/Bs against.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` — item 18's roadmap
  placement.
- `.claude/agents/done-checker.md`, `.claude/agents/ticket-scoper.md` — the two agents this pilot
  would scope to (read for context, not edited).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260907-FILTERED-REPLAY-EVAL-PILOT/` — the baseline results this spec
  A/Bs against.

## Related Code Areas
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/` — new spec doc lands here.
- `.claude/agents/done-checker.md`, `.claude/agents/ticket-scoper.md` — read-only context, not
  modified.

## Assumptions / Open Questions
- None — item 13's exit criteria are already MET per its own recorded Results/Decision section,
  and the sequencing rule this spec must honor is stated explicitly in
  `bucket_c_future_options.md`.

## Implementation Notes
Read `.claude/agents/done-checker.md`/`ticket-scoper.md` directly and confirmed neither declares a
`model:` frontmatter field today (spot-check consistent with `review_independence_epic.md`'s own
already-recorded 0-of-16 finding). Also confirmed, by reading `implement-ticket.js`'s shadow-
reviewer call site, that a separate call-level `model:` parameter already exists on the `agent()`
helper — the spec explicitly distinguishes this from the per-agent-file frontmatter mechanism named
in `bucket_c_future_options.md`'s own text, so the eventual pilot implementation isn't ambiguous
about which mechanism to use.

Wrote the six-section Experiment Specification reusing item 13's exact shape (header block, "Why
this is an experiment, not an epic", Hypothesis/Baseline/Method/Metrics/Exit/Kill/Out of
Scope/References). The Method section makes the source doc's "masking a real quality regression"
warning concrete: a candidate-vs-baseline verdict-match-rate comparison, computed and reported
before any cutover consideration, reusing item 13's own `tools/agent_replay/` infrastructure and
metric vocabulary rather than inventing a second scoring approach.

Linked the new spec doc from `bucket_c_future_options.md`'s item-18 entry with a dated "Cleared"
note, mirroring how item 13's own downstream unblock was recorded elsewhere in this doc set.

## Test Summary
No automated tests apply — this ticket's diff is documentation-only (one new spec doc, one small
edit to an existing doc). Verified per `test_plan.md`'s manual checklist: all six required sections
present, both target agent names present, the frontmatter-vs-call-level mechanism distinction
stated explicitly, `bucket_c_future_options.md` links to the new doc — confirmed by direct
read-through and grep after writing.

## Files Changed
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/model_routing_mechanical_agents_experiment.md`
  — new, the Experiment Specification.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md` — item-18
  entry updated with a link to the new spec doc.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` — item 18's row updated
  from "H2, blocked" to unblocked, linking the new spec doc (mirrors the precedent item 13's own
  ticket set updating its roadmap row on completion).
- `staging_artifacts/TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC/` — new:
  `investigation.md`, `plan.md`, `test_plan.md`.
- `tickets/todos/TCK-20260923-MODEL-ROUTING-MECHANICAL-AGENTS-EXPERIMENT-SPEC.md` — deleted
  (superseded by this file).

## Completion Summary
Wrote the Bucket-C item 18 Experiment Specification per `bucket_c_future_options.md`'s own "When it
clears" guidance, now that item 13's eval pilot exit criteria are MET. The spec scopes a `model:`
frontmatter override pilot to exactly `done-checker.md` and `ticket-scoper.md`, reuses item 13's
existing replay infrastructure and metric vocabulary rather than building new tooling, and makes the
source proposal's named risk (a routing pilot masking a real quality regression) concrete via an
explicit baseline-comparison mechanism rather than restating it as a caution. No code or agent-file
changes were made — running the pilot and any cutover decision remain separate, later work.
