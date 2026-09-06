---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE
phase: done
date: 2026-09-06
tags: [testing, simulation-quality, corpus]
---

# TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE

## Title
World Corpus Test Coverage for New Features (M9) — tracking epic for the 8-ticket corpus-authoring/gap-closure sweep

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` is, like M8, an "informs" epic
with no buildable deliverable of its own — it classifies all 32 stateful ideas against this repo's
real test-tier framework and specifies concrete corpus-test plans, with the actual building deferred
to "the relevant idea's own ticket or a dedicated corpus-authoring ticket." Since this doc was
written (2026-08-24), M2 through M8 have all shipped — re-verified against real code before
ticketing, several items this doc flagged as blocked are now genuinely unblocked, one flagged gap
(`entity_evolved`) is confirmed still real, and the single highest-value finding
(`CampaignScorecardEvaluator`'s 7-fixed-field gap) is confirmed still open and now directly
actionable since all 4 ideas it blocks (53/55/58/62) have shipped via M5.

This epic tracks child tickets only; no direct implementation happens here.

**Real findings from this scoping pass, not inherited uncritically:**
- **Idea 66's item 2 (Region/Place corpus-wide migration) is fully resolved, not merely planned.**
  Confirmed directly against `tickets/done/TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD.md`: the
  actual implementation followed this epic's own recommended two-stage pilot (Stage A
  `unit_information_source`, Stage B `hero_guild_routing`) and `state_hash`-first recalibration
  procedure exactly, including handling the one real deviation found (`state_hash` itself was blind
  to Place data, triaged and a new `canonical_state_hash` field added instead of a silent workaround).
  No child ticket needed for this item — it's historical, not open.
- **`entity_evolved` event gap confirmed still real** (item 3's standalone finding) — zero real code
  hits for this event type anywhere in `src/`, confirmed by direct grep.
- **`CampaignScorecardEvaluator.evaluate()` still checks exactly the same 7 fixed fields** named in
  this epic's item 1, none touching reputation/nemesis/Chronicle fidelity — confirmed directly against
  `src/domains/campaigns/scorecard.py`. All 4 ideas it blocks (53, 55, 58, 62) shipped via M5 (PR
  #128) without this prerequisite being satisfied — a real, standing testing gap for already-live
  mechanics, not a future concern.
- **Several items 4 entries flagged "blocked" are now unblocked, re-verified directly:**
  - Idea 60 (Reputations Are Local)'s "hard-blocked... determinism-aware pass" note is cleared —
    `src/replay/fingerprint.py:72` confirmed to already include `regional_reputation` in the
    fingerprint string (landed as part of M5).
  - Ideas 32+43, 51/52, 65's "blocked on idea 43"/"blocked on 43+59" notes are cleared — idea 43
    (`TCK-20260831-POPULATION-COHORT-SEEDING`) and idea 59
    (`TCK-20260905-HOME-EXILE-REFUGEE-THREADS`) are both confirmed DONE.
  - Idea 54's "gated on Clan" note is cleared — Clan (idea 36) shipped in M2.
- **Item 6 (known scale ceiling) re-confirmed still accurate, not stale.**
  `TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION` is DONE, but its own Completion Summary confirms
  it delivered an honest finding (the ~68-entity ceiling is real, `WorldProceduralGenerator` remains
  broken/dead code) rather than fixing the ceiling — no idea currently needs a larger world, so this
  isn't blocking anything today, matching the epic doc's own original framing exactly.
- **Idea 63 (Belief/Religion) remains genuinely not concretely specifiable** — the schema itself is
  underspecified with no real anchor to build a scenario against; explicitly excluded from this
  epic's child tickets, not silently dropped (see Out of Scope).

## Scope
- Track, at epic level only, the 8 child tickets below.
- Serve as the `## Related Tickets` link target once any child ticket is picked up for real
  implementation.
- Correct the epic doc's own item 2 (idea 66) to historical/resolved status (done in this same pass).
- Nothing else. No investigation.md/plan.md/test_plan.md staging artifacts at the epic level — each
  child ticket carries its own once picked up for implementation.

## Out of Scope
- Anything from Milestones 1 through 8's own functional scope — all confirmed DONE, not re-litigated.
- Idea 63 (Belief/Religion) corpus testing — genuinely not concretely specifiable yet; revisit once
  the schema itself is grounded, not part of this epic's child tickets.
- Re-litigating the 2026-07-13 Coverage Decision Gate's FACTION/INFORMATION saturation finding.
- Fixing `WorldProceduralGenerator`'s scale-ceiling bug — `TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION`
  already closed as an honest-finding ticket; no idea today needs it, so re-opening it isn't this
  epic's job.

## Acceptance Criteria
- [x] This epic ticket exists at `## Status: EPIC_SCOPED`, listing all 8 child tickets, with no
      implementation performed as part of closing this acceptance criterion.
- [x] The epic doc's item 2 (idea 66) is corrected from "recommendation" framing to confirmed-resolved
      status, with the real implementing ticket cited.
- [x] A future session that picks up any child ticket runs it through the full standard-tier pipeline
      and links back to this epic. All 8 children landed: `TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS`,
      `TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST`, `TCK-20260906-ENTITY-EVOLVED-EVENT-GAP`,
      `TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS`, `TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS`,
      `TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS`, `TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED`,
      `TCK-20260906-RACE-DIVERSITY-AUDIT-INVESTIGATION` (2026-09-06, this batch).

## Related Tickets
### Child tickets (implementation sequence — see `tickets/done/m9-corpus-test-coverage/SEQUENCE.md`, moved from `tickets/todos/` once the last child ticket landed)
- `TCK-20260906-CAMPAIGN-SCORECARD-EVALUATOR-FIELDS` — item 1, highest value, fully specified already.
- `TCK-20260906-ENTITY-EVOLVED-EVENT-GAP` — item 3's standalone finding, small and independent.
- `TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS` — ideas 32+43, 51/52, 54, 60, 65 (item 4 entries
  whose blockers cleared during this scoping pass).
- `TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS` — ideas 4, 10, 13, 14, 22, 30, 33, 36/40, 39,
  44, 49 (item 4 entries needing only an added assertion to an existing corpus run).
- `TCK-20260906-CORPUS-TEST-NEW-WORLD-NEEDED` — ideas 50, 64 (item 4 entries needing a genuinely new
  Unit-tier world).
- `TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST` — the real `simq_long_run_observation.py`
  default-ticks bug (item 4, ideas 20/34) plus their corpus test and the age-tier reconciliation
  question.
- `TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS` — ideas 48, 57 (item 4 entries needing longer-run/
  stress-tier corpus extensions).
- `TCK-20260906-RACE-DIVERSITY-AUDIT-INVESTIGATION` — idea 37's real gap (no race-diversity dimension
  in the corpus registry) — investigative, scopes the audit rather than building it directly.

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` — corrected in this pass (item 2
  resolved-status update)
- `docs/simulation_quality/corpus_tier_taxonomy.md`
- `docs/brainstorm/rpg_expected_schemas.html` — "Expected Events" section, the full per-idea event
  registry this epic's item 3/4 draw from

## Related Stored Artifacts
None — epic tier tracks child tickets only; each child ticket carries its own staging artifacts once
picked up for implementation.

## Related Code Areas
- `src/domains/campaigns/scorecard.py` (`CampaignScorecardEvaluator`)
- `tools/simq_long_run_observation.py`
- `config/simulation_quality/corpus_registry.yaml`
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- Each child ticket's own Investigate phase should re-confirm its specific per-idea citations against
  real code at implementation time (mechanism status, exact field names, corpus world composition),
  not just inherit this scoping pass's citations — the same discipline `TCK-20260823-EPIC-RPG-M6-
  POLITICAL-IDENTITY`'s own children applied.
- `SEQUENCE.md` (now in `tickets/done/m9-corpus-test-coverage/`, originally `tickets/todos/`) enforces
  build order for `implement-epic`.
- The idea-37/idea-20 age-tier reconciliation questions were genuinely open design decisions at
  scoping time — both resolved by their own child tickets: idea 37's registry-shape question by
  `TCK-20260906-RACE-DIVERSITY-AUDIT-INVESTIGATION` (answered, not built — no demonstrated need),
  idea 20's `get_age_bracket()`/`LifeStage` overlap by `TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST`
  (already resolved by a prior ticket, `TCK-20260824-LIFE-STAGE-TRANSITIONS`, cited rather than
  re-decided).

## Implementation Notes
This epic tracked only — no direct implementation at the epic level, per its own Scope. Each
child ticket ran its own full standard-tier pipeline independently; see each child ticket's own
Implementation Notes for details.

## Test Summary
See each child ticket's own Test Summary. No epic-level tests.

## Files Changed
None directly by this epic ticket, beyond its own body and the epic doc it tracks
(`docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`, corrected across multiple
child ticket landings — most recently by `TCK-20260906-RACE-DIVERSITY-AUDIT-INVESTIGATION`'s own
idea-37 resolution).

## Completion Summary
All 8 M9 child tickets landed with zero material scoping drift — every load-bearing citation this
epic's own scoping pass made held up under implementation scrutiny, though nearly every child
ticket found and honestly disclosed real, narrower corrections beyond this epic's own text (wrong
field names, conflated mechanisms, dead/unreachable pipeline paths, a same-file threshold
conflation, a field-system conflation between `PlaceKind` and `RegionState.kind`) — never forced or
fabricated, always resolved with real evidence or an explicit deferral. Real highlights: idea 39's
Campaign-mode testing gap closed with 2 new evaluator fields + a decoupled real-pipeline test suite
after discovering `CampaignScorecardEvaluator` and the real multi-episode `CampaignOrchestrator`
were structurally disjoint (a real premise flaw in this epic's own scoping, corrected rather than
forced); a genuinely stale tooling default (`simq_long_run_observation.py`'s 5000-tick default,
0.03% of the real elder threshold) fixed with a guard, not a reckless bump; a real `entity_evolved`
observability gap closed with a correctly-wired production event; 16 corpus-test assertions
authored across 2 tickets covering 16 ideas total, with 11 real premise corrections found along the
way; a real stress-tier pipeline-integration test for idea 48 after finding the ticket's own scope
conflated two separate field systems; idea 50/64 confirmed to have already been correctly
documented as unshipped by this epic's own scoping pass, needing only formal closure; and idea 37
confirmed already fully shipped with real, adequate test coverage, closing this epic's last open
question. Zero ideas were left silently unaccounted for.
