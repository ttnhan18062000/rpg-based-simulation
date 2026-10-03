---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE
artifact_type: test_plan
tags: [adventure, agency, cognition, observability, schema]
---

# Test Plan — TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE

## Regression Surface

Existing tests that must keep passing (grouped by domain, all confirmed to exist by direct read this
session):

**Unit — strategic materialization / arbiter:**
- `tests/unit/strategic/test_adventure_route_materialization.py` (all 5 tests) — the direct-call
  tests against `evaluate_strategic_intent()`'s `ADVENTURE_ROUTE` branch that this ticket's new test
  extends. In particular `test_adventure_route_winner_materializes_with_raw_score_not_utility` and
  `test_form_party_materialized_objective_is_tactically_resolvable_not_a_stall` exercise the exact
  `switch_up` return path the fix touches — must keep asserting `project.score`/`project.kind`
  unchanged.
- `tests/unit/strategic/test_score_normalization.py` — covers STRAT-186/187 retention-margin/urgency
  comparisons inside `evaluate_project_switch()`, which this ticket must not touch or regress.
- `tests/unit/strategic/test_committed_intention_materialization.py` — the sibling feature sharing the
  exact same `if switch_up: extra_ci = {}; ...; return replace(switch_up, ..., **extra_ci)` code
  block this ticket also extends. Must keep passing to confirm the two features' extra-kwarg
  injections coexist without collision (disjoint `extra_ci` vs. new route-family kwargs, both merged
  into the same `replace()` call).
- `tests/unit/strategic/test_social_contract_materialization.py`,
  `tests/unit/strategic/test_region_stabilization_materialization.py` — the other two special
  `GoalKind` branches sharing the same dispatch chain (`intelligence.py:1466-1618`); must confirm this
  ticket's `ADVENTURE_ROUTE`-conditional addition does not leak into their branches.

**Unit — observability (read side, unchanged but must confirm still wired correctly):**
- `tests/unit/observability/test_event_shapers_strategy.py` — exercises `StrategyShaper.shape()`,
  the live-path reader of `last_routing_family`/`last_defer_reason`.
- `tests/unit/observability/test_event_extractor_agency2.py` — exercises the rollback-path reader,
  and (`TestAntiDriftGuards::test_defer_property_name_constant_matches_phase_and_extractor`) pins the
  `last_defer_reason` key-name contract, which this ticket must not touch.

**Unit — architecture / deletion guards:**
- `tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py` (all 4 tests) — must
  stay green; the `adventure_contract.md` guard only scopes the "## Engine Phase" section, disjoint
  from this ticket's planned "What It Owns"/"What It May Mutate" edits.
- `tests/unit/domains/adventure/test_eligibility_cognition_profile.py` — behavioral coverage for the
  relocated eligibility helpers; unaffected by this ticket but confirms no accidental regression to
  `_supports_adventure_routing`/`_resolve_cognition_profile_id`.

**Unit — core update-intent schema:**
- No dedicated `StrategicUpdate.merge()`/`is_noop()` unit-test file currently exists (confirmed by
  repo-wide search); this ticket's new tests (below) are the first direct coverage of these methods
  for the new field, per `update_intents.md`'s Extension Rule #10.

**Simulation-quality / calibration:**
- `tests/simulation_quality/test_agency_scorer.py` — must stay green unmodified; bypasses the
  emission wiring entirely via synthetic envelopes.
- `tests/simulation_quality/test_grade_regression.py` — the 6 named run_keys
  (`simq_routing_test`/`hero_guild_routing` × seeds 42/123/456, `_500t`) currently fail on AGENCY
  band-crossing (anchor `C`, live `A` once the fix lands) — this ticket's `grade_anchors.json`
  recalibration (AC4) must flip these back to passing without touching COGNITION on the seed123 pair
  (unrelated, already-correct `C` from the parent ticket).

## New Tests Required

1. **Test name:** `test_strategic_update_last_routing_family_set_is_noop_default`
   **Category:** unit
   **What it verifies:** a default-constructed `StrategicUpdate()` has `last_routing_family_set`/
   `last_routing_tick_set` both `None`, and `is_noop()` still returns `True` — required by
   `update_intents.md` Extension Rule #10 ("`is_noop()` on a default-constructed instance").
   **Where it should live:** new file `tests/unit/core/test_strategic_update_routing_family.py` (no
   existing `StrategicUpdate`-focused unit test file was found to extend).

2. **Test name:** `test_strategic_update_merge_last_routing_family_last_write_wins`
   **Category:** unit
   **What it verifies:** `StrategicUpdate.merge()` follows the "set last-write-wins" rule for the new
   fields (matching `current_project_id_set`'s documented behavior): merging `A(family=None)` then
   `B(family="take_easy_quest", tick=50)` yields `family="take_easy_quest", tick=50`; merging
   `A(family="recover", tick=10)` then `B(family=None, tick=None)` (a no-op update) leaves `A`'s
   values unchanged (the `other.field if other.field is not None else self.field` pattern every other
   scalar-set field in this dataclass already follows).
   **Where it should live:** same new file as Test 1.

3. **Test name:** `test_adventure_route_win_thread_family_into_strategic_update`
   **Category:** unit
   **What it verifies:** a winning `ADVENTURE_ROUTE` candidate's materialization
   (`evaluate_strategic_intent()`, called directly as the existing sibling tests in
   `test_adventure_route_materialization.py` already do) produces a `StrategicUpdate` whose
   `last_routing_family_set == "take_easy_quest"` (the **string** `.value`, not the raw `RouteFamily`
   enum — this exact assertion catches the `.value`-discipline risk flagged in investigation.md) and
   `last_routing_tick_set == <the tick passed in>`. Mirrors
   `test_adventure_route_winner_materializes_with_raw_score_not_utility`'s existing fixture shape
   (`_eligible`, `_fake_decide_factory`) exactly, adding only the new field assertions.
   **Where it should live:** `tests/unit/strategic/test_adventure_route_materialization.py` (extend
   the existing file, matching its established shape — this is the concrete realization of the
   originating ticket's illustrative "New Test 3").

4. **Test name:** `test_adventure_route_defer_family_does_not_set_routing_family`
   **Category:** unit
   **What it verifies:** negative case — a `DEFER_WITH_REASON`-classified `best_candidate` (which
   never reaches the `switch_up`-returning path; see
   `test_adventure_route_winner_preserves_none_none_handling_for_defer_family`'s existing fixture)
   must NOT set `last_routing_family_set`. Confirms the fix is scoped to the winning-route case only,
   matching the pre-deletion phase's own behavior (`last_routing_family` was written only in the
   winning branch; `last_defer_reason` — untouched by this ticket — was the separate DEFER-only
   write).
   **Where it should live:** `tests/unit/strategic/test_adventure_route_materialization.py`.

5. **Test name:** `test_adventure_route_win_that_loses_project_switch_does_not_set_routing_family`
   **Category:** unit
   **What it verifies:** a winning `best_candidate` whose `evaluate_project_switch()` call returns
   `None` (candidate rejected — locked current project, insufficient urgency margin) must not set
   `last_routing_family_set` anywhere, reproducing the pre-deletion phase's own `if strat_upd is None:
   continue` semantics exactly (see investigation.md's "Current Behavior" section). Construct via a
   monkeypatched `evaluate_project_switch` returning `None`, or a real locked-project fixture matching
   `test_score_normalization.py`'s existing lock-scenario pattern.
   **Where it should live:** `tests/unit/strategic/test_adventure_route_materialization.py` or
   `tests/unit/strategic/test_score_normalization.py`, whichever Implement judges fits the existing
   fixture conventions better.

6. **Test name:** `test_adventure_route_win_property_updates_carries_last_routing_family`
   **Category:** integration
   **What it verifies:** AC2's literal requirement — exercising the **outer** refine-loop merge site
   (`StrategicIntelligenceSystem.evaluate_all_strategic_intents()`, `intelligence.py:895-929`, which
   currently has zero test coverage per investigation.md Risk #5), asserting that the resulting
   `StateUpdate.entity_updates[hero.id].property_updates["last_routing_family"]` equals the expected
   string and `["last_routing_tick"]` equals the tick, for a winning `ADVENTURE_ROUTE` candidate. This
   is the test that most directly proves `route_selected`/`action_executed`/`route_family_first_use`
   can fire again — it exercises the exact dict key names `event_shapers.py:751`/`event_extractor.py:595`
   read (`"last_routing_family"`), not just the `StrategicUpdate`-internal field name.
   **Where it should live:** new file `tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py`,
   or fold into `test_adventure_route_materialization.py` under a clearly-separated section if
   Implement judges the existing file's `_state`/`_entity` helpers are directly reusable at this
   outer-loop level (they likely need a `StateUpdate` wrapper and a `GovernorPolicy`/cadence stub not
   currently present in that file's fixtures — check before assuming reuse).

7. **Test name:** `test_agency_events_fire_end_to_end_for_winning_adventure_route`
   **Category:** integration
   **What it verifies:** feeds the `StateUpdate` produced by Test 6's scenario through
   `StrategyShaper.shape()` (live path) and asserts `route_selected`, `action_executed`, and
   `route_family_first_use` `SimulationEvent`s are actually emitted with the correct `family` payload
   — this is the end-to-end proof AC3 requires beyond the unit-level field assertions, closing the
   gap between "the field is set" and "the observability events actually fire."
   **Where it should live:** `tests/unit/observability/test_event_shapers_strategy.py` (extend,
   matching its existing fixture shape for constructing a `StateUpdate` with a routing-carrying
   `EntityUpdate`).

## Scoped Pytest Commands

```
# Core schema unit tests (new)
pytest tests/unit/core/test_strategic_update_routing_family.py -v

# Adventure-route materialization (existing + extended)
pytest tests/unit/strategic/test_adventure_route_materialization.py -v

# Sibling special-branch regression check (must not regress from the shared switch_up-site edit)
pytest tests/unit/strategic/test_score_normalization.py tests/unit/strategic/test_committed_intention_materialization.py tests/unit/strategic/test_social_contract_materialization.py tests/unit/strategic/test_region_stabilization_materialization.py -v

# Outer refine-loop integration test (new)
pytest tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py -v

# Observability read-side regression + new end-to-end event test
pytest tests/unit/observability/test_event_shapers_strategy.py tests/unit/observability/test_event_extractor_agency2.py -v

# Deletion-ticket architecture guards (must stay green, disjoint doc section)
pytest tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py -v

# AgencyScorer unit coverage (must stay green unmodified, bypasses emission wiring)
pytest tests/simulation_quality/test_agency_scorer.py -v -m "not slow"

# Grade regression, scoped to exactly the 6 named run_keys (AGENCY only expected to flip; COGNITION
# on the seed123 pair must remain unchanged from the parent ticket's C/0.0)
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "simq_routing_test_seed42_500t or simq_routing_test_seed123_500t or simq_routing_test_seed456_500t or hero_guild_routing_seed42_500t or hero_guild_routing_seed123_500t or hero_guild_routing_seed456_500t"
```

Never `pytest tests/` repo-wide (CLAUDE.md Testing Rule). A full `-m "not slow"` sweep of
`test_grade_regression.py` (all ~89 `FAST_ANCHOR_KEYS`) before/after, `git stash`-compared, is
recommended as a final cross-contamination check (matching the parent ticket's own precedent), not as
a routine per-step command.

## Anti-Drift Test Guards

- **`test_adventure_route_win_that_loses_project_switch_does_not_set_routing_family` (New Test 5) is
  the guard against over-broadening the fix** — it would catch an implementation that sets
  `last_routing_family_set` unconditionally inside the `ADVENTURE_ROUTE` branch (e.g., before the
  `switch_up`/`if switch_up:` check) rather than gated on actual acceptance by
  `evaluate_project_switch()`, which would diverge from the pre-deletion phase's own semantics.
- **`test_adventure_route_win_thread_family_into_strategic_update`'s string-vs-enum assertion (New
  Test 3) is the guard against the `.value` discipline risk** flagged in investigation.md — asserting
  `last_routing_family_set == "take_easy_quest"` (a bare string) rather than
  `== RouteFamily.TAKE_EASY_QUEST` would still pass if Implement forgets `.value()`, since
  `RouteFamily` is a `str` subclass and equality holds either way; the test must additionally assert
  `type(result.last_routing_family_set) is str` (not `isinstance`, which would also pass for the enum
  since it subclasses `str`) to actually catch a missed `.value` call.
- **`tests/unit/strategic/test_score_normalization.py` full pass is the guard against any accidental
  change to `evaluate_project_switch()`'s own body** — this ticket's Out of Scope forbids touching it;
  a source-hash guard test (matching `TCK-20260812-COMMITTED-INTENTION-SEQUENCE`'s own
  `test_evaluate_project_switch_source_hash_unchanged` precedent,
  `tests/architecture/test_committed_intention_arbiter_byte_identical_guard.py`) already exists and
  covers this — Implement should confirm that guard still passes rather than adding a duplicate.
- **`tests/unit/strategic/test_committed_intention_materialization.py` full pass is the guard against
  the two features' `extra_ci`/new-route-kwargs colliding** inside the shared
  `return replace(switch_up, ..., **extra_ci)` call — both features write into the same `**kwargs`
  expansion; a naming collision or an accidental overwrite of one feature's kwarg by the other would
  surface here first.
- **`test_agency_scorer.py` staying green throughout is expected, not a completeness signal** — do
  not treat a green run of this file as evidence the fix works; it bypasses the emission wiring
  entirely by construction (documented already in the parent ticket's Anti-Drift Notes, re-stated
  here since it applies equally to this ticket).
- **Do not extend `SCORE_TOLERANCE_OVERRIDES` (`test_grade_regression.py:90-96`) for any of the 6
  named run_keys** — a `grade_anchors.json` point-edit restoring the original `A`-grade values
  (re-verified fresh via `calibrate_simq.py`, not copied from the pre-drift snapshot in
  investigation.md/plan.md, per the parent ticket's own Step-1 fresh-reverification precedent) is the
  correct shape, mirroring how the parent ticket recalibrated these same anchors down.
- **`docs/parity_ledger/infrastructure.yaml` YAML-parses cleanly** after the INFRA-237 addendum edit:
  `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`.
