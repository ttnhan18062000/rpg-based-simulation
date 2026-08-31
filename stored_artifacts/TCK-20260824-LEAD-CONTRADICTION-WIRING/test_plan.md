---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260824-LEAD-CONTRADICTION-WIRING
artifact_type: test_plan
tags: [information, strategy, cognition]
---

# Test Plan — TCK-20260824-LEAD-CONTRADICTION-WIRING

## Regression Surface

Existing tests that must keep passing (grouped by domain — this ticket touches `pipeline.py`'s
`refine()` phase list, `lead_contradiction.py`, `contradiction.py`, `bridge.py`, and
`docs/parity_ledger/strategic_cognition.yaml`, so the surface spans strategy/cognition unit tests
plus the pipeline-level integration/parity suites):

**unit**
- `tests/unit/cognition/test_information_seeking.py` (full file — `TestLeadContradiction` class plus
  every other class in the file, since it also covers `PaidInformationTransactionSystem` and other
  E42-epic systems that share fixtures/imports with the class being extended)
- `tests/unit/domains/information/test_phase5_belief_contradiction.py`
- `tests/unit/domains/information/test_phase5_information_events.py`
- `tests/unit/domains/information/test_phase5_observation_belief_bridge.py`
- `tests/unit/strategic/test_belief_cycle.py` (adjacent `BeliefCycleSystem` — must show zero
  behavior change; this ticket must not touch it, but the pipeline reordering could theoretically
  perturb its inputs if inserted in the wrong place)
- `tests/unit/strategic/test_detour_suggestion.py` (STRAT-006/007/008/009 — exercises
  `LeadRoutingSystem`/`DetourSuggestionSystem`, which must remain unaffected by contradiction-testing
  changes to `_is_lead_contradicted()`)

**integration**
- `tests/integration/scenarios/test_phase5_information_belief_scenarios.py`
- Any existing full-tick / pipeline-level scenario test that exercises `AuthoritativeApplyPipeline.
  refine()` end-to-end with feature flags at default (must confirm the new `lead_contradiction`
  phase, gated `ENABLE_LEAD_CONTRADICTION`, does not change existing tick output when the flag is
  OFF/unset by default) — locate via `pytest --collect-only tests/integration -k pipeline` at
  implementation time and add the concrete path(s) found.

**parity / architecture guard**
- `tests/tools/test_parity_index.py` (validates `docs/parity_ledger/*.yaml` structure —
  STRAT-230's edit must not break duplicate-ID or schema checks; `TestRealLedgerCollisionGuard` in
  particular)
- `tests/architecture/test_phase18_import_boundaries.py` (imports `LeadRoutingSystem` per earlier
  grep — confirm no accidental new cross-domain import introduced by wiring
  `BeliefContradictionService` into `InformationBeliefPhase`/`bridge.py`)

## New Tests Required

1. **Full-pipeline contradiction parity test**
   - Name: `test_pipeline_refine_produces_lead_contradiction_matching_isolated_enforce`
   - Category: integration
   - Verifies: AC1 — building an `AuthoritativeState` with a non-EXHAUSTED `location`-kind lead
     pointing at a depleted `ResourceNodeState` (`remaining_charges=0`), calling
     `AuthoritativeApplyPipeline.refine(state, StateUpdate())` (with `ENABLE_LEAD_CONTRADICTION` ON,
     or ON-by-default if the implementer chooses that route) produces the same
     `belief_contradiction` / `lead_contradiction_resolved` `SimulationEvent`s and the same
     `StateUpdate.entity_updates[...].strategic` / `information_providers_update` mutations that
     calling `LeadContradictionSystem.enforce(state, StateUpdate())` directly produces on the
     identical input state. Assert event payloads and the resulting `LeadState`
     (`certainty=EXHAUSTED`, `test_outcome="FAILURE"`, `failure_count` incremented) are
     bit-identical between the two call paths.
   - Where: `tests/unit/cognition/test_information_seeking.py` (extend `TestLeadContradiction`) or a
     new `tests/integration/scenarios/test_lead_contradiction_pipeline.py` if a full
     `AuthoritativeState` fixture is too heavy for the unit file's existing helpers — implementer's
     call based on which existing fixture (`_make_state` in `test_phase5_belief_contradiction.py` vs.
     the unit test's own `_make_state`) is easier to extend to a full `refine()` call.

2. **`ENABLE_LEAD_CONTRADICTION` flag OFF/default regression test**
   - Name: `test_pipeline_refine_skips_lead_contradiction_when_flag_off`
   - Category: integration
   - Verifies: with the same depleted-lead fixture, calling `refine()` with the feature flag
     explicitly OFF produces no `belief_contradiction` event and does not mutate the lead — proves
     the phase is properly flag-gated and does not silently always-run in a way that breaks existing
     scenario baselines.
   - Where: same file as test 1.

3. **`BeliefContradictionService.detect()` real call-site test — `claim_failed_search`**
   - Name: `test_claim_failed_search_observation_triggers_belief_contradiction_via_production_path`
   - Category: integration
   - Verifies: AC2 — a `claim_failed_search` observation reaching the new production call site
     (whichever of `InformationBeliefPhase.apply()`'s new branch, or `ObservationBeliefBridge.
     process_observation()` given a real caller — per the implementation choice made for the open
     question in investigation.md §Risks item 1) results in `BeliefContradictionService.detect()`
     being invoked, and the resulting `BeliefContradictionResult(contradiction_detected=True, ...)`
     is applied as a `StrategicUpdate(leads_add_or_update=[...])` — not a direct mutation — visible
     in the returned `StateUpdate.entity_updates[actor.id].strategic`.
   - Where: `tests/unit/domains/information/test_phase5_belief_contradiction.py` (extend) or
     `tests/unit/domains/information/test_phase5_information_belief_phase.py` if the call site lands
     in `phase.py` directly — file may need to be created if it doesn't exist; check first.

4. **`BeliefContradictionService.detect()` real call-site test — `region_danger_seen`**
   - Name: `test_region_danger_seen_observation_triggers_belief_contradiction_via_production_path`
   - Category: unit
   - Verifies: AC2's second observation kind — a `region_danger_seen` observation against a
     `VAGUE`/`APPROXIMATE`-certainty lead whose `detail` matches the danger's `region_id` produces
     the same typed-update behavior as test 3. Also asserts the *negative* case: a `PRECISE`-certainty
     lead is not degraded (matches existing `contradiction.py:61` guard on
     `lead.certainty in (VAGUE, APPROXIMATE)`).
   - Where: same file as test 3.

5. **`_is_lead_contradicted()` — OBJECT lead coverage**
   - Name: `test_object_lead_contradicted_when_item_absent_from_world`
   - Category: unit
   - Verifies: AC3 for `LeadKind.OBJECT` — whatever world-state check the implementer adds (per
     investigation.md §3, likely against `state.ground_items`/`state.chests`) correctly returns
     `True` when the referenced object is absent and `False` when present. Include a companion
     `test_object_lead_not_contradicted_when_item_present` negative case.
   - Where: `tests/unit/cognition/test_information_seeking.py` (extend `TestLeadContradiction`, new
     helper `_make_object_lead`/reuse resource-node-style fixture pattern for ground items).

6. **`_is_lead_contradicted()` — EVENT lead coverage**
   - Name: `test_event_lead_contradicted_when_world_event_no_longer_active`
   - Category: unit
   - Verifies: AC3 for `LeadKind.EVENT` — per investigation.md §3's flagged open question, whatever
     state surface is chosen (`local_scars`/`recent_world_events`) correctly detects a
     no-longer-true event lead. Include the negative case (`test_event_lead_not_contradicted_when_
     event_still_active`).
   - Where: same file as test 5.

7. **`_is_lead_contradicted()` — CONCEPT lead coverage**
   - Name: `test_concept_lead_contradicted_on_failed_information_query` (if routed through
     `BeliefContradictionService`) or `test_concept_lead_contradicted_when_no_provider_knows_domain`
     (if routed through `_is_lead_contradicted()`'s state-scan shape) — **name depends on the design
     decision flagged in investigation.md §Risks item 2; write whichever variant matches the actual
     implementation, not both**.
   - Category: unit
   - Verifies: AC3 for `LeadKind.CONCEPT`.
   - Where: same file as test 5, or alongside tests 3/4 if routed through the observation path.

8. **`LeadKind` string-literal regression guard**
   - Name: `test_is_lead_contradicted_resource_literal_remains_dead_code` (or equivalent assertion)
   - Category: unit / architecture guard
   - Verifies: the pre-existing `"resource"` string-literal branch in `_is_lead_contradicted()`
     (confirmed dead — no production `LeadState` construction ever uses `kind="resource"`) is not
     silently relied upon by the OBJECT/EVENT/CONCEPT extension, and that `"location"`/`"person"`
     behavior is byte-for-byte unchanged after the extension (regression, not new behavior) — assert
     the existing `test_belief_contradiction_fires_on_depleted_lead` and any `person`-kind test still
     pass unmodified.
   - Where: `tests/unit/cognition/test_information_seeking.py`.

9. **STRAT-230 parity evidence test wiring**
   - Name: n/a — this is not a new test but a **pointer update**: AC4 requires STRAT-230's
     `test_path` be updated to include the new full-pipeline test from item 1 above, in addition to
     (not replacing) the existing isolated `.enforce()` test, since both remain valid regression
     coverage. Confirm `tests/tools/test_parity_index.py`'s duplicate/format checks still pass after
     the YAML edit (`git diff --stat docs/parity_ledger/strategic_cognition.yaml` should show only
     the STRAT-230 entry changed — see Anti-Drift Test Guards below).

## Scoped Pytest Commands

```bash
# Core regression + new tests for this ticket's domain
pytest tests/unit/cognition/test_information_seeking.py \
       tests/unit/domains/information/ \
       tests/unit/strategic/test_belief_cycle.py \
       tests/unit/strategic/test_detour_suggestion.py \
       -v

# Integration scenario coverage (adjust path once the real full-pipeline test file/location is confirmed)
pytest tests/integration/scenarios/test_phase5_information_belief_scenarios.py -v

# Parity ledger structural integrity after the STRAT-230 YAML edit
pytest tests/tools/test_parity_index.py -v

# Architecture import-boundary guard (cheap, catches accidental new cross-domain imports)
pytest tests/architecture/test_phase18_import_boundaries.py -v
```

Never `pytest tests/`. If a full-pipeline test is added under a new file path, add it explicitly to
the first command once its location is known.

## Anti-Drift Test Guards

- **Pipeline phase-count guard**: after adding the new `run_phase("lead_contradiction", ...)` call,
  any existing test that asserts a specific phase count or exact `metric_counters` key set for
  `refine()` (search for `metric_counters` assertions in pipeline-level tests before implementation)
  must be checked — a silently-added phase that isn't feature-flag-gated correctly could break a
  golden-count assertion elsewhere in the suite.
- **`BeliefCycleSystem` non-interference guard**: re-run `tests/unit/strategic/test_belief_cycle.py`
  and any `intelligence.py`-level test (`tests/unit/strategic/` broadly) to confirm the adjacent,
  already-wired `location`-kind hostile-proximity contradiction mechanism produces byte-identical
  output before/after this ticket — this is the single easiest thing to accidentally perturb, since
  both mechanisms operate on the same `LeadState`/`LeadCertainty` types and could interact if the new
  `lead_contradiction` phase is inserted before `strategic_intelligence` instead of after (see
  investigation.md's phase-insertion rationale — inserting in the wrong position doesn't crash
  anything but could cause the two systems' writes to interleave differently across runs).
- **`LeadRoutingSystem`/`DetourSuggestionSystem` non-interference guard**: `tests/unit/strategic/
  test_detour_suggestion.py` must show no change — routing/bandwidth-eviction logic
  (STRAT-006/007/008/009) is adjacent to but independent of contradiction-testing; OBJECT/EVENT/
  CONCEPT contradiction coverage must not change how those leads are routed or evicted.
- **`"resource"`/`"information"` dead-literal guard**: a test asserting that `kind="resource"` and
  `kind="information"` continue to behave exactly as today (dead/no-op respectively) after the
  OBJECT/EVENT/CONCEPT extension — prevents the implementer from accidentally "fixing" the
  `"resource"` branch into a live path that no production code exercises, which would be undocumented
  scope creep beyond AC3's explicit OBJECT/CONCEPT/EVENT list.
- **Flag-default guard**: if `ENABLE_LEAD_CONTRADICTION` is added, a test must assert the flag's
  *default* mode (ON, OFF, or SHADOW) explicitly, since every other Enhanced-RPG phase in this
  pipeline ships with an explicit, deliberate default (several default OFF pending rollout) — do not
  let this ship with an implicit/undocumented default that differs from the AC1 full-pipeline test's
  assumption.
- **Parity YAML full-diff guard**: after editing `docs/parity_ledger/strategic_cognition.yaml` for
  STRAT-230, run `git diff --stat docs/parity_ledger/strategic_cognition.yaml` and confirm only the
  STRAT-230 entry's lines changed — this file is 3800+ lines and a YAML round-trip via an automated
  parity-updater tool can silently reformat the entire file (known failure mode in this repo; see
  project memory on parity-updater full-file rewrite risk) rather than making a minimal targeted edit.
