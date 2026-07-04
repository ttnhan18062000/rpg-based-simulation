---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL
phase: open
date: 2026-07-04T12:17:33Z
tags: [simulation_quality, feature-flags, testing, guardrail, audit-fix-plan]
---

# TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL

## Title
Add per-scenario feature-flag guardrail test covering the expanded corpus's flag surface

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Folds in `docs/plans/audit_fix_plan.md` P2-E ("Feature-gated phases have no per-scenario default
test"). Per that finding, 8 pipeline phases are gated behind `FeatureMode` flags
(`src/domains/optimization/feature_flags.py`) and no test verifies the correct default flag values
per scenario/world type — a misconfigured scenario silently loses features. This risk is
substantially amplified by this epic's own preceding 9 tickets: before this batch, only
`urban_political` had a non-empty `feature_flags:` profile block (`ENABLE_BELIEF_ASSIMILATION`,
`ENABLE_SOCIAL_COOPERATION`) and only `simq_routing_test` had `ENABLE_ADVENTURE_ROUTING` (via a
hardcoded harness special case, generalized by ticket 3 in this batch). After tickets 3-9 land, the
corpus will have many more worlds with many more per-world flag combinations
(`ENABLE_ADVENTURE_ROUTING`, `ENABLE_BELIEF_ASSIMILATION`, `ENABLE_SELF_MODEL_COGNITION` across
unit/end-to-end/stress-tier worlds) — exactly the kind of expanded, easy-to-misconfigure surface
P2-E's finding warns about. This ticket lands last in the batch specifically so its test matrix
covers that expanded surface, not just the pre-epic baseline.

## Scope
1. Add a test (in `tests/integration/` or `tests/certification/`, per P2-E's own fix guidance) that:
   - Loads every world's `config/simulation_quality/profiles/<world>.yaml` (or
     `default.yaml` fallback where a world has no dedicated profile)
   - Asserts the expected `feature_flags:` state for that world, per this epic's own record of what
     should be ON/OFF for each world:
     - The 9 pre-existing non-routing worlds (`urban_political`, `dungeon_crawl`, `sandbox_world`,
       `wilderness_survival`, `highland_traverse`, `swamp_border_world`, `frontier_living_world`,
       `frontier_extended`, `generated_frontier_3_42`) — `ENABLE_ADVENTURE_ROUTING` must be
       OFF/absent (per `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s anti-drift note: "if any calibration
       world enables `ENABLE_ADVENTURE_ROUTING`, AGENCY will activate and grade anchors must be
       updated" — this test is exactly that anti-drift guard, made concrete)
     - `simq_routing_test` and the new AGENCY unit-tier world (ticket 6) —
       `ENABLE_ADVENTURE_ROUTING` must be ON
     - `urban_political` and any world from ticket 7 (E2E content expansion) that seeded
       `information_source_profiles` — `ENABLE_BELIEF_ASSIMILATION` must be ON
     - The new self-model pilot world (ticket 5) — `ENABLE_SELF_MODEL_COGNITION` must be ON, and
       `ENABLE_BELIEF_ASSIMILATION` must be OFF (per that ticket's explicit isolation requirement)
     - New unit-tier FACTION/INFORMATION worlds (ticket 4) — flag state matching each world's single
       isolated mechanic
     - New stress-tier worlds (ticket 8) — flag state matching whatever content ticket 8 actually
       seeded (e.g. its large-scale FACTION/INFORMATION world should have
       `ENABLE_BELIEF_ASSIMILATION` ON if it seeded `information_source_profiles`)
2. Assert the inverse direction too: a world with a Pattern-6 content field seeded
   (`faction_tension_overrides`, `information_source_profiles`, etc.) but the corresponding flag OFF
   (or vice versa) is flagged as a real misconfiguration — this is the "seeding profiles without
   turning the flag on produces zero signal" trap investigation.md §3 documents; catch it at test
   time, not by discovering silent zero-signal grades after the fact.
3. Confirm the test matrix explicitly covers every world that exists after tickets 1-9 land — do
   not write it against only the pre-epic 10-world baseline.
4. Run the new test and confirm it passes against the actual post-epic corpus state.

## Out of Scope
- Fixing any misconfiguration this test discovers in an already-completed prior ticket in this
  batch — if this test finds a real drift/misconfiguration, that is a legitimate finding; either fix
  it directly if trivial (e.g. a missing flag line) or file a targeted follow-up ticket, but do not
  silently loosen the test to make it pass
- Changing `FeatureMode`, `feature_flags.py`, or any flag-gated phase's runtime behavior — this
  ticket only adds a static/config-level assertion test, not new engine logic
- Re-scoping or re-authoring any of tickets 1-9's world content — this ticket is a guardrail on top
  of what they produce, not a redo of their content decisions

## Acceptance Criteria
- [ ] New test exists (`tests/integration/` or `tests/certification/`) loading every world's
      profile YAML (or `default.yaml` fallback) and asserting expected `feature_flags:` state
- [ ] Test explicitly enumerates and covers all worlds added by tickets 4, 5, 6, 8 in this batch,
      not just the pre-epic 10-world baseline
- [ ] Test asserts both directions of the flag/content-field pairing (flag ON with no matching
      content, and content seeded with flag OFF, are both caught as misconfigurations)
- [ ] Test asserts the 9 pre-existing non-routing worlds keep `ENABLE_ADVENTURE_ROUTING` OFF (the
      AGENCY-DA anti-drift guard, made concrete and automatically enforced)
- [ ] Test passes against the actual corpus state after tickets 1-9 have landed
- [ ] `docs/plans/audit_fix_plan.md` P2-E section updated from "OPEN" to resolved, with the new
      test's path cited, and the Summary Table's P2-E row updated to match

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE — this ticket's test matrix must cover the
  generalized mechanism ticket 3 introduces
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO — worlds this test matrix must cover
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT — worlds this test matrix must cover
  (including the ENABLE_BELIEF_ASSIMILATION-must-be-OFF isolation requirement)
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY — worlds this test matrix must cover
- TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION — worlds this test matrix must cover
- TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS — worlds this test matrix must cover
- TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA — source of the anti-drift note this test operationalizes

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 (mechanic
  inventory) and §4 open question 5 (P2-E fold-in rationale)
- `docs/plans/audit_fix_plan.md` — P2-E section (source finding, fix guidance) and Summary Table
- `docs/simulation_quality/eval_matrix_results.md` — AGENCY Cross-World Design Note (anti-drift
  language this test enforces)

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation

## Related Code Areas
- `src/domains/optimization/feature_flags.py` — 8 gated phases/flags
- `config/simulation_quality/profiles/` — every world's profile YAML, including all new ones tickets
  4-8 add
- `data/content/simulation_scenarios/` (per P2-E's original file reference)
- `tests/integration/` or `tests/certification/` — new test location (implementer's choice, justify
  in Implementation Notes)

## Assumptions / Open Questions
- UQ-1: Should this test be a single parametrized test iterating all worlds, or one test function
  per world? Default to a single parametrized test (per-world flag-expectation table as test data)
  for maintainability — adding a future world means adding one table row, not one new function.
- UQ-2: Where should the "expected flag state per world" table live — hardcoded in the test file, or
  in a small fixture/config file? Default to hardcoding in the test file unless the number of worlds
  makes that unwieldy (>15 worlds), in which case a fixture file is preferable; implementer's
  judgment.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
