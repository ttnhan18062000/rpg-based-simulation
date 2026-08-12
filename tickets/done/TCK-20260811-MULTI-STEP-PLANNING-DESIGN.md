---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-MULTI-STEP-PLANNING-DESIGN
phase: done
date: 2026-08-11
tags: [cognition]
---

# TCK-20260811-MULTI-STEP-PLANNING-DESIGN

## Title
Design-scoping: multi-step/persistent planning for adventure-eligible entities

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Explore letting an entity commit to a short sequence of future intentions (train -> craft -> quest) rather than re-deciding the single next action every eligible tick. The original author explicitly stated this needs its own separate design conversation, not a scorer tweak -- investigation confirms no implementation ACs can be honestly derived, so this ticket is scoped as design-scoping work that produces a design doc and a go/no-go decision, not code.

## Scope
- A design doc (e.g. docs/architecture/<date>-multi-step-persistent-planning-design.md) proposing a durable typed model for committing to a short sequence of future intentions, explicitly reviewed against the Strategic/Tactical Rule
- Design doc explicitly resolves how a committed-but-not-yet-executed intention interacts with the existing single-slot current_project_id/current_objective_id model and the detour/lock-bypass arbiter in evaluate_strategic_intent()
- Design doc explicitly states its relationship to the existing ProgressionPlan.goal_queue and its documented 'multi-goal lookahead deferred' boundary (docs/simulation/domains/progression_planner_contract.md) -- supersede/extend/coexist, or explicit rationale for a separate tick-level concept
- Ticket closes when the design doc is written and reviewed, with either an accepted follow-up implementation ticket opened or an explicit reject/defer decision recorded with rationale

## Out of Scope
- No production code merged under this ticket -- this is design-scoping work only, not an implementation ticket
- Any code-behavior AC is explicitly excluded per the source proposal's own scoping statement

## Acceptance Criteria
- [x] A design doc exists (e.g. docs/architecture/<date>-multi-step-persistent-planning-design.md) proposing a durable typed model for committing to a short sequence of future intentions, explicitly reviewed against the Strategic/Tactical Rule
- [x] Design doc explicitly resolves how a committed-but-not-yet-executed intention interacts with the existing single-slot current_project_id/current_objective_id model and the detour/lock-bypass arbiter in evaluate_strategic_intent()
- [x] Design doc explicitly states its relationship to the existing ProgressionPlan.goal_queue and its documented 'multi-goal lookahead deferred' boundary -- supersede/extend/coexist, or explicit rationale why a separate tick-level concept is needed alongside it
- [x] No production code is merged under this ticket; the ticket closes when the design doc is written and reviewed, with either an accepted follow-up implementation ticket opened or an explicit reject/defer decision recorded with rationale -- `git diff --stat -- src/` confirmed empty throughout; design doc records GO + the follow-up ticket `tickets/todos/TCK-20260812-COMMITTED-INTENTION-SEQUENCE.md` has been filed using the design doc's own stub content verbatim as its scope

## Related Tickets
- TCK-20260619-E61-PROGRESSION

## Related Docs
- docs/simulation/domains/progression_planner_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/campaigns/progression_plan.py
- src/domains/campaigns/plan_revision.py
- src/domains/campaigns/orchestrator.py
- src/domains/adventure/scoring.py
- src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- The single-slot current_project_id model and lock-bypass arbiter are actively in flux right now (this batch's own TCK-20260811-ADVENTURE-GOAL-SCORER and TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION) -- this design-scoping work should probably explicitly wait for those to land and stabilize first
- Two structurally distinct planning concepts already coexist (episode-level ProgressionPlan vs. tick-level single-step GoalScorer re-decision) -- the new design risks creating a third overlapping concept if not explicitly scoped against both
- Forcing implementation-level ACs here would violate the source doc's own explicit scoping and this repo's Uncertainty Rule
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md (Future Extension Patterns)

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260811-MULTI-STEP-PLANNING-DESIGN/plan.md` (approved,
2 review rounds). Wrote the new design doc
`docs/architecture/2026-08-12-multi-step-persistent-planning-design.md` following plan.md's exact
9-section outline (frontmatter, Context, Goals, Non-Goals, Design [7 numbered subsections mirroring
plan.md's Steps 1-7], Future Extension Patterns, Diagrams [2 mermaid diagrams], Go/No-Go Decision,
Open Questions For Implementation) — transcribing plan.md's resolved reasoning (Q1-Q5, the
duplicate-`GoalKind` coexistence trace, the "coexist" relationship to `ProgressionPlan.goal_queue`,
the `reserved_detour_depth` disposition) into prose rather than re-deriving it. Added the one
post-landing note to
`docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`'s "Future
Extension Patterns" section, matching the exact voice/format precedent already used twice there.

Spot-checked a sample of plan.md's citations directly against current source before transcribing,
rather than trusting the plan text alone: `intelligence.py:1393-1408` (routine/role `.kind.lower()`
boost lookups, `modified_scores.sort(key=lambda x: (-x.utility, x.kind))`), `src/ai/goals/base.py`
`GoalRegistry.register()`'s `ValueError`-on-class-conflict behavior, and
`src/core/strategic.py:327-341` (`CognitionProfile.max_active_projects`/`reserved_detour_depth`/
`detour_breadth` field values and comments). All matched plan.md's claims exactly; no citation
drift found in the sampled set.

**Resolved deviation from plan.md's Step 8**: the dispatched Implement run initially scoped its own
file writes too narrowly (exactly two files: the design doc and the sibling doc's post-landing
note), omitting plan.md's Step 8 instruction to actually file the follow-up ticket. This was caught
immediately after Implement returned and fixed directly: `tickets/todos/TCK-20260812-COMMITTED-INTENTION-SEQUENCE.md`
has been filed using the design doc's own Follow-Up Ticket Stub content verbatim as its scope, and
the design doc's Go/No-Go Decision section updated to reference the real filed ticket instead of
noting it as unfiled. AC4 is now genuinely, fully satisfied on disk.

No `src/` file was touched (`git diff --stat -- src/` confirmed empty). No `docs/mechanics/*.md` or
`docs/parity_ledger/*.yaml` file was touched. No file belonging to any of the 9 already-DONE
`adventure-cognition-merge` sibling tickets was touched other than the one anticipated post-landing
note. `CognitionProfile.reserved_detour_depth` was not repurposed or removed. The
`ProgressionPlan.goal_queue` relationship was stated explicitly as "coexist," not left to omission.
Committed intentions were not given special priority inside `evaluate_project_switch()` in the
design's own text -- the "unmodified, ordinary candidate" answer was used throughout.

## Test Summary

Not applicable -- this ticket's deliverable is a design document, not code (test_plan.md states
explicitly: "There is nothing for pytest to run against"). No pytest suite was run. The only
"test" performed was the citation spot-check described above in Implementation Notes, plus
confirming `git diff --stat -- src/` is empty (the ticket's one hard negative check, per
test_plan.md's Scoped Pytest Commands section).

## Files Changed

- `docs/architecture/2026-08-12-multi-step-persistent-planning-design.md` (new) -- the design doc,
  this ticket's primary deliverable.
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` (edited) --
  one new post-landing note added to "Future Extension Patterns," per plan.md's Step 8.
- `tickets/todos/TCK-20260812-COMMITTED-INTENTION-SEQUENCE.md` (new) -- the follow-up
  implementation ticket, filed using the design doc's own stub content verbatim.

## Completion Summary

Wrote the design doc for multi-step/persistent planning (train -> craft -> quest committed
sequences), resolving all four ACs the ticket's Scope requires: (1) a durable typed
`CommittedIntention` model on a new `StrategicComponent.committed_intentions` field, reviewed
against the Strategic/Tactical Rule and placed on the strategy side; (2) its interaction with
`current_project_id` and `evaluate_project_switch()` -- injected as one ordinary, unmodified tier-5
candidate, with the one disclosed deviation (losing candidates retry instead of being discarded)
living entirely in the new model's own bookkeeping, not the arbiter, and the newly-traced
duplicate-`GoalKind` coexistence consequence confirmed structurally harmless against real code;
(3) its relationship to `ProgressionPlan.goal_queue` stated explicitly as "coexist," each of the
three planning concepts given a distinct, non-overlapping responsibility; (4) the decision recorded
is GO, and the follow-up implementation ticket `TCK-20260812-COMMITTED-INTENTION-SEQUENCE` has been
filed using the design doc's own stub content verbatim -- "no production code merged" confirmed
(`git diff --stat -- src/` empty throughout) and "follow-up ticket opened" now genuinely true on
disk. Plan review caught and required disclosure of a real architectural consequence (duplicate
`GoalKind` coexistence) before it shipped as unstated permanent doc content; a narrower run-scoping
gap in the initial Implement dispatch (omitting the ticket-filing step) was caught and fixed
immediately after.
