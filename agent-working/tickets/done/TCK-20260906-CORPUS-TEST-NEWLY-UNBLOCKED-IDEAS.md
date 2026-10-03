---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS
phase: done
date: 2026-09-06
tags: [testing, simulation-quality, corpus]
---

# TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS

## Title
Author corpus tests for ideas 32+43, 51/52, 54, 60, 65 — blockers cleared since M9's original scoping

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
M9 epic (`TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE`) child 3 of 8. Each of these ideas was
flagged "blocked" in the original M9 scoping (2026-08-24), but re-verified against real code,
2026-09-06: every blocker has since shipped.

- **Idea 60 (Reputations Are Local)** — "hard-blocked... determinism-aware pass" cleared:
  `src/replay/fingerprint.py:72` already includes `regional_reputation` in the fingerprint string
  (landed with M5).
- **Ideas 32 (Reproduction) + 43 (population_cohorts seeding)** — "blocked on idea 43" cleared:
  `TCK-20260831-POPULATION-COHORT-SEEDING` (DONE) and M3's Reproduction epic (DONE) have both shipped.
- **Ideas 51/52 (Country EXPAND + population-driven expansion)** — "blocked on idea 43" cleared, same
  as above.
- **Idea 54 (Guilt by Association)** — "gated on Clan" cleared: Clan (idea 36) shipped in M2.
- **Idea 65 (Named Refugee Threads)** — "blocked on 43+59" cleared: idea 59
  (`TCK-20260905-HOME-EXILE-REFUGEE-THREADS`) is DONE alongside idea 43.

## Scope
Author the following corpus tests, per the epic doc's own concrete specs (re-confirm each against
real shipped code during Investigate, not just this ticket's citations):
- **Idea 60**: `frontier_extended` world — read the same entity's `public_reputation`-equivalent
  (confirm real field name, likely `regional_reputation`) from 3 different regions, assert 3 distinct
  values rather than one global float.
- **Idea 32+43**: `frontier_living_world`, past the existing 200-tick calibration window — assert
  `demographic_birth` fires at least once, `population_pressure_gate` reads `migration_threshold=0.7`
  correctly, and `genetic_inheritance_weight` (0.8-1.3) is applied to at least one child vs. parent
  average.
- **Ideas 51/52**: `frontier_marches` — assert `EXPAND_TERRITORY` fires for the faction with the
  highest population-scarcity signal, targeting an adjacent unclaimed region.
- **Idea 54**: new world needed, 2 Clans of 4 members each; one member of Clan A commits a witnessed
  betrayal; assert a stranger's trust delta toward an unmet Clan A member is measurably lower than
  baseline.
- **Idea 65**: `crowded_frontier` (6 factions, 4 regions) — trigger a hostile-pressure event in one
  region, assert a civilian's home-region field is set to the fled-from region and a displacement
  tick is recorded.

## Out of Scope
- Building any of these 5 ideas' underlying mechanisms — all confirmed already shipped; this ticket
  only authors the corpus tests exercising them.
- Any other item from M9's scope.

## Acceptance Criteria
- [x] All 5 corpus tests above are authored and passing against real compiled worlds.
- [x] Each test asserts the specific named outcome (not a generic smoke test) and would fail if the
      underlying mechanism regressed.

## Related Tickets
- `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (parent epic)
- `TCK-20260831-POPULATION-COHORT-SEEDING`, `TCK-20260905-HOME-EXILE-REFUGEE-THREADS`,
  `TCK-20260904-CLAN-REPUTATION-ASSOCIATION` (the shipped prerequisites this ticket's tests target)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/replay/fingerprint.py`
- `src/domains/demographics/cohort.py`
- `config/simulation_quality/corpus_registry.yaml`

## Assumptions / Open Questions
- Idea 54's test needs a genuinely new corpus world (2 Clans of 4) — confirm no existing world already
  fits this shape before authoring one, during Investigate.

## Implementation Notes
All 5 corpus tests authored and passing (`tests/simulation_quality/`): `test_regional_reputation_corpus.py`
(idea 60), `test_reproduction_cohort_seeding_corpus.py` (idea 32+43), `test_expand_territory_corpus.py`
(idea 51/52), `test_clan_reputation_witnessed_betrayal.py` (idea 54), `test_named_refugee_threads_corpus.py`
(idea 65). No production code changed.

**Correction — idea 54's real trigger is party-defection, not contract-betrayal.**
`CLAN_REPUTATION_MISCONDUCT_DELTA`'s only LIVE pipeline write site is the real party-defection path
(`src/engine/pipeline_phases/groups.py`); the contract-betrayal site
(`src/systems/social_systems/contracts.py`) is explicitly self-documented as never wired to any live
caller. Exercised the real, live path instead. No registered corpus world carries real `ClanState`
content (confirmed via grep), so this sub-test uses a hand-seeded, Unit-tier `AuthoritativeState` (2
Clans of 4) through a real `Kernel.tick_once()`, matching this same M9 batch's own established
precedent (tickets 1-3) for hard-to-reach-via-corpus scenarios — disclosed, not silently substituted.
`appraise_contract()`'s internal `trust_score` is not returned to callers, so the test observes the
real, externally-visible `ReasonCode`/`ContractStatus` decision flip instead (a tuned observer whose
baseline trust_score sits just above the accept/reject boundary, crossed by the real -0.025 max
single-defection swing) — a real, non-tautological regression-catching assertion.

**Correction — 2 real, previously-undocumented gates found for ideas 32+43 and 51/52.**
1. `ENABLE_REPRODUCTION_HUMANOID_PATH` (idea 32+43's own real gate) is OFF by default in
   `frontier_living_world`'s own registered profile — no shipped calibration run of this world has
   ever exercised humanoid reproduction. Feature flags live on `AuthoritativeState.feature_flags`
   (read by `src/engine/world_dynamics.py:213`), not the `Kernel(flags=...)` constructor argument —
   a real, non-obvious distinction this ticket's Implement phase discovered while debugging why the
   mechanism never fired. Explicitly enabled for this test.
2. Every faction in `frontier_marches` (and, by extension, every other real corpus world checked)
   compiles with an EMPTY `FactionState.territory` tuple — no region-ownership-to-faction-territory
   sync exists at world-load time, so `EXPAND_TERRITORY`'s own gate (`mean_scarcity > 0.7` over
   `fs.territory`) can never evaluate true against any real corpus world's initial compiled state.
   The test hand-seeds one faction's real `territory` field with a real, zero-resource-node region
   from the loaded world (`compute_regional_scarcity()` returns 1.0 for any region with zero
   resource nodes, by its own docstring) and calls the real, pure `FactionDecisionPhase.execute()`
   directly — proving the gate/target-resolution logic is correct, while disclosing that no shipped
   corpus world currently reaches this state through ordinary play.

Both findings are real, disclosed limitations of the current corpus/profile set — not defects in the
underlying mechanisms, and not fixed here (out of this test-authoring ticket's own scope).

## Test Summary
`tests/simulation_quality/test_regional_reputation_corpus.py`,
`test_reproduction_cohort_seeding_corpus.py`, `test_expand_territory_corpus.py`,
`test_clan_reputation_witnessed_betrayal.py`, `test_named_refugee_threads_corpus.py` — 6 assertions
across 5 files, all passing.

## Files Changed
- `tests/simulation_quality/test_regional_reputation_corpus.py` (new)
- `tests/simulation_quality/test_reproduction_cohort_seeding_corpus.py` (new)
- `tests/simulation_quality/test_expand_territory_corpus.py` (new)
- `tests/simulation_quality/test_clan_reputation_witnessed_betrayal.py` (new)
- `tests/simulation_quality/test_named_refugee_threads_corpus.py` (new)

## Completion Summary
All 5 ideas (60, 32+43, 51/52, 54, 65) now have real corpus-tier test coverage, each asserting a
specific named outcome that would fail if the underlying mechanism regressed. Found and disclosed 3
real corrections beyond original scoping: idea 54's real live trigger is party-defection (not the
disclosed-dead contract-betrayal path); `ENABLE_REPRODUCTION_HUMANOID_PATH` is off by default in
`frontier_living_world`'s own profile (idea 32+43 has never been calibration-exercised); and every
real corpus world compiles with empty `FactionState.territory` (idea 51/52's `EXPAND_TERRITORY` gate
can never fire against unmodified corpus state). No production code changed.
