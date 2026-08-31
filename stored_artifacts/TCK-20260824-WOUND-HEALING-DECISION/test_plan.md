---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260824-WOUND-HEALING-DECISION
artifact_type: test_plan
tags: [combat]
---

# Test Plan — TCK-20260824-WOUND-HEALING-DECISION

This is a documentation/dead-code-disposition ticket (Option (b) already decided). There is no new
healing logic to implement or test. The test surface is entirely about (1) confirming the
regression suite still passes after `heal_wound()`/`get_diagnosis_quality()` are removed or
annotated, and (2) locking in evidence that zero production producers exist, so a future accidental
re-introduction of an untracked healing trigger is caught.

## Regression Surface

Existing tests that must keep passing, grouped by domain. None of these test bodies should need
behavior changes — only `TestScarPermanence`'s three tests and `test_effective_stats_with_scars`
may need updating if `heal_wound()` is deleted rather than annotated (see New Tests Required).

**Unit — `src/engine/rpg_depth.py` (WoundService/MedicalService/SkillScalingService):**
- `tests/unit/core/test_rpg_depth.py` — full file, including:
  - `TestWoundInfliction` (unaffected — owned by the separate `WOUND-THRESHOLD-DECISION` ticket, do
    not touch)
  - `TestScarPermanence` (`test_scar_permanence`, `test_scar_lesser_penalty`,
    `test_scar_cumulative_penalties`, lines 234-258) — directly calls `heal_wound()`
  - `TestSkillScaling::test_effective_stats_with_scars` (line 475-489) — calls `heal_wound()` to
    build a scar fixture
  - `TestSkillScaling::test_wound_heal_through_apply` (line 590-603) — tests the apply-path
    consumer, does **not** call `heal_wound()`, must stay green untouched

**Unit — `src/core/updates.py` (WoundUpdate merge/is_noop):**
- `tests/unit/domains/optimization/test_component_patches.py` — `WoundPatch`/`WoundUpdate` coverage
- `tests/integration/optimization/test_component_patch_apply_parity.py`
- `tests/integration/optimization/test_apply_plan_parity.py` (line 38: `WoundUpdate(wounds_add=[],
  scars_add=[])` construction in a parity fixture)

**Unit/Integration — `src/engine/combat.py` (wound infliction production path):**
- `tests/unit/combat/test_direct_combat_outcomes.py` (includes the two `WOUND-PENALTY-FORMULA-WIRING`
  severity-scaling tests — must not regress)
- `tests/unit/combat/test_combat_matrix.py`
- `tests/unit/combat/test_parity_comb_006.py`
- `tests/integration/combat/test_relation_combat_integration.py`
- `tests/integration/pipeline/test_combat_legality_matrix.py`
- `tests/integration/pipeline/test_combat_trust.py`

**Unit — `src/engine/patches.py` (WoundPatch.apply):**
- Covered by the `test_component_patches.py` / `test_component_patch_apply_parity.py` files listed
  above (no dedicated `patches.py`-only test file exists in this repo).

**Unit — `src/observability/event_extractor.py` (wound_sustained/wound_healed/scar_gained):**
- `tests/unit/observability/test_event_extractor_vitals.py` — `test_wound_sustained_severity_mapping`,
  `test_wound_healed_fires`, `test_scar_gained_fires` (all three must keep passing unchanged — this
  ticket does not touch the event-extractor consumer logic, only the doc/ledger text describing its
  reachability)
- `tests/unit/observability/test_event_extractor_attributes.py` (references the same
  wound_sustained/wound_healed/scar_gained fallback pattern in a comment; sanity-check it still
  imports cleanly if anything in `rpg_depth.py` changes)

## New Tests Required

Per the ticket's acceptance criteria, this ticket does not add new *behavioral* tests (no new
healing trigger exists to test). The required additions are regression/documentation-of-decision
tests confirming dead code stays dead and the parity/event-ledger corrections are accurate.

- **Test name**: `test_heal_wound_has_no_production_callers` (or equivalent grep/AST-based guard)
  - **Category**: architecture guard
  - **What it verifies**: no file under `src/` (excluding `src/engine/rpg_depth.py` itself)
    references `heal_wound(` — i.e. locks in the zero-caller finding from this investigation so a
    future change cannot silently add a producer without a corresponding doc/ticket update. Only
    required if the Implement phase chooses "annotate dead-by-design" over "delete" — if
    `heal_wound()` is deleted outright, this guard is moot (the symbol no longer exists to be
    called) and should be skipped in favor of a simple "no leftover references" grep-based check
    instead.
  - **Where it should live**: `tests/unit/core/test_rpg_depth.py` (co-located with the other
    `WoundService`/`MedicalService` tests) or `tests/architecture/` if this repo has an existing
    architecture-guard directory for similar checks — check for precedent before creating a new
    location.

- **Test name**: `test_wound_healed_and_scar_gained_have_zero_production_producers` (integration,
  non-mocked)
  - **Category**: integration
  - **What it verifies**: runs a real, non-mocked `Kernel.tick_once()` (or the closest existing
    real-tick harness used elsewhere for gated-off mechanics, e.g. the pattern cited by COMB-296's
    own `v2_evidence`: `test_information_intent_execution_fires_through_kernel_tick_once`) across
    enough ticks to produce at least one `wound_sustained` event (with `ENABLE_COMBAT_ENGAGEMENT` on
    for the test only), and asserts **zero** `wound_healed` or `scar_gained` events are ever
    produced, even though wounds are sustained. This is the concrete evidence needed to correct
    COMB-296/ENTITY-018 accurately (AC #4) rather than asserting it from static analysis alone.
  - **Where it should live**: `tests/integration/combat/` (new file or added to
    `test_relation_combat_integration.py` if its existing fixture already spins up a real Kernel
    loop with combat enabled).

- **If `heal_wound()`/`get_diagnosis_quality()` are deleted (not just annotated)**: update, not
  delete outright, `TestScarPermanence`'s three tests and `test_effective_stats_with_scars` in
  `tests/unit/core/test_rpg_depth.py` to construct `ScarState` by hand instead of via
  `WoundService.heal_wound()` — this preserves the scar-penalty-math coverage
  (`get_scar_stat_penalties`, `get_effective_stats` with scars) that has nothing to do with the
  healing-trigger decision and must not be lost as collateral damage.
  - **Category**: unit (test maintenance, not new coverage)
  - **Where it should live**: `tests/unit/core/test_rpg_depth.py` (same location, same test names,
    updated fixture construction)

## Scoped Pytest Commands

```
pytest tests/unit/core/test_rpg_depth.py -v
pytest tests/unit/domains/optimization/test_component_patches.py tests/integration/optimization/test_component_patch_apply_parity.py tests/integration/optimization/test_apply_plan_parity.py -v
pytest tests/unit/combat/ tests/integration/combat/ -v -m "not slow"
pytest tests/unit/observability/test_event_extractor_vitals.py tests/unit/observability/test_event_extractor_attributes.py -v
pytest tests/integration/pipeline/test_combat_legality_matrix.py tests/integration/pipeline/test_combat_trust.py -v
```

Never `pytest tests/` — scoped to the five Related Code Areas' domains (rpg_depth/updates/combat/
patches/event_extractor) and their direct test counterparts, per the Testing Rule.

## Anti-Drift Test Guards

- **`TestWoundInfliction` in `tests/unit/core/test_rpg_depth.py` must be unaffected** — it belongs to
  the separate `TCK-20260824-WOUND-THRESHOLD-DECISION` ticket's `should_inflict_wound()` scope. A
  passing run of this class after this ticket's changes is evidence no drift into that ticket's
  territory occurred.
- **`test_wound_heal_through_apply` must keep passing unmodified** — it is the apply-path consumer
  test for `WoundUpdate.wounds_heal`/`WoundPatch.apply`, which this ticket explicitly does not
  remove (only the dead *producer*, `heal_wound()`, is in scope). If this test starts failing or
  needs modification, that is a signal the change accidentally touched consumer plumbing, not just
  the dead producer — stop and re-scope.
- **The two `WOUND-PENALTY-FORMULA-WIRING` severity-scaling tests in
  `test_direct_combat_outcomes.py`** (`test_wound_penalties_scale_with_severity_through_live_combat_path`,
  `test_severe_wound_max_hp_penalty_reduces_effective_max_hp_through_apply_path`) must keep passing
  unchanged — they cover the already-shipped penalty formula wiring, a different ticket's completed
  work that this ticket must not regress.
- **`LocalScarState`-related tests (`tests/unit/world/test_consequences.py`) must not be touched or
  referenced** — confirms no accidental conflation between entity `ScarState` (this ticket's
  concern) and the unrelated world/regional `LocalScarState` subsystem (see investigation.md's
  Finding 6 note).
- **A new/updated test must prove `wound_sustained` still fires while `wound_healed`/`scar_gained`
  do not**, in the same real-tick run — this distinguishes "gate-limited but real" (wound_sustained)
  from "zero producers regardless of gate" (wound_healed/scar_gained), which is the precise
  distinction this ticket's doc/ledger corrections depend on. A test that only proves
  wound_healed/scar_gained absence without also proving wound_sustained presence would not
  distinguish "combat is off" from "no producer exists," which is the exact ambiguity this ticket
  exists to resolve.
