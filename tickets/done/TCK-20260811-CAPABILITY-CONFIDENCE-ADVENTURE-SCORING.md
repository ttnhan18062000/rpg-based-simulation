---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING
phase: done
date: 2026-08-11
tags: [cognition, self-model]
---

# TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING

## Title
Wire capability-estimate-driven confidence into adventure route scoring

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Deepen adventure's internal reasoning by making route confidence reflect capability-estimate-driven data from CapabilityEstimateService instead of a flat generation-time confidence constant. Investigation found this is a blocked/larger-prerequisite idea, not a simple wire-up: CapabilityEstimateService is structurally empty in the live pipeline today, so this ticket must resolve that prerequisite as part of its own scope, disclosed explicitly rather than silently assumed.

## Scope
- Resolve the capability_context-never-populated prerequisite: either (a) populate a real CapabilityContext upstream of SelfModelUpdatePhase, or (b) have AdventureRouteScorer call CapabilityEstimateService.estimate() itself with a route-scoped ad-hoc context, bypassing the never-populated field -- decision made explicitly, not assumed
- For a route whose family maps to a capability key, confidence_bonus reflects a real CapabilityEstimate.estimate value, not always the generation-time confidence constant
- New capability read stays the entity's own subjective belief per scoring.py's documented information-opacity boundary

## Out of Scope
- Memory-informed candidates (TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING) and relationship-aware FORM_PARTY (TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY) -- separate tickets
- Any change to AdventureGoalScorer/AdventureDecisionService's wrapper migration -- orthogonal but touches the same files; recommend landing after that migration settles

## Acceptance Criteria
- [x] The capability_context-never-populated prerequisite gap is explicitly disclosed and resolved as part of this ticket's own scope (not silently assumed already wired)
- [x] For a route whose family maps to a capability key, confidence_bonus reflects a real CapabilityEstimate.estimate value, not always the generation-time confidence constant
- [x] Existing isolated CapabilityEstimateService unit tests continue to pass unchanged

## Related Tickets
None.

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/cognition/capability_estimate.py
- src/cognition/self_model_phase.py
- src/core/self_model.py
- src/domains/adventure/scoring.py

## Assumptions / Open Questions
- BLOCKED/larger-prerequisite finding: entity.self_model.capabilities.estimates is empty in production today regardless of this concern, because capability_context is never supplied to SelfModelUpdatePhase.run() at its only production call site (zero grep hits for capability_context= outside the 2 cognition files) -- this is not a simple wire-up; the prerequisite must be resolved and disclosed, not hidden
- Sequencing/merge conflict risk with the adventure/cognition wrapper migration tickets (which declare AdventureRouteScorer 'unchanged internally') -- recommend landing after those settle, or explicitly disclaim the risk if landed concurrently
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md (Future Extension Patterns)

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING/plan.md`'s
8 steps, verbatim on Step 1's reviewed code:

1. `AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py`) now imports
   `CapabilityContext`/`CapabilityEstimateService` and replaces the "── 5. Confidence Bonus ──"
   block: for `GATHER_RESOURCE` routes with a resolvable `target_node_id`/`resource_nodes` entry
   **and** a `has_item` requirement naming a tool, and for `CRAFT_UPGRADE` routes with a
   `recipe_known` requirement, `confidence_bonus` is now `CapabilityEstimateService.estimate(...)
   .estimate × 0.15` instead of the flat `route.confidence × 0.15`. All other routes, and mapped
   routes whose key/tool-requirement cannot be resolved, keep the flat term unchanged (this
   includes the round-1-review regression case: a resolvable `GATHER_RESOURCE` node with no tool
   requirement at all, which `test_depletion_scoring.py`'s fixtures exercise). No change to the
   final-score formula or the `dataclasses.replace(...)` write-back — both already referenced
   `confidence_bonus` by name.
2. Added `tests/unit/domains/adventure/test_capability_confidence_scoring.py` with the 7 tests
   from plan.md/test_plan.md (items 1-7), including test 4's 4 sub-cases (recipe-less
   CRAFT_UPGRADE, node_id=None, missing-node GATHER_RESOURCE, and the round-1 regression guard:
   resolvable GATHER_RESOURCE node with no requirements at all).
3. `docs/mechanics/04_strategic_cognition.md`: added `### 6.12 Capability-Driven Confidence Bonus`
   after §6.11, and updated §6.2's `confidence_bonus` row to reference it.
4. `docs/parity_ledger/strategic_cognition.yaml`: extended STRAT-227's `text`, `v2_evidence`, and
   `test_path` (appended, did not create a new entry); YAML re-validated as parseable post-edit.
5. `docs/cognition/capability_and_knowledge_contract.md`: corrected the stale "generates a blocker
   (scored at −2.0 penalty)" claim to accurately describe the ad-hoc `confidence_bonus` call.
6. `docs/cognition/README.md`: corrected the `src/domains/adventure/` row in the "Relationship to
   other subsystems" table — no longer claims `entity.self_model.capabilities` is read directly.
7. `docs/simulation/domains/adventure_contract.md`: added a "What It Reads" row for the ad-hoc
   capability call and updated the `confidence_bonus` formula-table row; did not resync the rest
   of the table's pre-existing staleness (out of scope per plan).
8. `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`: marked
   the "Capability-estimate-driven confidence" Future Extension Pattern bullet closed/scoped with
   this ticket ID, explicitly noting the upstream `SelfModelUpdatePhase` gap is bypassed, not
   fixed.

No deviations from plan.md — Step 1's code block was implemented exactly as specified (verified by
direct comparison after writing). One minor pre-existing inaccuracy inherited verbatim from plan.md
Step 5's spec text: the sentence "(see 'Not yet live' note above)" in
`capability_and_knowledge_contract.md` does not point at an actual prior "Not yet live" heading in
that specific file (that phrase/pattern exists in `04_strategic_cognition.md` §6.11, not this file)
— implemented verbatim per the explicit instruction not to reinterpret Step-level exact text; flagged
here rather than silently fixed, since it is a doc cross-reference wording issue, not a functional
or architectural one.

## Test Summary

- New file `tests/unit/domains/adventure/test_capability_confidence_scoring.py`: 7/7 passed.
- Full regression suite named in plan.md's Step 1 Verify note
  (`test_capability_confidence_scoring.py` + `test_phase3_route_scoring.py` +
  `test_depletion_scoring.py` + `test_memory_informed_scoring.py` + `test_scoring_plan_bonus.py` +
  `test_hero_quest_scoring.py`): 47/47 passed. `test_depletion_scoring.py`'s 6 tests specifically
  confirmed passing — this was the exact regression round-1 review caught and the plan's
  `required_tool is not None` gate fix resolves.
- Full `tests/unit/domains/adventure/` + `tests/unit/cognition/test_phase2_capability_estimate_service.py`
  + `tests/unit/cognition/test_phase2_self_model_phase.py`: 107/107 passed — confirms AC3
  (`capability_estimate.py` untouched, its unit tests pass unchanged) and that
  `test_phase2_self_model_phase.py` still shows `capability_context` defaulting to `None` at
  production `apply()` level (no upstream wiring silently added).
- `git diff --stat src/cognition/capability_estimate.py` returns empty — confirms zero edits to
  that file, satisfying AC3's explicit "unchanged" requirement.

## Files Changed

- `src/domains/adventure/scoring.py` — capability-driven `confidence_bonus` (Step 1)
- `tests/unit/domains/adventure/test_capability_confidence_scoring.py` — new file (Step 2)
- `docs/mechanics/04_strategic_cognition.md` — new §6.12, updated §6.2 row (Step 3)
- `docs/parity_ledger/strategic_cognition.yaml` — extended STRAT-227 (Step 4)
- `docs/cognition/capability_and_knowledge_contract.md` — staleness correction (Step 5)
- `docs/cognition/README.md` — staleness correction (Step 6)
- `docs/simulation/domains/adventure_contract.md` — new read row + formula row (Step 7)
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` — closed
  Future Extension Pattern bullet (Step 8)
- `docs/mechanics/adventure_routing_contract.md` — Architecture-Verify round-1 finding, fixed
  directly: `confidence_bonus` formula-table row + worked-example clarification, corrected to
  disclose the capability-driven exception for `GATHER_RESOURCE`/`CRAFT_UPGRADE`
- `docs/observability/decision_trace_contract.md` — same pass: `confidence_bonus` field comment in
  the decision-trace JSON schema corrected to describe both the flat and capability-driven sources

## Completion Summary

Implemented ad-hoc, scorer-local capability-driven `confidence_bonus` in
`AdventureRouteScorer.score()`: `GATHER_RESOURCE` (via `resource_nodes[target_node_id].kind`, gated
on a real tool requirement) and `CRAFT_UPGRADE` (via `route.requirements`'s `recipe_known` entry)
routes now source `confidence_bonus` from a direct `CapabilityEstimateService.estimate()` call
instead of the flat `route.confidence × 0.15` constant; all other routes, and mapped routes whose
key cannot be resolved, keep the flat term. This resolves the ticket's AC1 prerequisite by bypassing
(not fixing) the upstream gap — `SelfModelUpdatePhase.apply()` still never passes a
`capability_context`, so `entity.self_model.capabilities.estimates` remains empty in production; this
is disclosed explicitly in all 7 updated docs. `src/cognition/capability_estimate.py` was not
modified, satisfying AC3. 7 new unit tests were added and the full named regression suite (107 tests
across adventure scoring, capability estimation, and self-model phase) passes, with
`test_depletion_scoring.py`'s round-1-review-caught regression case specifically confirmed safe.

Plan review went through 2 rounds: round 1 found a real defect that would have shipped as a
regression -- the `GATHER_RESOURCE` branch's fallback gate only checked whether the target node
resolved, not whether a real tool requirement existed on the route, and since
`CapabilityEstimateService.estimate()`'s `has_tool` defaults to `True` when no tool data is
supplied, this would have silently switched off the flat `confidence_bonus` term for every
resolvable `GATHER_RESOURCE` route -- breaking `test_depletion_scoring.py`'s regression tests. Fixed
by wrapping the entire capability-lookup block inside `if required_tool is not None:`. Round 2
independently re-traced the fix and APPROVED. Architecture-Verify ran 2 rounds: round 1 found a
mislabeled cross-reference (pointed at a "Not yet live" callout that doesn't exist for this term)
and 2 stale P1/authoritative docs (`adventure_routing_contract.md`, `decision_trace_contract.md`)
still unconditionally describing `confidence_bonus` as the flat formula -- fixed via targeted,
minimally-scoped edits (a pointer/caveat, not a full resync of either doc's other pre-existing
staleness). Round 2 APPROVED with no further gaps. Parity phase independently re-confirmed
STRAT-227 and the `social_narrative.yaml`/`progression.yaml`/`infrastructure.yaml` false-positive
determinations, finding no further gaps.
