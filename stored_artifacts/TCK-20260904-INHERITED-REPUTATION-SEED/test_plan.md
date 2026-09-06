---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260904-INHERITED-REPUTATION-SEED
artifact_type: test_plan
tags: [lifecycle, social]
---

# Test Plan — TCK-20260904-INHERITED-REPUTATION-SEED

## Regression Surface

Unit:
- `tests/unit/progression/test_lifecycle.py` — `birth_record()` unit tests, especially
  `test_builder_birth_record_path_two_parent_case`, `test_builder_birth_record_path_parentless_case`,
  `test_builder_birth_record_seeds_child_social_bonds_toward_parents`,
  `test_parent_bond_updates_for_birth_apply_through_authoritative_path`,
  `test_no_marriage_precondition_in_birth_record_schema_or_apply_path`. Must stay green — the new
  kwargs are additive/optional and must not change any existing call's output.
- `tests/unit/progression/test_genetics.py` — must stay green unchanged; confirms the new
  reputation-combine work does not disturb `GeneticsSystem`.
- `tests/unit/social/test_relationships.py` — full file, especially
  `test_public_reputation_locality_differs_by_region_after_region_scoped_event`,
  `test_regional_reputation_delta_clamped_to_public_reputation_range`,
  `test_public_reputation_impact` (SOC-005's `test_path`) — confirms
  `RelationshipService.process_update()`'s existing `public_reputation`/`regional_reputation`
  write semantics are byte-for-byte unchanged by this ticket.
- `tests/unit/world/test_natural_creature_reproduction.py` — especially
  `test_natural_creature_and_magical_demonic_paths_never_attach_genetic_profile` (the anti-drift
  precedent) and `test_natural_creature_reproduction_does_not_reference_genetics` — must stay
  green; confirms parentless paths remain untouched.
- `tests/unit/world/test_reproduction_humanoid_cadence.py` — full file, especially
  `test_social_bond_seeded_between_each_parent_and_child_at_high_familiarity_sentiment`,
  `test_genetics_uses_real_parent_role_data_for_combat_lean`,
  `test_humanoid_reproduction_commits_through_authoritative_apply_path` — the real two-parent
  call chain this ticket's new kwargs will also flow through.
- `tests/unit/core/` — general `SocialComponent`/`V2EntityBuilder`/canonical-dict coverage.
- `tests/unit/domains/` — required per the confirmed structural coverage backstop (sibling ticket
  TCK-20260904-REPUTATION-LOCALITY-SCOPE): any ticket touching `src/core/` (this one touches
  `src/core/builder.py`) must include this directory in the Test phase's scoped pytest command,
  even though no specific domain subtest currently asserts on `SocialComponent` directly.

Architecture:
- `tests/architecture/test_social_write_paths.py` — both tests
  (`test_public_reputation_and_regional_reputation_write_paths_are_allowlisted`,
  `test_relationships_py_is_the_authoritative_writer`) must stay green. `builder.py` is already
  allowlisted for `public_reputation=` writes, so the new `.social(public_reputation=seed)` call
  inside `birth_record()` should not require editing this guard's `ALLOWED_FILES` — if it does
  turn out to require an edit, that is a signal the write landed somewhere unexpected and must be
  investigated, not silently allowlisted.

Integration:
- `tests/integration/optimization/test_component_patch_apply_parity.py` — includes
  `test_birth_record_writes_genetic_profile_via_authoritative_apply_path`; run to confirm no
  cross-talk with the new reputation-seed write.
- `tests/integration/scenarios/test_demographics.py` — references `spawn_humanoid_offspring`;
  confirm no behavior drift in aggregate demographic outcomes.

## New Tests Required

Per acceptance criteria:

1. **AC1 — both parents supplied yields a value strictly between them**
   - Test name: `test_birth_record_seeds_public_reputation_from_both_parents_average` (or
     equivalent, per Plan's chosen weighting formula)
   - Category: unit
   - Verifies: `birth_record(parent_a_public_reputation=X, parent_b_public_reputation=Y)` with
     `X != Y` produces `child.social.public_reputation` strictly between `min(X, Y)` and
     `max(X, Y)` (not equal to the class default `1.0` when `X`/`Y` are both `!= 1.0`).
   - Location: `tests/unit/progression/test_lifecycle.py` (mirrors
     `test_builder_birth_record_path_two_parent_case`'s placement).

2. **AC2 — zero or exactly one parent value supplied falls back to class default**
   - Test name: `test_birth_record_public_reputation_falls_back_to_default_with_partial_parent_data`
   - Category: unit
   - Verifies: three sub-cases (neither kwarg passed; only `parent_a_public_reputation` passed;
     only `parent_b_public_reputation` passed) all yield `child.social.public_reputation == 1.0`
     (the `SocialComponent` class default), confirming the "both required to trigger seeding"
     reading of AC2 over Scope's looser "whichever value(s) supplied" wording (see investigation's
     Risks section).
   - Location: `tests/unit/progression/test_lifecycle.py`.

3. **AC3 — parentless paths produce unmodified class-default reputation**
   - Test name: `test_natural_creature_and_magical_demonic_paths_never_seed_public_reputation`
   - Category: unit / anti-drift
   - Verifies: `EntityGenerator.spawn_natural_creature_offspring()` and
     `spawn_magical_demonic_entity()` both produce entities with `social.public_reputation == 1.0`
     (mirrors `test_natural_creature_and_magical_demonic_paths_never_attach_genetic_profile`
     exactly).
   - Location: `tests/unit/world/test_natural_creature_reproduction.py`.

4. **AC4 — post-birth deltas move a birth-seeded value identically to the class default**
   - Test name: `test_heroism_and_notoriety_deltas_apply_identically_to_birth_seeded_reputation`
   - Category: unit
   - Verifies: given a child built with a birth-seeded `public_reputation` (e.g. `0.6`), applying
     `RelationshipService.process_update(child.social, SocialUpdate(heroism_delta=0.2))` moves the
     value to `0.8` exactly as it would from any other starting value — no floor, ceiling, or
     persistence special-cased to the value's birth-seed origin. Also assert the same delta
     applied to a class-default (`1.0`) `SocialComponent` produces the expected `+0.2` result, to
     make the "identical mechanism" comparison explicit rather than implicit.
   - Location: `tests/unit/social/test_relationships.py` (co-locate with existing
     `process_update()` reputation tests).

5. **AC5 — new write path never imports/calls `ReputationUpdateService`/`PublicReputationProfile`**
   - Test name: `test_reputation_seed_write_path_does_not_reference_reputation_update_service`
   - Category: architecture guard (source-text)
   - Verifies: `inspect.getsource()` on `V2EntityBuilder.birth_record()` (and the new pure combine
     function, wherever the Plan phase locates it) contains neither `"ReputationUpdateService"`
     nor `"PublicReputationProfile"`, mirroring
     `test_natural_creature_reproduction_does_not_reference_genetics`'s
     `assert "Genetics" not in source` pattern.
   - Location: `tests/architecture/test_social_write_paths.py` (co-locate with the existing
     `public_reputation=`/`regional_reputation=` write-path guards) or a new file alongside it —
     Plan's call.

Additional recommended (not required by a literal AC, but closes the real-call-chain gap the
genetics ticket also closed):

6. **Real call-chain integration test**
   - Test name: `test_humanoid_reproduction_seeds_child_public_reputation_from_parents`
   - Category: integration / unit (matches the style of
     `test_social_bond_seeded_between_each_parent_and_child_at_high_familiarity_sentiment` in the
     same file)
   - Verifies: `HumanoidReproductionService.process_reproduction()`'s real call chain (through
     `EntityGenerator.spawn_humanoid_offspring()`) resolves `a.social.public_reputation` /
     `b.social.public_reputation` at the call site and produces a child with a seeded (non-default)
     `public_reputation` when the two parents' values differ — closing the same "unit test passes
     but the real caller never wires the kwarg" gap risk the genetics ticket's own AC1
     ("a real, live caller ... verifiable via a grep") was designed to catch.
   - Location: `tests/unit/world/test_reproduction_humanoid_cadence.py`.

7. **Determinism / canonical-hash regression check (no new test strictly required, but verify)**
   - Not a new test — `public_reputation` is already covered unconditionally by
     `StateFingerprinter.get_fingerprint()` (`src/replay/fingerprint.py:69`) and
     `EntityState.to_canonical_dict()`. Run the existing canonical-hash/fingerprint tests
     (`tests/unit/core/test_entity_integrity.py`) to confirm a birth-seeded value round-trips
     correctly with no special-case gap — flagged here so the Test phase does not skip this
     verification just because no new field was added.

## Scoped Pytest Commands

```
pytest tests/unit/progression/test_lifecycle.py tests/unit/progression/test_genetics.py \
  tests/unit/social/ \
  tests/unit/world/test_natural_creature_reproduction.py tests/unit/world/test_reproduction_humanoid_cadence.py \
  tests/unit/core/ \
  tests/unit/domains/ \
  tests/architecture/test_social_write_paths.py \
  tests/integration/optimization/test_component_patch_apply_parity.py \
  tests/integration/scenarios/test_demographics.py \
  -q
```

Never `pytest tests/`. If the Plan phase locates the new pure combine function inside
`src/systems/social_systems/relationships.py` rather than `builder.py`, add
`tests/unit/social/` explicitly (already included above) and re-run
`tests/architecture/test_social_write_paths.py` with particular attention to whether
`ALLOWED_FILES` needs a deliberate, disclosed edit (it should not, per this investigation's
finding that `builder.py` is already the correct construction-time write location).

## Anti-Drift Test Guards

- `tests/architecture/test_social_write_paths.py::test_public_reputation_and_regional_reputation_write_paths_are_allowlisted`
  — must continue passing with `builder.py`'s existing allowlist entry; a red flag if it starts
  failing (would mean the write landed in an unexpected file) or if `ALLOWED_FILES` had to be
  edited to accommodate it.
- New AC3 test (`test_natural_creature_and_magical_demonic_paths_never_seed_public_reputation`)
  — catches any accidental coupling of the new kwargs to `parent_a_entity_id`/`parent_b_entity_id`
  presence rather than the new kwargs' own presence (see investigation's Anti-Drift Hazards: the
  natural-creature/magical paths call `birth_record()` with `parent_a_entity_id=None,
  parent_b_entity_id=None` but never the new reputation kwargs).
- New AC5 source-text guard — catches any accidental import/call of
  `ReputationUpdateService`/`PublicReputationProfile`, guarding the explicit Out-of-Scope boundary
  against the two structurally-similar-but-unrelated reputation systems merging by accident.
- `tests/unit/social/test_relationships.py` full-file regression — catches any accidental change
  to `RelationshipService.process_update()`'s existing clamp/delta semantics, which this ticket
  must leave completely untouched (no new decay logic, no new fields on `SocialUpdate` itself per
  Scope).
- New AC2 test (`..._falls_back_to_default_with_partial_parent_data`) — catches silent
  implementation of Scope's looser "weighted average of whichever value(s) supplied" wording
  instead of AC2's stricter "both required" contract; this is the single highest-risk
  spec-ambiguity in this ticket (see investigation Risks) and deserves its own explicit guard
  rather than being folded into the AC1 test.
- `regional_reputation`-touching tests (`test_public_reputation_locality_differs_by_region_...`,
  `test_regional_reputation_delta_clamped_...`) in `tests/unit/social/test_relationships.py` —
  regression guard confirming this ticket did not (per the investigation's recommendation) also
  seed `regional_reputation`; if the Plan phase does decide to extend scope there, these tests'
  fixtures would need deliberate updates, not silent passage.
