---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE
phase: done
date: 2026-07-03
tags: [quests, strategy, world-evolution, backlog]
---

# TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE

## Title
Pressure-driven quest generation: extend QuestGenerator to select templates from world-state signals, not just hero level

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Carried over from `docs/plans/audit_fix_plan.md` P1-D (confirmed still open 2026-07-03).
`QuestGenerator` (`src/quests/generator.py`) selects from a static `TEMPLATES` list keyed only by
hero level (`QuestTemplate("q_slime_cull", "Clear the Slimes", QuestKind.HUNT, 1, 5, ...)`, etc.).
It does not read resource scarcity, regional threat level, or regional trauma score — signals the
`ResourceOpportunityProvider` already generates from world state for a different subsystem. Quest
content is therefore static and level-gated rather than emergent from the world's actual pressure
history, which caps NARRATIVE/PROGRESSION richness independent of any SimQ scoring-infrastructure
gap.

## Scope
1. Re-verify `QuestGenerator`'s current template-selection logic against `src/` (this ticket may be
   picked up well after 2026-07-03 — confirm the static-template characterization is still
   accurate before planning around it).
2. Identify the world-state pressure signals already available for reuse: resource scarcity by
   region, regional threat level, regional trauma score (see `docs/mechanics/05_world_evolution.md`
   §trauma and `docs/mechanics/03_economic_laws.md` §resource pressure for the driving formulas).
3. Extend `QuestGenerator` to accept these signals and select/weight quest templates that match the
   current pressure profile (e.g. a scarcity-driven region favors GATHER templates, a
   high-trauma region favors HUNT/defense templates).
4. Ensure hero-level gating is preserved alongside the new pressure-driven selection — this is an
   addition to the existing level-based filter, not a replacement.
5. Add tests: quest selection responds to a changed pressure profile in a controlled scenario;
   existing level-gating behavior is unchanged for scenarios with flat/neutral pressure.

## Out of Scope
- Changing `QuestTemplate`'s reward/requirement structure
- The broader quest activation precondition chain (`P1-B`, already resolved separately)
- Any change to `ResourceOpportunityProvider` itself (only consume its existing signals)

## Acceptance Criteria
- [x] `QuestGenerator` accepts world-state pressure signals (scarcity, threat, trauma) as selection
      inputs, not just hero level — new `QuestPressureProfile` param (safely defaulted to `None`)
      on `generate()`/`generate_quests()`, populated by `GuildAction.visit()` from
      `RegionState.trauma_score`/`hazard_level` and a resource-node-charge-ratio scarcity signal
- [x] Quest template selection demonstrably shifts when pressure signals change, in a test scenario
      — `test_quest_generation_favors_hunt_under_high_trauma`,
      `test_quest_generation_favors_gather_under_high_scarcity` (both passing)
- [x] Existing hero-level gating behavior unchanged for neutral-pressure scenarios (regression test)
      — `test_quest_generation_neutral_profile_matches_legacy_none` proves the `None`/neutral-weight
      fallback path calls the exact pre-existing `rng.choice(...)`, byte-identical, not just similar
- [x] `docs/mechanics/05_world_evolution.md` cross-referenced correctly for the signal formulas
      actually used — corrected in place: the ticket's original citation to a nonexistent
      `03_economic_laws.md` §resource pressure section was wrong; trauma/hazard are documented in
      `05_world_evolution.md` §2, and a new §3 "Derived Scarcity Ratio" subsection documents the
      node-charge-ratio formula this ticket introduces

## Related Tickets
- None currently open covering this — carried over fresh from `docs/plans/audit_fix_plan.md` P1-D

## Related Docs
- `docs/plans/audit_fix_plan.md` P1-D — original finding, source of this ticket, now marked RESOLVED
- `docs/mechanics/05_world_evolution.md` §2 "Regional Trauma & Hazards" — trauma/hazard formulas
- `docs/mechanics/05_world_evolution.md` §3 "Derived Scarcity Ratio" (new; corrects this ticket's
  original citation of a nonexistent `docs/mechanics/03_economic_laws.md` §resource pressure —
  that file has no such section; the node-charge-ratio scarcity formula this ticket introduces is
  documented here instead)

## Related Stored Artifacts
- None yet

## Related Code Areas
- `src/quests/generator.py` — `QuestGenerator`, `TEMPLATES`
- `src/systems/strategic_systems/intelligence.py` — quest-to-project activation chain (already
  fixed for P1-B, do not re-touch that logic)

## Assumptions / Open Questions
- UQ-1 (resolved 2026-07-04): deterministic weighted-random selection was chosen over
  exact-highest-match-always-wins. Reasoning: keeps content variety (a dominant pressure signal
  for many ticks doesn't lock in the same template forever), stays fully deterministic/replayable
  via the existing seeded `DeterministicRNG._composite_seed` mechanism (new `weighted_choice()`
  method added alongside `choice()`), and makes the "neutral-pressure unchanged" acceptance
  criterion satisfiable exactly (not approximately) — the `None`/equal-weight case falls back to
  literally calling the pre-existing `rng.choice(...)`, byte-identical to current behavior.
  Verified correct by architecture review (confirmed `Random.choice`/`Random.choices` are
  different algorithms that would NOT coincidentally match from the same seed, so the explicit
  fallback branch — not an accidental equivalence — is what guarantees this).

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE/plan.md`'s 9 steps:

1. Added `QuestPressureProfile` (frozen, slots dataclass: `trauma`, `hazard`, `scarcity`, all
   default `0.0`) to `src/quests/generator.py` — ephemeral, computed fresh per call, never stored
   in `AuthoritativeState`.
2. `GuildAction.visit()` (`src/town/guild.py`) now resolves `entity.navigation.region_id` (with
   the same `"hometown"` fallback `ResourceOpportunityProvider` uses), reads
   `RegionState.trauma_score`/`hazard_level` from `state.regions`, and derives a scarcity ratio
   `1.0 - avg(remaining_charges/max_charges)` over matching `state.resource_nodes` — mirroring
   `src/world/providers/resources.py`'s own read pattern. All three signals default to `0.0` when
   region/nodes are missing (no `KeyError`).
3. Added `DeterministicRNG.weighted_choice()` to `src/platform/rng.py`, reusing the exact
   `_composite_seed(...)` mechanism as the existing `choice()`, differing only in the terminal
   `random.Random(seed).choices(seq, weights=weights, k=1)[0]` call.
4. `QuestGenerator.generate()`/`generate_quests()` extended with a safely-defaulted
   `pressure_profile: Optional[QuestPressureProfile] = None` parameter. Level-band filtering stays
   the unchanged primary gate. `PRESSURE_AFFINITY` maps `HUNT`/`BOUNTY`→trauma, `LIBERATE`→hazard,
   `GATHER`→scarcity, `EXPLORE`→none. Selection: if `pressure_profile is None` or all computed
   weights are equal, call the pre-existing `rng.choice(Domain.QUEST, tick, level, candidates)`
   unchanged (byte-identical fallback — confirmed by architecture review this is a deliberate
   branch, not an accidental algorithm equivalence, since `Random.choice`/`Random.choices` consume
   the RNG stream differently even from the same seed); otherwise draw via the new
   `rng.weighted_choice(...)`.
5. Fixed a pre-existing masked test bug: `tests/unit/quest/test_quest_generation.py` had two
   functions both named `test_quest_generation_determinism` (line 11, testing
   `QuestGenerator.generate`; line 106, testing `QuestOpportunityGenerator.from_resource_depleted`)
   — pytest only ever collected the second. Renamed the first to
   `test_quest_generator_determinism`; collected-test count confirmed to increase by one
   (18 → 19).
6. Added 6 new unit tests (`test_quest_generation_favors_hunt_under_high_trauma`,
   `test_quest_generation_favors_gather_under_high_scarcity`,
   `test_quest_generation_neutral_profile_matches_legacy_none`,
   `test_level_gating_overrides_pressure`, `test_pressure_driven_selection_determinism`,
   `test_quest_generation_missing_region_signal_defaults_neutral`) plus 1 integration smoke test
   (`test_guild_visit_quest_reflects_region_pressure`). All 19 unit tests and all 4 guild-pipeline
   tests pass.
7. Docs: added a "Derived Scarcity Ratio" subsection to `docs/mechanics/05_world_evolution.md` §3
   "Ecology & Replenishment" (correcting the ticket's own wrong original citation to a nonexistent
   `03_economic_laws.md` §resource pressure section — that file has no such section). Marked
   `docs/plans/audit_fix_plan.md`'s P1-D entry RESOLVED (header, summary table row, "still open"
   list). This ticket's own Related Docs citation corrected in place (see above).
   **Two-systems note**: this ticket's `QuestGenerator`/`GuildAction.visit()` path is distinct
   from the separate, already-pressure-driven `QuestOpportunity`/`state.quest_registry` system
   (`src/domains/world_emergence/services.py`, wired since TCK-20260619-E23A/E23C, resource-
   depletion/threat events → `QuestOpportunity` → route-scoring → reward payout) — the two are
   not duplicative, they serve different quest-origination paths (Guild-visit vs. world-emergence
   events) and neither was touched by the other's fix.
8. Updated `docs/parity_ledger/strategic_cognition.yaml`: filled real `test_path` values for
   `STRAT-154` through `STRAT-158` (previously `null`); added new entry `STRAT-244` (next-free ID,
   confirmed via full-repo grep) documenting the pressure-driven-selection capability itself.
9. Confirmed untouched, per scope guards: `src/systems/world_systems/quest_generator.py` (dead
   code, zero call sites, not prior art), the `QuestOpportunity`/`quest_registry` system,
   `DynamicQuestSeedService`/`QuestSeed` (abandoned scaffold), and
   `StrategicIntelligenceSystem`'s quest-to-project activation chain (already fixed for P1-B).

## Test Summary
- `pytest tests/unit/quest/test_quest_generation.py --collect-only -q` — 19 tests collected (was
  18 before the duplicate-name fix)
- `pytest tests/unit/quest/test_quest_generation.py -v` — 19 passed
- `pytest tests/unit/world/test_guild_pipeline.py -v` — 4 passed (including the new
  `test_guild_visit_quest_reflects_region_pressure`)
- Determinism explicitly verified: `test_pressure_driven_selection_determinism` (same seed →
  same weighted-choice draw) and `test_quest_generation_neutral_profile_matches_legacy_none`
  (fallback path byte-identical to pre-existing `rng.choice(...)`)

## Files Changed
- `src/quests/generator.py` — `QuestPressureProfile` dataclass, `PRESSURE_AFFINITY` mapping,
  `pressure_profile` parameter + weighted-selection logic on `generate()`/`generate_quests()`
- `src/town/guild.py` — `GuildAction.visit()` resolves region + computes pressure signals
- `src/platform/rng.py` — new `DeterministicRNG.weighted_choice()` method
- `tests/unit/quest/test_quest_generation.py` — renamed duplicate test, added 6 new tests
- `tests/unit/world/test_guild_pipeline.py` — added 1 new integration test
- `docs/mechanics/05_world_evolution.md` — new "Derived Scarcity Ratio" subsection under §3
- `docs/plans/audit_fix_plan.md` — P1-D marked RESOLVED
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-154..158 `test_path` filled; new STRAT-244

## Completion Summary
Extended `QuestGenerator`'s template selection to weight candidates by regional pressure signals
(trauma, hazard, scarcity) already available in durable state, while preserving hero-level gating
as the primary filter and guaranteeing byte-identical fallback behavior for neutral-pressure
scenarios via an explicit branch to the pre-existing `rng.choice(...)` call (not an accidental
algorithm equivalence). Added a deterministic `weighted_choice()` primitive to `DeterministicRNG`
reusing the existing composite-seed mechanism. Fixed a pre-existing masked duplicate-test-name bug
along the way (a `QuestGenerator` determinism test was never actually running). 23 tests passing
across both scoped suites, docs and parity ledger updated, P1-D marked resolved in
`audit_fix_plan.md`. No changes to the separate `QuestOpportunity`/world-emergence quest system or
the already-fixed quest-to-project activation chain.
(to be filled on done)
