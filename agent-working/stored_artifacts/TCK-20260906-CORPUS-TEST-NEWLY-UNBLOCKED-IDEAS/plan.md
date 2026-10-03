---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS
date: 2026-09-06
---

# Plan: TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS

## Ordered Steps

1. **Idea 60** — `tests/simulation_quality/test_regional_reputation_corpus.py`. Compile/load
   `frontier_extended` (reuse existing corpus-loading helper pattern from a sibling
   `tests/simulation_quality/` file), run enough ticks for at least one entity to have
   `regional_reputation` entries for >=3 regions (or, if the real profile's own tick budget can't
   guarantee this deterministically, hand-seed via `V2EntityBuilder.social(regional_reputation={...})`
   run through one `Kernel.tick_once()` to prove the field round-trips through the real
   `AuthoritativeState`/fingerprint path — decide based on what Investigate found the real profile
   actually produces). Assert >=3 distinct values.
2. **Idea 32+43** — `tests/simulation_quality/test_reproduction_cohort_seeding_corpus.py`. Real
   `frontier_living_world` calibration run (`tools/calibrate_simq.py` machinery or a direct
   `Kernel`-driven run matching this repo's own calibration convention). Assert `demographic_birth`
   count >= 1. Directly assert `PopulationCohort.migration_threshold == 0.7` on the real compiled
   cohort data (not the calibration run itself, since this is a static field default). Assert a
   real child entity's genetics multiplier is in `[0.8, 1.3]` (via `genetics.py`'s own real
   function, given real parent attribute values).
3. **Ideas 51/52** — `tests/simulation_quality/test_expand_territory_corpus.py`. Real
   `frontier_marches` run long enough for a real `EXPAND_TERRITORY` directive to fire (per
   `faction_decision.py`'s own gating: mean scarcity over territory > 0.7). Assert the directive's
   `target_region` is adjacent and unclaimed at decision time.
4. **Idea 54** — `tests/simulation_quality/test_clan_reputation_witnessed_betrayal.py`. Hand-build
   `AuthoritativeState` with 2 `ClanState` entries (4 members each), one `GroupRecord` for a Clan-A
   member's party with `grievance_log` at/above `effective_defection_threshold` (baseline 3). Run
   `Kernel.tick_once()`, confirm `state.clans["clan_a"].clan_reputation` dropped by
   `CLAN_REPUTATION_MISCONDUCT_DELTA` (-0.25). Then call `SocialAppraisalSystem.appraise_contract()`
   directly (pure function, no bond/history) for a stranger observer judging an unmet Clan-A member,
   both BEFORE (clan_reputation=1.0 baseline) and AFTER (post-defection clan_reputation) — assert
   `trust_score` measurably lower after.
5. **Idea 65** — `tests/simulation_quality/test_named_refugee_threads_corpus.py`. Real
   `crowded_frontier` run with a region driven to/above `calamity_intensity=0.6` (matching
   `DisplacementService.compute_displacement()`'s own real gate — confirm exact threshold during
   Implement by reading `src/world/displacement.py` directly). Assert a displaced entity's
   `home_region_id` is set to the original (fled-from) region, not the new region, and that a
   displacement occurred this tick (via `EntityUpdate.new_position` or an equivalent real signal).

## Files to Change
- 5 new test files under `tests/simulation_quality/` (listed above) — no production code.
- Ticket file itself: Implementation Notes + Completion Summary (Finalize).

## Explicit Scope Guards
- No `src/` production code changes — this is a pure test-authoring ticket.
- Do not build a new registered corpus world for idea 54 (see investigation.md's correction) — a
  hand-scripted Unit-tier proof is the scope-appropriate choice.
- Do not exercise `resolve_contract_outcome(betrayal=True)` (disclosed-dead path) as the idea-54
  trigger — use the real, live party-defection path instead.

## Dependency Map
All 5 steps are independent of each other (different worlds/mechanisms) — may be implemented and
tested in any order or in parallel.

## Acceptance Criteria Map
- AC1 ("all 5 corpus tests authored and passing") — steps 1-5.
- AC2 ("each test asserts a specific named outcome, not a generic smoke test") — see each step's
  own named assertion above; idea 54's test explicitly includes the negative/baseline comparison.

## Unresolved Questions
None.
