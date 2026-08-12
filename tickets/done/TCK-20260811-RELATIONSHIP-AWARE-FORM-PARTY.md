---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY
phase: done
date: 2026-08-11
tags: [cognition, adventure, social]
---

# TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY

## Title
Wire relationship-aware trust/bonds into FORM_PARTY scoring

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Deepen adventure's internal reasoning by making FORM_PARTY route generation relationship-aware via src/systems/social_systems/ trust/relationship data instead of a flat sociability scalar. Investigation found this is the lowest-risk, most-buildable of the design's 3 signal-enrichment ideas: FORM_PARTY generation already partially uses relationship data (the nemesis block) but PartyCompositionScorer.score() never reads trust_history/bonds for the specific candidates being considered.

## Scope
- PartyCompositionScorer.score() (src/systems/social_systems/party_composition.py:105) reads the specific candidate's real trust_history/bonds (SocialComponent) in addition to role-diversity/OCEAN-compatibility
- AdventureRouteScorer's confidence_bonus / personality_bias terms (scoring.py lines 207-208, 224) for FORM_PARTY incorporate the candidate's trust_history/bonds value alongside the existing sociability scalar
- Two otherwise-identical FORM_PARTY candidate pools differing only in one candidate's trust_history value produce different comp_score/confidence for that candidate
- New regression test alongside existing test_sociability_weight_is_0_40_on_form_party_route

## Out of Scope
- Memory-informed candidates (TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING) and capability-estimate confidence (TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING) -- separate tickets
- Any change to AdventureGoalScorer/AdventureDecisionService's wrapper migration -- orthogonal but touches the same files; recommend landing after that migration settles

## Acceptance Criteria
- [x] FORM_PARTY confidence/benefit for a specific candidate incorporates that candidate's real per-entity trust_history/bonds value -- genuinely satisfied at the read/computation layer (each candidate's own trust entry is read and folded in); the value exposed on the materialized route is a pool-level mean across candidates, not a literal single-candidate output field, since `AdventureRouteOption` has no per-candidate identity field (same class of gap as `HUNT_WEAK_ENEMY`/`SCOUT_LOCATION`, disclosed in the design doc)
- [x] Two otherwise-identical FORM_PARTY candidate pools differing only in one candidate's trust_history value produce different comp_score/confidence for that candidate -- fully, literally satisfied at the comp_score/confidence aggregate-output granularity the AC's own wording describes
- [x] Regression test added -- **reinterpreted, not literally alongside** `test_sociability_weight_is_0_40_on_form_party_route` (which lives in `tests/unit/domains/adventure/test_phase3_route_scoring.py`, a `scoring.py`-facing file this ticket makes zero edits to). New tests instead land in `tests/unit/social/test_party_composition.py`, the file that actually changed. `test_sociability_weight_is_0_40_on_form_party_route` itself continues to pass completely unmodified -- the strongest possible proof this ticket does not touch that formula. Deviation approved at Review round 1.
- [x] FORM_PARTY sociability weight of 0.40 remains bit-identical; new trust/bonds term is additive, not a replacement -- unconditionally true: `src/domains/adventure/scoring.py` has zero diff lines in this ticket's entire implementation

## Related Tickets
- TCK-20260628-E41F-PARTY-SCORER
- TCK-20260628-E43G-NEMESIS-RELATION

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/adventure/generator.py
- src/domains/adventure/scoring.py
- src/systems/social_systems/relationships.py
- src/systems/social_systems/party_composition.py
- src/core/models/social.py

## Assumptions / Open Questions
- Sequencing/merge conflict risk with the adventure/cognition wrapper migration tickets (which declare AdventureRouteScorer/Generator 'unchanged internally') -- recommend landing after those settle, or explicitly disclaim the risk if landed concurrently
- New trust/bonds read must stay the entity's own subjective belief, per scoring.py's documented information-opacity boundary, not omniscient world truth
- Related design doc: docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md (Future Extension Patterns)

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY/plan.md`'s 8 steps,
approved on Review round 1 (unusually clean for this epic -- no correction round needed).

Central architectural decision (Option A, chosen and verified during Plan/Review): trust/bonds
awareness lives entirely inside `PartyCompositionScorer.score()`
(`src/systems/social_systems/party_composition.py`) and `AdventureRouteGenerator.generate()`'s
FORM_PARTY branch (`src/domains/adventure/generator.py`) -- `src/domains/adventure/scoring.py` is
**not touched at all**. `AdventureRouteScorer.score()` never receives the candidate pool and
`AdventureRouteOption` has no per-candidate-id field, so `scoring.py`'s layer structurally cannot
know which individual candidate contributed what; only `PartyCompositionScorer.score()` (which runs
before candidates collapse into one aggregate `comp_score`) has genuine per-candidate visibility.

- `PartyCompositionScorer.score()` gained a new optional keyword-only `actor` parameter and a new
  `TRUST_BONUS_WEIGHT = 0.15` constant; when `actor` is supplied, an additional mean directed
  trust/bond term (bond sentiment takes priority over `trust_history` when both exist for a
  candidate, mirroring the real precedent in `src/systems/social_systems/appraisal.py:39-41` and
  `docs/simulation/social_systems_contract.md:70`) is folded in and the result clamped to
  `[0.0, 1.0]`. Pre-existing `role_diversity`/`ocean_compatibility` computation and the
  `actor is None` path are byte-identical to before.
- `AdventureRouteGenerator.generate()`'s FORM_PARTY branch now passes `actor=entity` into
  `PartyCompositionScorer.score(candidates[:8], actor=entity)` for `expected_benefit`, and folds the
  same trust term into generation-time `confidence` separately. Extended the existing `reason=`
  telemetry string with the new trust term value, matching the existing `comp_score={comp_score:.2f}`
  pattern.
- New test file `tests/unit/social/test_party_composition.py` extended with 6 new tests (16
  pre-existing + 6 new = 22), not `tests/unit/domains/adventure/test_phase3_route_scoring.py` (see
  AC3's disclosed reinterpretation above).
- `docs/parity_ledger/social_narrative.yaml`: new `SOC-244` entry (confirmed next-free id) --
  `STRAT-227` in `strategic_cognition.yaml` was deliberately NOT extended a third time, since
  `scoring.py` is untouched.
- `docs/mechanics/04_strategic_cognition.md`: new `## 7` section documenting `PartyCompositionScorer`
  for the first time ever (it had no Mechanics Bible coverage before this ticket), including §7.1
  (pre-existing role-diversity/OCEAN base score) and §7.2 (the new trust/bonds term).
- `docs/simulation/social_systems_contract.md`: added `party_composition.py` to the file's Source
  line and a new `## Party Composition` section.
- `docs/simulation/domains/adventure_contract.md`: new "What It Reads" row for
  `entity.social.trust_history`/`.bonds`.
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`: closed the
  "Relationship-aware FORM_PARTY" Future Extension Pattern bullet.

Two pre-existing, unrelated findings disclosed (not fixed, out of scope): (1) `party_composition.py`'s
own module docstring mis-cites "Logic IDs: SOC-231/SOC-232" for its role-diversity/OCEAN scoring, but
those real IDs in `social_narrative.yaml` describe unrelated behavior (Grief urgency, Nemesis
relation) -- flagged in the new `SOC-244` entry's `divergence_note`. (2) `src/core/state.py:573`'s
`GroupRecord.composition_score` field comment has a second instance of the same SOC-232 mis-citation.
(3) `src/systems/world_systems/groups.py:312` is a second, pre-existing caller of
`PartyCompositionScorer.score()` (positional args only, no `actor` concept) -- confirmed unaffected
by the new optional/keyword-only parameter, correctly untouched.

One deviation from the smooth pipeline: the original Implement dispatch was cut off mid-session by
an API rate-limit error after completing Steps 1-5 (code, tests, parity ledger, Mechanics Bible) but
before Steps 6-8 (the 2 remaining docs + design-doc bullet closure). I (the orchestrator) verified
Steps 1-5's landed state directly (all 22 tests passing, `scoring.py` diff confirmed empty, YAML
re-validated), then completed Steps 6-8 directly per plan.md's exact specified content, rather than
re-dispatching a fresh Implement pass for a handful of already-fully-specified doc edits.

## Test Summary

`pytest tests/unit/social/test_party_composition.py -v`: **22 passed** (16 pre-existing + 6 new).
`pytest tests/unit/domains/adventure/test_phase3_route_scoring.py::test_sociability_weight_is_0_40_on_form_party_route -v`:
**1 passed**, confirming the existing sociability-weight test remains completely unmodified and
green (direct proof AC4 holds). Combined regression check across this and the 2 prior sibling
tickets in this epic (`test_party_composition.py` + `test_phase3_route_scoring.py` +
`test_capability_confidence_scoring.py` + `test_memory_informed_scoring.py`): **47 passed, 0
failed** -- confirms no cross-contamination between the three scoring-term tickets landed in this
epic. `git diff --stat -- src/domains/adventure/scoring.py` returns empty, confirming AC4's
bit-identical requirement holds unconditionally.

## Files Changed
- `src/systems/social_systems/party_composition.py` -- new `actor` param, `TRUST_BONUS_WEIGHT`
  constant, trust/bonds lookup and additive term
- `src/domains/adventure/generator.py` -- FORM_PARTY branch passes `actor=entity`, folds trust term
  into `confidence`, extended `reason=` telemetry
- `tests/unit/social/test_party_composition.py` -- 6 new tests
- `docs/mechanics/04_strategic_cognition.md` -- new `## 7` section (first-ever `PartyCompositionScorer`
  coverage)
- `docs/parity_ledger/social_narrative.yaml` -- new `SOC-244` entry
- `docs/simulation/social_systems_contract.md` -- Source line + new `## Party Composition` section
- `docs/simulation/domains/adventure_contract.md` -- new "What It Reads" row
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` -- closed
  Future Extension Pattern bullet

## Completion Summary

Made `FORM_PARTY` route generation relationship-aware: `PartyCompositionScorer.score()` now folds a
trust/bonds-derived term (weight 0.15, bond-sentiment-priority, additive) into its existing
role-diversity/OCEAN-compatibility base score when an `actor` is supplied, and
`AdventureRouteGenerator.generate()`'s FORM_PARTY branch uses this for both `expected_benefit` and
`confidence`. The entire change lives at generation time in `party_composition.py`/`generator.py`;
`scoring.py`'s existing `sociability × 0.40` `personality_bias` term is completely untouched,
satisfying AC4 trivially. All 4 ACs satisfied, with AC1/AC3 carrying disclosed, Review-approved
honesty notes about genuine-per-candidate-read-vs-pool-aggregate-output and the reinterpreted test
location respectively. 22/22 new-file tests pass; the pre-existing sociability-weight test remains
green and completely unmodified. Plan review approved on the first round -- no correction needed,
unusual for this epic. Two pre-existing, unrelated SOC-231/232 ID-mis-citation bugs and one
unaffected second caller of `PartyCompositionScorer.score()` were found and disclosed, not silently
fixed.

Two minor, non-blocking test-coverage gaps were flagged by the Test phase, neither warranting a
follow-up ticket given their low severity: (1) `src/systems/world_systems/groups.py:312`'s
pre-existing, unaffected second caller of `PartyCompositionScorer.score()` (never passes `actor`)
has no dedicated pinned-value regression test proving its output is byte-identical before/after
this change -- the same underlying `actor is None` code path IS directly pinned by
`test_party_composition_score_unchanged_when_actor_omitted`, so the risk is structural/indirect
coverage only, not an untested code path. (2) `generator.py`'s new `max(0.0, ...)` confidence-floor
clamp in the FORM_PARTY branch has no dedicated test, since it is defensively inert under all
realistic conditions (only reachable when `sociability < 0.2`, the branch's own gating condition
for generating a FORM_PARTY route at all, per the plan's own analysis) -- both gaps were considered
during Plan and judged acceptable residual risk rather than deferred scope.
