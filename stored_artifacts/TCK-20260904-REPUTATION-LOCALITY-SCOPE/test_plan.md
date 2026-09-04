---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260904-REPUTATION-LOCALITY-SCOPE
artifact_type: test_plan
tags: [social, determinism]
---

# Test Plan — TCK-20260904-REPUTATION-LOCALITY-SCOPE

## Regression Surface

Existing tests that must keep passing (AC #4: "without breaking any existing test"):

**Unit — social:**
- `tests/unit/social/test_relationships.py` — `test_public_reputation_impact` (line 62-77) asserts
  `social.public_reputation == 1.5` after a heroism delta via `RelationshipService.process_update()`.
  Must still hold for whatever the retained/global read resolves to.
- `tests/unit/social/test_parity_soc_134.py` — `TestSocialAppraisalWithNarrative` (SOC-134, P0):
  `test_high_public_reputation_source_accepted` / `test_zero_public_reputation_source_rejected`
  (lines 29-60), builder-seeded `public_reputation=2.0`/`0.0`.
- `tests/unit/social/test_reputation_learning.py` — builder-seeded `public_reputation=1.8`/`0.4`
  (lines 17, 24).
- `tests/unit/social/test_social_memory.py` — extensive `public_reputation` export/import/decay
  coverage, lines 260-414 (`SocialMemoryExporter`/`Importer`/`Decay` round-trip assertions).
- `tests/unit/social/test_social_lifecycle.py` — `public_reputation` present in lifecycle fixtures.
- `tests/unit/social/test_social_bonds.py`, `tests/unit/social/test_social_memory_service.py` —
  adjacent `SocialComponent`/`place_attachment` coverage; must not regress from field-list changes.

**Unit — core / determinism:**
- `tests/unit/core/test_entity_integrity.py` —
  `test_social_seven_newly_covered_fields_participate_in_canonical_hash` (lines 270-306) and
  `test_social_nemesis_ids_participates_in_canonical_hash_end_to_end` (lines 308-331): confirms
  `place_attachment`'s canonical-hash coverage pattern this ticket's own new field must match; must
  not regress.
- `tests/unit/core/test_canonical_hash_status_effect.py`, `tests/unit/domains/progression/test_progression_decision_canonical_hash.py`
  — sibling canonical-hash-coverage tests in the same file family.
- `tests/unit/engine/test_hash_scheduler.py` — `CanonicalHashScheduler`/`HashMode` sanctioning logic
  (unaffected by field content, but exercises the same `CanonicalStateHasher.get_hash()` path).

**Integration:**
- `tests/integration/scenarios/test_macro_economy.py` — `test_reputation_discount_applies` (TOWN-181,
  P1): exact discount-percentage assertions at `public_reputation=1.6`/default `1.0` (lines 196-212).
- `tests/integration/scenarios/test_social_memory.py` — cross-episode carry-forward integration.
- `tests/integration/campaigns/test_progression_planner_three_episode.py`,
  `tests/unit/domains/campaigns/test_campaign_orchestrator.py`,
  `tests/unit/domains/campaigns/test_orchestrator_plan_wiring.py` — `EntityCarryForward.reputation`
  construction/read paths (`campaigns/orchestrator.py:479,654`, `campaigns/state.py:101-119`).
- `tests/integration/kernel/test_checkpoint_reproducibility.py` — full checkpoint round-trip;
  exercises `CanonicalStateHasher` end-to-end, must stay bit-identical for unchanged state.

**Observability (un-named consumers, at risk of silent staleness — see investigation Anti-Drift):**
- `tests/unit/observability/test_event_extractor_social_faction.py` — `reputation_delta` emission
  threshold (`REPUTATION_DELTA_THRESHOLD=0.05`) test, reads `public_reputation` diff between ticks.
- `tests/unit/observability/test_event_shapers_social.py` — matching shaper-side test.
- `tests/unit/observability/test_event_extractor_social_memory.py`,
  `test_event_extractor_contract_milestone.py`, `test_event_extractor_agency2.py`,
  `test_event_extractor_narrative.py` — adjacent social-domain observability coverage.

## New Tests Required

Per acceptance criteria:

1. **AC #1 — sole write path guard**
   - Test name: `test_public_reputation_locality_write_path_is_relationship_service_only` (or
     equivalent source-text guard, matching the project's existing "no second write path" guard-test
     idiom)
   - Category: architecture guard (source-text / AST scan, not a runtime test)
   - Verifies: no assignment to the new locality-scoped field (or to `public_reputation` itself)
     exists anywhere in `src/` outside `RelationshipService.process_update()` — must explicitly decide
     (per Plan) whether `SocialMemoryImporter.apply()`'s existing direct `dc_replace(...,
     public_reputation=...)` (`social_memory.py:522-526`) is an accepted exception or must be
     refactored to call `RelationshipService.process_update()` first; the guard's grep/AST pattern
     must reflect whichever Plan decides, not silently exempt it by omission.
   - Location: `tests/unit/social/test_relationships.py` or a new
     `tests/architecture/test_social_write_paths.py`, matching this repo's existing architecture-guard
     test placement convention (check `tests/architecture/` for precedent before creating a new file).

2. **AC #2 — region-scoped read differs by region**
   - Test name: `test_public_reputation_locality_differs_by_region_after_region_scoped_event`
   - Category: unit
   - Verifies: for the same entity, a locality-scoped read at region A and region B returns
     distinguishably different values after a reputation-affecting `SocialUpdate` is applied scoped to
     region A only (not region B) — i.e. the two reads are not both reading the same retained global
     scalar.
   - Location: `tests/unit/social/test_relationships.py` (mirrors `test_public_reputation_impact`,
     lines 62-77) or a new `tests/unit/social/test_reputation_locality.py`.

3. **AC #3 — canonical-hash coverage preserved**
   - Test name: `test_social_public_reputation_locality_participates_in_canonical_hash` (naming
     convention matches `test_social_nemesis_ids_participates_in_canonical_hash_end_to_end`)
   - Category: unit / determinism
   - Verifies: `EntityState.to_canonical_dict()`'s `"social"` sub-dict includes the new locality-scoped
     field (not just the retained scalar), and diverging it changes `to_canonical_dict()` output —
     following the exact pattern of
     `test_social_seven_newly_covered_fields_participate_in_canonical_hash`
     (`tests/unit/core/test_entity_integrity.py:270-306`). A second test should confirm
     `StateFingerprinter.get_fingerprint()`'s `state_hash` (`src/replay/fingerprint.py`) also changes
     when only the region-keyed value differs (not just the flat scalar), since that file's coverage
     is separate from `CanonicalStateHasher` and is explicitly named in the ticket's own Scope.
   - Location: `tests/unit/core/test_entity_integrity.py` (canonical-dict test, alongside the existing
     social-fields tests) and `tests/unit/replay/` or wherever existing `StateFingerprinter` tests
     live (check for an existing fingerprint test file before creating a new one).

4. **AC #4 — three named consumers keep working under the new shape**
   - Test name: extend/adapt existing tests rather than duplicate — `test_parity_soc_134.py`'s two
     tests, `test_macro_economy.py::test_reputation_discount_applies`, and `test_social_memory.py`'s
     export/import tests are the direct regression coverage; add one new test per consumer confirming
     the *region-scoped* value (not just the retained global default) is actually consulted, e.g.:
     - `test_appraise_contract_uses_region_scoped_reputation_when_present` — appraisal reads a
       region-specific entry that differs from the entity's global scalar, and the appraisal outcome
       reflects the region-specific value.
     - `test_reputation_discount_uses_region_scoped_value_at_shop_location` (only if Plan decides
       `shop.py`/`town/shop.py` need to resolve a region-specific value — see investigation Risk #2;
       otherwise this test is not needed and the existing `test_reputation_discount_applies` alone
       suffices).
     - `test_social_memory_export_import_carries_locality_data_or_documents_its_reduction` — confirms
       what happens to the new region-keyed data across the cross-episode boundary (aggregated?
       dropped to the retained scalar only? per Plan's decision).
   - Category: unit / integration (matches the existing tests they extend)
   - Location: same files as the existing tests they extend, to keep the regression and new coverage
     colocated.

5. **AC #5 — corrected premise recorded**
   - Not a code test — verified by done-checker's frontmatter/content review of the ticket's
     Investigation Notes section, not a pytest assertion. No new test file needed; this investigation
     already supplies the corrected-premise text for the ticket to carry forward.

## Scoped Pytest Commands

Primary scoped regression + new-test run (social domain + determinism, reusing
TCK-20260902-SOCIAL-CANONICAL-HASH-GAP's own scoped command as precedent):

```
pytest tests/unit/social/ tests/unit/core/test_entity_integrity.py tests/unit/engine/test_hash_scheduler.py tests/integration/kernel/test_checkpoint_reproducibility.py -m "not slow"
```

Economy discount + campaign carry-forward surface:

```
pytest tests/integration/scenarios/test_macro_economy.py tests/integration/scenarios/test_social_memory.py tests/unit/domains/campaigns/ tests/integration/campaigns/test_progression_planner_three_episode.py -m "not slow"
```

Observability delta-emission surface (un-named consumer, verify no silent staleness):

```
pytest tests/unit/observability/test_event_extractor_social_faction.py tests/unit/observability/test_event_shapers_social.py -m "not slow"
```

Never: `pytest tests/` (unscoped) — per project Testing Rule.

## Anti-Drift Test Guards

- **Global-scalar-untouched guard**: a test asserting that `apply_reputation_discount()`'s existing
  callers (`shop.py`/`town/shop.py`), `state_presenter.py`'s API field, and
  `EntityCarryForward.reputation` all still produce their pre-ticket values for an entity with no
  region-specific reputation data — i.e. the retained global scalar's default-fallback behavior is
  unchanged for entities that never trigger a region-scoped event. Catches silent scope creep into the
  5+ consumers not named in this ticket's Scope.
- **Composition-rule guard**: a test asserting `SocialUpdate.merge()`'s existing `reputation_set`
  (last-writer-wins) and `heroism_delta`/`notoriety_delta` (summed) semantics are unchanged after
  adding the new region-keyed delta field — catches an accidental change to the existing merge
  contract while adding new fields, mirroring how `place_attachment_delta`'s sum-by-key merge
  (`updates.py:339-341`) coexists with the pre-existing fields today.
- **SOC-005 test_path guard**: confirm the corrected `test_path` for SOC-005 (currently pointing at a
  nonexistent `tests_v2/parity/test_social_parity.py`) actually exists and passes after the parity
  ledger update — catches re-introducing a dangling P0 `test_path`.
- **`SocialMemoryImporter` write-path guard**: whichever way Plan resolves the pre-existing
  `dc_replace` bypass (see investigation Risk #3), add a regression test that fails if a *future*
  change reintroduces a second write path to `public_reputation`/the new locality field outside
  `RelationshipService.process_update()` — this is what makes AC #1's guard durable rather than a
  one-time check.
- **Determinism replay guard**: run `tests/integration/kernel/test_checkpoint_reproducibility.py`
  before and after the change with identical seeds/inputs and confirm hashes still match for state
  that does not touch the new field — catches an accidental non-determinism introduction (e.g.
  unsorted dict iteration) in the new canonical-hash/fingerprint code paths.
