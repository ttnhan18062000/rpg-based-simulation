---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260904-FACTION-EXPAND-DIRECTIVE
artifact_type: test_plan
tags: [faction, grand-strategy]
---

# Test Plan — TCK-20260904-FACTION-EXPAND-DIRECTIVE

## Regression Surface

**Unit — faction decision (must keep passing unmodified in behavior, only new cases added):**
- `tests/unit/domains/faction/test_faction_decision_phase.py` — all 11 existing tests, in particular
  `test_faction_decision_phase_produces_defend_border`,
  `test_faction_decision_phase_trade_route`,
  `test_faction_decision_phase_commission_quest`,
  `test_faction_decision_phase_high_tension_emits_defend_and_commission`,
  `test_faction_decision_phase_no_factions_returns_empty`,
  `test_faction_directive_not_in_state_update`,
  `test_faction_decision_phase_returns_list_not_state_update`,
  `test_faction_directive_has_slots` — must not regress: adding a 4th branch must not change when
  `DEFEND_BORDER`/`TRADE_ROUTE`/`COMMISSION_QUEST` fire, and the two anti-drift guards must still pass
  with zero modification to their assertions.
- `tests/unit/domains/faction/test_faction_awareness.py`, `test_diplomacy.py`,
  `test_siege_model.py`, `test_territory_transfer.py`, `test_war_exhaustion.py` — unrelated directive
  kinds but same module family (`faction_decision.py`/`faction_constants.py` imports); confirm no
  import-time or shared-fixture breakage from the new constant/branch.

**Unit — demographics (population-pressure signal source, read-only consumer, must not regress):**
- `tests/unit/world/test_demographics.py` — all `compute_population_density`/`compute_regional_scarcity`
  coverage (TC-D5-01–04, E52B scarcity tests) — this ticket only reads these functions, never modifies
  `cohort.py`.

**Unit — world dynamics / camp (new optional parameter must not break existing call sites):**
- `tests/unit/world/test_world_dynamics.py` — all `resolve_dynamics()` call sites (**5** in this file,
  re-verified by grep: lines 15, 37, 58, 68, 419 — an earlier draft of this plan undercounted this as
  4).
- `tests/unit/world/test_camp_lifecycle.py` — `test_camp_maturity_and_spawn`,
  `test_camp_clearing_reward` (and any others in the file) — existing camp maturity/spawn/clearing
  behavior must be byte-identical when no `faction_directives` (or an empty list) is passed. 7
  `process_camps()` call sites (lines 64, 98, 117, 136, 159, 251, 286).
- `tests/unit/world/test_natural_creature_reproduction.py` — **required addition, previously omitted
  from this Regression Surface entirely.** 9 `process_camps()` call sites (lines 47, 100, 118, 135,
  152, 172, 198, 224, 257), all constructing `state.camps` directly and exercising the same
  `for c_id, camp in state.camps.items():` loop (`src/world/camp.py`) that Step 6 of `plan.md` adds
  its new `EXPAND_TERRITORY`-consumption branch to. This file's 14 tests must be run and pass
  unmodified — a regression here would mean the new branch altered maturity/spawn behavior for camps
  that carry no matching directive, which is exactly the byte-identical-when-absent guarantee this
  ticket requires.
- `tests/unit/world/test_sovereignty_events.py` — `resolve_dynamics(..., cadence=cadence)` call site.
- `tests/unit/world/test_creature_territory_lifecycle.py` — 4 `resolve_dynamics()` call sites, confirms
  the unrelated `CreatureTerritoryService` consumer of `state.camps` is unaffected.
- `tests/unit/world/test_reproduction_humanoid_cadence.py` — 2 `resolve_dynamics()` call sites,
  confirms `HumanoidReproductionService` cadence gating is unaffected.
- `tests/integration/world/test_phase9_stability.py` — `resolve_dynamics()` integration call site.

**Integration — full pipeline (confirms phase-8b wiring point + downstream `world_dynamics` threading
survive a real `refine()` call):**
- `tests/integration/scenarios/test_faction_campaign.py` — exercises `FactionDecisionPhase` inside a
  real multi-tick campaign; confirms the new branch doesn't destabilize existing
  DEFEND_BORDER/TRADE_ROUTE/COMMISSION_QUEST/war/siege behavior.
- `tests/integration/scenarios/test_demographics.py` — exercises `compute_population_density()` "wired"
  assertions; confirms the new faction-side consumer doesn't alter demographics' own behavior. This
  file also has 1 direct `resolve_dynamics()` call site (line 333, `resolve_dynamics(state,
  StateUpdate(), generator, cadence)`) — previously omitted from Step 4's call-site enumeration in
  `plan.md`; that omission is corrected there, and this file's behavior must stay unchanged here too.

**Scoped pytest commands for the above (run before claiming completion):**
```
pytest tests/unit/domains/faction/ tests/unit/world/test_demographics.py tests/unit/world/test_world_dynamics.py tests/unit/world/test_camp_lifecycle.py tests/unit/world/test_natural_creature_reproduction.py tests/unit/world/test_sovereignty_events.py tests/unit/world/test_creature_territory_lifecycle.py tests/unit/world/test_reproduction_humanoid_cadence.py -v
pytest tests/integration/scenarios/test_faction_campaign.py tests/integration/scenarios/test_demographics.py tests/integration/world/test_phase9_stability.py -v
```

## New Tests Required

Per Acceptance Criteria, in `tests/unit/domains/faction/test_faction_decision_phase.py` unless noted:

1. **`test_faction_decision_phase_expand_territory_emitted_under_population_pressure`**
   Category: unit. Verifies: given a faction with territory whose regions are under population
   pressure (per whatever threshold/aggregation `plan.md` selects over
   `compute_population_density`/`compute_regional_scarcity`) and at least one faction-less region
   exists (`RegionState.owner_faction_id is None`) elsewhere in `state.regions`, `execute()` emits an
   `EXPAND_TERRITORY` directive for that faction with `target_region` set to the faction-less region's
   id. Location: `tests/unit/domains/faction/test_faction_decision_phase.py`.

2. **`test_faction_decision_phase_expand_territory_not_emitted_without_pressure`**
   Category: unit (negative/no-trigger case, explicitly required by AC). Verifies: a faction whose
   territory is under normal (non-scarce/non-dense) conditions does not emit `EXPAND_TERRITORY`, even
   when a faction-less region exists. Location: same file.

3. **`test_faction_decision_phase_expand_territory_not_emitted_without_target`**
   Category: unit (edge case). Verifies: a faction under population pressure but with **no**
   faction-less region available anywhere in `state.regions` does not emit `EXPAND_TERRITORY` (no
   valid target — must not emit a directive with `target_region=None` as a fallback). Location: same
   file.

4. **`test_faction_decision_phase_expand_territory_target_resolution_deterministic`**
   Category: unit (determinism guard). Verifies: with multiple faction-less regions available, target
   selection is deterministic and reproducible across repeated calls with the same input (e.g. sorted
   by region id, matching the `cohort.py` precedent) — construct two faction-less regions with ids
   chosen so an unsorted-dict-iteration bug would be observable, assert the same target is picked both
   times. Location: same file.

5. **`test_faction_decision_phase_expand_territory_transient_not_persisted`**
   Category: architecture guard (matches FAC-003's existing verification approach, explicitly required
   by AC). Verifies: `EXPAND_TERRITORY` directives never appear as a `StateUpdate`/`AuthoritativeState`
   field — extend (or add a sibling to) the existing `test_faction_directive_not_in_state_update`
   pattern; also assert a full `refine()`-style call sequence (construct state → call
   `FactionDecisionPhase.execute()` → assert returned value is `list[FactionDirective]`, not merged into
   any `StateUpdate`) produces no `AuthoritativeState` field named anything expand/territory-related.
   Location: same file, alongside the existing anti-drift guards.

6. **`test_faction_constants_expand_territory_value`**
   Category: unit (trivial but required for constant-shape parity with the other 3). Verifies:
   `EXPAND_TERRITORY == "EXPAND_TERRITORY"` in `src/engine/faction_constants.py`, importable from both
   `faction_constants.py` and re-exported (or directly importable) from `faction_decision.py`, matching
   the existing `DEFEND_BORDER`/`TRADE_ROUTE`/`COMMISSION_QUEST` import pattern. Location: same file.

Per the CampService integration leg (real, tested, non-stub per AC), new tests in
`tests/unit/world/test_camp_lifecycle.py` (or a new `test_camp_faction_directive_consumption.py` in the
same directory if `plan.md` prefers isolating the new surface):

7. **`test_camp_service_consumes_expand_territory_directive`**
   Category: unit / integration (crosses `FactionDecisionPhase` → `CampService`, the 3rd of the 3
   phases AC requires covered). Verifies: constructing a `state.camps` entry whose resolved region
   matches an `EXPAND_TERRITORY` directive's `target_region` produces the documented consumption effect
   (whatever `plan.md` specifies — e.g. an altered `CampUpdate.maturity_delta`) when
   `CampService.process_camps(state, generator, faction_directives=[...])` is called directly. Location:
   `tests/unit/world/test_camp_lifecycle.py`.

8. **`test_camp_service_ignores_expand_territory_directive_for_other_region`**
   Category: unit (negative case). Verifies: a camp whose region does **not** match any
   `EXPAND_TERRITORY` directive's `target_region` is unaffected — same maturity/spawn behavior as
   today, with directives present but irrelevant. Location: same file.

9. **`test_camp_service_process_camps_backward_compatible_no_directives`**
   Category: architecture guard (regression-prevention for the new optional parameter). Verifies:
   calling `CampService.process_camps(state, generator)` with **no** `faction_directives` argument (the
   pre-existing call signature, still used by all production call sites unless `world_dynamics.py` is
   also updated to always pass it) behaves byte-identically to before this ticket — i.e. the new
   parameter is genuinely optional and does not change default behavior. Location: same file.

10. **`test_resolve_dynamics_threads_faction_directives_to_camp_service`**
    Category: integration (confirms the full 3-phase threading: `pipeline.py`'s `faction_directives`
    local → `resolve_dynamics(..., faction_directives=...)` → `CampService.process_camps(...,
    faction_directives=...)`). Verifies: calling `WorldDynamicsSystem.resolve_dynamics(state, update,
    generator, cadence=..., faction_directives=[<EXPAND_TERRITORY directive>])` results in the same
    consumption effect verified in test 7, confirming the parameter is genuinely passed through, not
    silently dropped at the `resolve_dynamics()` layer. Location: `tests/unit/world/test_world_dynamics.py`.

## Scoped Pytest Commands

```
pytest tests/unit/domains/faction/test_faction_decision_phase.py -v
pytest tests/unit/domains/faction/ -v
pytest tests/unit/world/test_camp_lifecycle.py tests/unit/world/test_world_dynamics.py tests/unit/world/test_natural_creature_reproduction.py -v
pytest tests/unit/world/ -k "camp or faction or dynamics" -v
pytest tests/integration/scenarios/test_faction_campaign.py -v
```

`tests/unit/world/test_natural_creature_reproduction.py` is listed **by explicit file name** above,
not relied on via the `-k "camp or faction or dynamics"` line below it — verified by direct
`--collect-only` run that the `-k` filter only matches 1 of this file's 14 tests
(`test_camp_maturity_threshold_spawns_natural_creature_offspring`, via the substring "camp"); its
other 13 tests (named around `spawn_eligibility`, `birth`, `reproduction`, `genetics`) do not contain
"camp", "faction", or "dynamics" and would be silently skipped by that filter alone. The `-k` line is
a broader, non-exhaustive sweep of `tests/unit/world/`; it is not a substitute for the explicit file
list on the line above it, which is authoritative for this ticket's required regression run.

Never `pytest tests/` — always scoped to `tests/unit/domains/faction/`, `tests/unit/world/`
(camp/dynamics/natural-creature-reproduction-relevant subset), and the one faction-campaign
integration scenario, per the domain this ticket actually touches.

## Anti-Drift Test Guards

- **FAC-003 transient-scratch guard** (test 5 above): must continue to catch any future accidental
  addition of a `faction_directives`/`expand_territory`-shaped field to `StateUpdate` or
  `AuthoritativeState` — this is the single most important regression this ticket must not introduce,
  given the ticket's own explicit "must NOT be persisted" requirement.
- **`resolve_dynamics()`/`process_camps()` backward-compatibility guard** (test 9 above, plus the full
  existing regression surface's call sites in the "Regression Surface" section): must catch any
  accidental signature change that breaks any of the 16 confirmed `resolve_dynamics()` call sites (1
  production + 15 test, enumerated in `plan.md` Step 4) or 17 confirmed `process_camps()` call sites
  (1 production + 16 test, enumerated in `plan.md` Step 6) — none of which currently pass a
  `faction_directives` argument.
- **Mutual-exclusivity non-interference guard**: extend
  `test_faction_decision_phase_high_tension_emits_defend_and_commission`-style coverage with one case
  where a faction simultaneously qualifies for `DEFEND_BORDER` (or `TRADE_ROUTE`) **and**
  `EXPAND_TERRITORY`'s population-pressure gate, asserting both directives are emitted together (unless
  `plan.md` explicitly decides `EXPAND_TERRITORY` should be mutually exclusive with one of the existing
  three, in which case this test asserts that exclusivity instead) — prevents the new branch from
  silently suppressing or duplicating existing directive emission.
- **No Camp/Nest/City-ownership scope-creep guard**: a test asserting `EXPAND_TERRITORY` target
  resolution never selects a region based on `state.camps` contents or any City-ownership-aware
  signal — only `RegionState.owner_faction_id` — catches accidental scope expansion into the two
  explicitly out-of-scope target-resolution strategies.
- **`recipe_materials()` non-hard-gate guard**: a test constructing a faction whose entities/territory
  would have `recipe_materials()` return an empty tuple (the confirmed real-world case, since
  `known_recipes` is populated via the disjoint `craft_*` namespace) still allows `EXPAND_TERRITORY` to
  fire under population pressure alone — catches an accidental hard-gate on the near-inert predicate
  that would silently make the branch unreachable in production.
- **Determinism guard** (test 4 above): catches a non-deterministic target-resolution implementation
  (e.g. relying on raw dict iteration order over `state.regions` without sorting), which would break
  the kernel's overall determinism guarantee (`docs/engine/kernel.md`) the same way an unsorted
  `find_adjacent_regions`/`_check_migration` implementation would have.
