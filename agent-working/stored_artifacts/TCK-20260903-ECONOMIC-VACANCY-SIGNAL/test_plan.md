---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260903-ECONOMIC-VACANCY-SIGNAL
artifact_type: test_plan
tags: [economy, lifecycle]
---

# Test Plan — TCK-20260903-ECONOMIC-VACANCY-SIGNAL

## Regression Surface

**Unit — lifecycle:**
- `tests/unit/progression/test_lifecycle.py` — full file, esp. `test_death_by_old_age`,
  `test_combat_death_classification`, `test_permadeath_death_classification`,
  `test_succession_and_heirloom_transfer`, and the `test_default_heir_*` suite
  (`resolve_lifecycle` is the integration site for the new vacancy check; must not change existing
  death/heir/heirloom/life-stage outcomes).

**Unit — economy:**
- `tests/unit/economy/test_economy_health_monitor.py`, `tests/unit/economy/test_economy_alerts.py` —
  `EconomyHealthMonitor`/`GoldHoardingEvent`/`InflationSpiralEvent` behavior must stay unchanged;
  this ticket references the class shape but must not alter its gini-threshold alert logic or its
  `_event_listeners` dispatch wiring.

**Unit/integration — strategic:**
- `tests/unit/strategic/test_occupation_change_scorer.py`,
  `tests/integration/strategic/test_occupation_change_reachability.py` — `OccupationChangeGoalScorer`
  region-count-scan pattern is being reused, not modified; both suites must pass unchanged.

**Integration — town/parity:**
- `tests_v2/parity/test_town_resolution_parity.py` (blacksmith + shop scenarios, per
  `TOWN-017`/`TOWN-026`/`TOWN-028`/`TOWN-043` `test_path` references in
  `docs/parity_ledger/town_resource.yaml`) — crafting must stay entity-agnostic unless Plan
  deliberately decides otherwise (see investigation.md Anti-Drift Hazards).

**World-event plumbing precedents** (locate exact test paths at implementation time — not
enumerated in the ticket's own Related Code Areas, found during investigation):
- Tests exercising `DemographicCycleService.process_demographics`
  (`src/domains/demographics/cohort.py`) — the closest real precedent for
  death-triggers-`WorldEvent`-via-`world_events_add`.
- Tests exercising `FactionAwarenessService.compute_tension_updates`
  (`src/engine/faction_decision.py`) — the closest real precedent for an authoritative system
  reading `state.recent_world_events` (one-tick-lagged).
- Run `grep -rl "process_demographics\|FactionAwarenessService\|world_events_add" tests/` to
  enumerate the exact files before scoping the final regression command.

**Determinism/canonical-hash suite** — required only if Plan selects Option 2 (a new durable field
on `BuildingState`/`RegionState`): any new dataclass field must carry canonical-hash coverage from
day one (the explicit lesson from `TCK-20260902-PLACE-SCHEMA-MIGRATION`'s own working-log entry,
which found and fixed a real bug from a hand-rolled fast-constructor's hardcoded field list missing
a new field). Not needed if Option 1 (no new durable schema) is chosen.

## New Tests Required

1. **`test_sole_shopkeeper_death_emits_vacancy_event`**
   - Category: unit
   - Verifies: a region with exactly one living `SHOPKEEPER` (or whichever role(s) Plan selects):
     killing that entity through `LifecycleSystem.resolve_lifecycle` produces a `WorldEvent` of the
     new vacancy category in the returned `StateUpdate.world_events_add`, carrying `vacated_role`
     and `region_id` (via `WorldEvent.subject`/`region_id` or an equivalent typed payload field
     chosen by Plan).
   - Location: `tests/unit/progression/test_lifecycle.py` (colocated with the rest of
     `resolve_lifecycle`'s death-triggered side-effect tests).

2. **`test_non_sole_occupant_death_does_not_emit_vacancy_event`**
   - Category: unit
   - Verifies: a region with two or more living entities holding the same production-relevant role —
     killing one of them does **not** emit the vacancy event (negative case, guards against a
     naive "any production-role death" implementation that ignores the "sole occupant" condition).
   - Location: `tests/unit/progression/test_lifecycle.py`.

3. **`test_vacancy_event_committed_through_authoritative_apply_path`**
   - Category: architecture guard
   - Verifies: the vacancy `WorldEvent` reaches `AuthoritativeState.recent_world_events` after a
     real `apply.py` apply-cycle (not just constructed in isolation) — i.e. run the death through
     the actual `StateUpdate` → `apply_generation`/`apply_partial` path and assert the event is
     present in the post-apply state's `recent_world_events` window. This is the test that
     satisfies acceptance criterion 1's "through the authoritative apply path" language concretely,
     distinguishing it from `EconomyHealthMonitor`'s side-channel `_event_listeners` pattern (see
     investigation.md).
   - Location: `tests/unit/progression/test_lifecycle.py` or a new
     `tests/integration/economy/test_economic_vacancy_signal.py`.

4. **`test_vacancy_signal_readable_by_consuming_system`**
   - Category: integration
   - Verifies: whichever consumer Plan selects (PP-07 `BlacksmithSystem` or PP-20
     `TownResolutionSystem`) actually reads `state.recent_world_events` and reacts (e.g. sets a
     readable flag, adjusts a rate, or otherwise observably changes its output) when the vacancy
     event is present — proven by reading it back from state/events per acceptance criterion 2,
     not by constructing the consumer call in isolation with a hand-built event list.
   - Location: `tests/unit/economy/test_economy_alerts.py` (if PP-07/PP-20 wiring lands near the
     existing alert tests) or a new file colocated with the chosen consumer's own test file
     (`tests_v2/parity/test_town_resolution_parity.py` region if PP-20 is chosen).

5. **`test_vacancy_remains_detectable_across_subsequent_tick_if_unfilled`**
   - Category: integration
   - Verifies: advance at least one more tick after the death without anything "filling" the role —
     the vacancy is still detectable by the consumer (reading the still-in-window
     `recent_world_events`), satisfying acceptance criterion 3. Should also assert/document the
     500-tick `WORLD_EVENT_WINDOW` boundary condition explicitly (see Anti-Drift Test Guards below)
     rather than leaving "remains detectable" untested for its actual bounded lifetime.
   - Location: same file as test 4.

6. **`test_single_production_entity_town_regression_throughput_delta`**
   - Category: integration (regression scenario, matches ticket's own AC directly)
   - Verifies: single-production-entity town, entity killed, N ticks advanced (same seed) vs. a
     same-seed control run where the entity survives — measurable production-throughput delta
     between the two runs (e.g. total crafted items, or gold/resource flow through the blacksmith
     over the N ticks). Per investigation.md's flagged risk, this test's design must make explicit
     whether the delta is expected to come from (a) natural one-fewer-entity effect or (b) the
     consumer's reaction to the vacancy signal — do not leave this ambiguous in the test's own
     docstring/comments, since it directly determines whether the test would still pass if the
     vacancy-signal wiring were accidentally removed.
   - Location: new `tests/integration/economy/test_economic_vacancy_signal.py`.

7. **`test_role_and_region_scope_of_sole_occupant_check`**
   - Category: unit
   - Verifies: the occupancy check is correctly scoped to region (not world-wide) — two regions each
     with exactly one `SHOPKEEPER`; killing the one in region A emits a vacancy event scoped to
     region A only, region B's entity/event is unaffected. Guards against the "global role count"
     misinterpretation flagged in investigation.md's Anti-Drift Hazards.
   - Location: `tests/unit/progression/test_lifecycle.py`.

## Scoped Pytest Commands

```
pytest tests/unit/progression/test_lifecycle.py \
       tests/unit/economy/ \
       tests/unit/strategic/test_occupation_change_scorer.py \
       tests/integration/strategic/test_occupation_change_reachability.py \
       tests/integration/economy/ \
       -v
```

Add, once located (Regression Surface note above):
```
pytest <cohort/faction_decision world-event test files> -v
```

Parity-specific (only the blacksmith/shop-scoped subset, never the full parity suite):
```
pytest tests_v2/parity/test_town_resolution_parity.py -k "blacksmith or shop" -v
```

Never: `pytest tests/` (full suite) or an unscoped `pytest tests_v2/parity/`.

## Anti-Drift Test Guards

- **`OccupationChangeGoalScorer` suite unchanged**: `tests/unit/strategic/test_occupation_change_scorer.py`
  and `tests/integration/strategic/test_occupation_change_reachability.py` must pass byte-for-byte
  unchanged — catches accidental coupling from reusing the region-matching scan pattern.
- **`TOWN-017` crafting stays entity-agnostic unless deliberately changed**: a guard test asserting
  a *different* entity than the deceased can still craft at the blacksmith building post-death,
  unless Plan explicitly decided to gate `BlacksmithSystem` on the vacancy signal (in which case this
  guard should be replaced with the deliberate new behavior's own test, and
  `docs/parity_ledger/town_resource.yaml`'s `TOWN-017` entry updated in the same session).
- **`recent_world_events` window-bound guard**: a test confirming a vacancy event older than
  `WORLD_EVENT_WINDOW` (500 ticks) is no longer present in `state.recent_world_events` — prevents
  the implementation or its tests from silently assuming unbounded "remains detectable" persistence.
- **No `filled_by_entity_id` resolution logic guard**: a static/structural check (or simply the
  absence of any such field/branch in the diff, verified at code-review time) that no apprentice-
  promotion/import/auto-refill logic was added — this is the ticket's explicit Out of Scope, and the
  regression-prone direction is scope creep into "idea 64 done right" rather than "vacancy signal
  only."
- **PlaceState/idea 66 non-interference guard**: confirm the new code does not import from or
  depend on `PlaceState`/`PlaceKind` (not present in this branch per investigation.md) — a simple
  `grep -rn "PlaceState\|PlaceKind\|occupant_entity_id" src/<new files>` returning nothing is
  sufficient; no dedicated test needed, but call it out at Verify time.
