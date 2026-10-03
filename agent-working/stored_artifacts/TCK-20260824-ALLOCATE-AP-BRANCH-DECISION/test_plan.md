---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260824-ALLOCATE-AP-BRANCH-DECISION
artifact_type: test_plan
tags: [progression]
---

# Test Plan — TCK-20260824-ALLOCATE-AP-BRANCH-DECISION

## Regression Surface

Existing tests that must keep passing regardless of which wire/dormant/consolidation path Plan
picks. Grouped by domain; all are unit-tier (no arena-combat or integration tests touch this
branch directly).

**`ALLOCATE_AP` action-router path (`core_actions.py` / `action_router.py`):**
- `tests/unit/quest/test_progression_regression.py::test_attribute_allocation_and_recalc` (module
  also has `test_evolution_trigger_and_stat_boost`, unrelated to AP but same file — run whole file)
  — the only direct test of `SimulationDomainLogic.execute_action` with an
  `{"action": "ALLOCATE_AP", ...}` payload.

**`AllocateAttributeAction` (`src/actions/attributes.py`):**
- `tests/unit/progression/test_attribute_growth.py` (all 5 tests: `test_hero_ap_grant_on_level_up`,
  `test_monster_no_ap_auto_scale`, `test_attribute_allocation_and_recalc`,
  `test_aptitude_multiplier_PROG_015`, `test_attribute_cap_PROG_046`) — exercises the dead-code
  aptitude-multiplier path directly. If Plan decides to delete/port this file, these tests are the
  direct casualty and must be explicitly repointed or removed as part of implementation, not left
  orphaned.

**`ConversionKind.ALLOCATE_AP` / `resolver.py` cosmetic path:**
- `tests/unit/domains/progression/test_phase6_conversion_intent_bridge.py::
  test_allocate_ap_conversion_maps_to_allocate_ap_intent` — currently asserts only
  `upd.identity.unspent_ap_delta == -1`, no attribute assertion. If Plan fixes the cosmetic branch to
  actually grant an attribute delta, this test's assertions must be updated in the same change (it
  would otherwise keep passing while under-specifying the fixed behavior — a silent regression-test
  gap).
- `tests/unit/domains/progression/test_phase6_conversion_intent_bridge.py::
  test_craft_conversion_maps_to_blacksmith_craft_intent` — sibling test in same file, unaffected but
  must stay green (regression guard that the file's other `ConversionKind` branches aren't touched).
- `tests/unit/domains/progression/test_phase6_progression_boundary.py`,
  `tests/unit/domains/progression/test_phase6_conversion_decision_service.py`,
  `tests/unit/domains/progression/test_phase6_progression_events.py` — sibling Phase 6 progression
  suite; must stay green as an anti-drift guard that `gaps.py`/`generator.py`/`selector.py` are
  untouched by this ticket.
- `tests/unit/engine/test_sort_tiebreaker.py` — uses `ConversionKind.ALLOCATE_AP` as a
  deterministic-sort-tiebreaker fixture value (alphabetically-lowest kind); must stay green as a
  guard that `ConversionKind`'s enum values/ordering are untouched.

**Feature-flag-gate regression (relevant if the flag/wiring decision touches
`ENABLE_PROGRESSION_EVOLUTION` at all — must NOT be flipped by this ticket per its own scope, but
must be verified untouched):**
- `tests/integration/test_scenario_feature_flag_defaults.py` — asserts real per-flag ON/OFF defaults
  against the `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist established by
  `TCK-20260824-ROLLOUT-FLAG-DECISIONS`.
- `tests/unit/config/test_phase10_feature_flags.py` — same allowlist, unit-tier.

**Observability / parity regression (SUB-376 / ENTITY-008's own evidence, must not regress):**
- `tests/unit/observability/test_event_extractor_attributes.py` (6 tests) — SUB-376's own
  `test_path`; verifies `attribute_changed` event emission from real `AttributeComponent` diffs,
  independent of which producer fires it.

## New Tests Required

Per AC, mapped to whichever branch Plan selects. Listed so Plan/Implement can pick the applicable
subset without re-deriving test shape from scratch.

- **Test name**: `test_allocate_ap_unreachable_via_real_kernel_tick` (or equivalent negative-proof
  name)
  **Category**: integration (real, non-mocked `Kernel.tick_once()`)
  **What it verifies**: if Plan's decision is **dormant**, a real corpus-profile `Kernel.tick_once()`
  loop (same style as SUB-376's own attempted-then-fallback verification) over N ticks produces zero
  `attribute_changed` events attributable to `execute_allocate_ap` or the `ConversionKind.
  ALLOCATE_AP` resolver branch — i.e., a positive regression guard that the documented dormancy claim
  in the new `intentional_divergences.md` entry is actually true today, not just asserted. This is
  the "prove the negative" counterpart to the ticket's own conditional AC ("If wire: a real ...
  `Kernel.tick_once()` run demonstrates a live path").
  **Where it should live**: `tests/integration/progression/test_allocate_ap_dormancy.py` (new file
  — no existing integration test targets this branch specifically).

- **Test name**: `test_allocate_ap_conversion_maps_to_allocate_ap_intent` (existing test, extended)
  **Category**: unit
  **What it verifies**: IF Plan fixes `resolver.py`'s cosmetic branch, this existing test must gain
  an assertion on `upd.attributes` (currently absent — see Regression Surface above) proving the
  fix actually grants an attribute delta, not just documenting the decrement.
  **Where it should live**: `tests/unit/domains/progression/test_phase6_conversion_intent_bridge.py`
  (extend in place, do not duplicate).

- **Test name**: `test_execute_allocate_ap_rejects_unknown_attribute_name` (or grants zero AP
  decrement)
  **Category**: unit, regression-prone-path
  **What it verifies**: this investigation found `execute_allocate_ap` silently decrements AP with
  zero attribute gain for any of the 7 non-strength/vitality attribute names (PROG-068 gate not
  honored on the live path). If Plan's disposition for `AllocateAttributeAction` is "port aptitude
  logic into `core_actions.py`," this test should assert the corrected behavior (either full 9-
  attribute coverage, or an explicit `INSUFFICIENT_AP`/`INVALID_ATTRIBUTE`-style failure reason
  instead of a silent no-op decrement). If Plan's disposition leaves `execute_allocate_ap`
  unmodified, this test should instead assert-and-document the current (buggy) behavior explicitly,
  so it stops being an undocumented silent gap.
  **Where it should live**: `tests/unit/quest/test_progression_regression.py` (co-locate with the
  existing `test_attribute_allocation_and_recalc`, same file already covers this call path).

- **Test name**: `test_allocate_attribute_action_disposition` (only if Plan keeps
  `AllocateAttributeAction` alive in some documented-but-unwired form rather than deleting it)
  **Category**: architecture guard
  **What it verifies**: `AllocateAttributeAction` continues to have zero callers in `src/` outside
  its own test file — i.e., prevents a future accidental second live caller from being added without
  a deliberate consolidation decision. Only needed if the file survives this ticket; not needed if
  Plan deletes it (in which case its own existing test file's deletion is the disposition proof).
  **Where it should live**: `tests/architecture/` (new or existing architecture-guard module, per
  repo convention) or `tests/unit/progression/test_attribute_growth.py` itself as a guard test
  alongside the existing 5.

- **Test name**: parity-ledger regression test for whichever `PROG-*` status correction Plan makes
  (e.g. `test_prog_068_prog_069_status_matches_live_path` or reuse of an existing parity-index
  baseline test pattern)
  **Category**: unit / parity
  **What it verifies**: if Plan corrects PROG-068/PROG-069's `verified` status per this
  investigation's finding, a real test (not just doc prose) backs the new `test_path` the parity
  schema requires for any P0 entry — required by the repo's own "P0 entries require a passing
  test_path" rule, and directly by SUB-376/ENTITY-008's own established pattern of always backing a
  parity claim with a real, cited test.
  **Where it should live**: co-locate with whichever unit test ends up covering the corrected
  live-path behavior (`test_progression_regression.py` or `test_attribute_growth.py`, depending on
  which implementation Plan keeps live).

## Scoped Pytest Commands

```bash
# Core regression surface for this ticket's affected files
pytest tests/unit/quest/test_progression_regression.py \
       tests/unit/progression/test_attribute_growth.py \
       tests/unit/domains/progression/ \
       tests/unit/engine/test_sort_tiebreaker.py \
       -v

# Feature-flag-gate regression guard (must stay green untouched by this ticket)
pytest tests/integration/test_scenario_feature_flag_defaults.py \
       tests/unit/config/test_phase10_feature_flags.py \
       -v

# Observability/parity regression guard (SUB-376's own test_path)
pytest tests/unit/observability/test_event_extractor_attributes.py -v

# If Plan adds the real-kernel dormancy-proof integration test
pytest tests/integration/progression/ -v -m "not slow"
```

Never `pytest tests/` — all scoped to the progression/action-router/feature-flag domains this
ticket actually touches.

## Anti-Drift Test Guards

- **`tests/unit/domains/progression/test_phase6_progression_boundary.py`,
  `test_phase6_conversion_decision_service.py`, `test_phase6_progression_events.py`** staying green
  is the guard that `gaps.py` (`GrowthGapEvaluator`), `generator.py`
  (`ConversionOptionGenerator`), and `selector.py` (`ConversionDecisionService`) — all listed in
  Related Code Areas but only as context, not as things this ticket should modify — are genuinely
  untouched. Any diff in this ticket that fails one of these three files has drifted beyond the
  `resolver.py` cosmetic-branch fix the ticket's own AC actually authorizes.
- **`tests/unit/engine/test_sort_tiebreaker.py`** staying green guards that `ConversionKind`'s enum
  member set/values are untouched — a name or value change to `ALLOCATE_AP` itself (as opposed to
  its resolver-branch behavior) would silently break this determinism test.
- **`tests/integration/test_scenario_feature_flag_defaults.py` /
  `tests/unit/config/test_phase10_feature_flags.py`** staying green with `ENABLE_PROGRESSION_
  EVOLUTION` still asserted `OFF` in `_DELIBERATE_ON_DEFAULT_FLAGS`-style checks is the guard that
  this ticket does not accidentally flip the flag — that decision belongs to the separate, already-
  filed `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION`, not this one (see investigation.md
  Anti-Drift Hazards).
- **`tests/unit/observability/test_event_extractor_attributes.py`** staying green guards that
  whichever implementation ends up live still produces `AttributeComponent` diffs the existing
  `attribute_changed` event extractor can observe unchanged — i.e., this ticket must not change the
  *shape* of `AttributeUpdate`/`AttributeComponent`, only which code path populates it and how.
  A failure here would mean the fix leaked into observability territory outside this ticket's scope.
- **`tests/unit/progression/test_attribute_growth.py`'s 5 tests, if `AllocateAttributeAction` is kept
  rather than deleted**, staying green (unmodified) guards that porting its aptitude logic elsewhere
  didn't also silently break/orphan the original correct implementation before the port is verified
  equivalent.
