---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-INHERITED-REPUTATION-SEED
phase: done
date: 2026-09-04
tags: [lifecycle, social]
---

# TCK-20260904-INHERITED-REPUTATION-SEED

## Title
Idea 53 — Inherited Reputation (birth-seed write)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Design idea 53 (Inherited Reputation, docs/brainstorm/rpg_feature_atlas.html) targets SocialComponent.public_reputation (src/core/models/social.py:51, a plain float 0.0-2.0) — confirmed by the real idea-53 card text: at birth, seed a small fraction of the newborn's public_reputation from the parents' averaged standing, "not a full inheritance, a starting echo that decays toward neutral as the child's own actions accumulate real reputation." Investigation (2026-09-04) confirmed RelationshipService.process_update() (src/systems/social_systems/relationships.py:16-100) genuinely has no passive decay term anywhere on public_reputation — it is written only via update.reputation_set (full overwrite) or explicit heroism_delta/notoriety_delta, clamped [0.0, 2.0] — so the epic doc's "no new decay logic needed at all" claim is verified true; a birth-seeded value is naturally swamped by the child's own subsequent deltas with no special handling required. The exact hook and structural precedent already exist: TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE (DONE) extended V2EntityBuilder.birth_record() (src/core/builder.py:624-675) with optional parent_a_genetic_profile/parent_b_genetic_profile kwargs, a pure GeneticsSystem.combine_profiles() function, and a write via LifecycleUpdate.genetic_profile_set — this ticket follows the identical shape, targeting SocialComponent via the already-existing V2EntityBuilder.social(public_reputation=...) kwarg (builder.py:498-538) and SocialUpdate.reputation_set (src/core/updates.py:299, already exists). This ticket depends on TCK-20260904-REPUTATION-LOCALITY-SCOPE (idea 60's child ticket) landing first, since idea 60 may change public_reputation's shape from a flat float to a region-keyed structure — this ticket's birth-seed write must target whatever shape idea 60 leaves the field in, not assume it stays a flat float.

## Scope
- Extend V2EntityBuilder.birth_record() (src/core/builder.py) with optional parent_a_public_reputation/parent_b_public_reputation kwargs, mirroring the exact structural precedent of TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE's parent_a_genetic_profile/parent_b_genetic_profile kwargs.
- Add a pure combine function (weighted average of whichever parent value(s) are supplied, clamped to the field's valid range) and write the result via V2EntityBuilder.social(public_reputation=seed) / SocialUpdate.reputation_set — both already exist, no new field needed on SocialUpdate itself.
- No new decay mechanism: SocialUpdate/RelationshipService.process_update() must gain zero new fields and zero new periodic/decay call sites — the birth-seeded value must be swamped by ordinary post-birth play identically to how the class default (1.0) would be.
- Restrict the reputation-seed write to human/humanoid two-parent births only; natural-creature/magical-demonic parentless spawn paths must be explicitly excluded, matching the existing genetics anti-drift test pattern from TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE.
- Account for whatever field shape TCK-20260904-REPUTATION-LOCALITY-SCOPE (idea 60) lands public_reputation in — if it becomes a region-keyed structure rather than a flat float, this ticket's birth-seed write must target that structure correctly, not a stale flat-float assumption.

## Out of Scope
- Any new BirthEvent class or reputation_decay_rate field — docs/brainstorm/rpg_expected_schemas.html's schema-53 section proposes both, but they contradict the epic's own verified no-decay-needed correction; do not build either.
- ReputationUpdateService/PublicReputationProfile (src/domains/commitment/reputation.py, src/core/cognition.py) — a structurally separate, unrelated reputation representation this ticket must not touch.
- Idea 60's own field-shape change or idea 54's ClanState.clan_reputation field — sibling/prerequisite child tickets of the same epic.

## Acceptance Criteria
- [x] birth_record() called with both parent_a_public_reputation and parent_b_public_reputation supplied yields a child SocialComponent.public_reputation strictly between the two parents' values (not the class default 1.0), verified by a new test.
- [x] birth_record() called with zero or exactly one parent reputation value supplied falls back to the class default, verified by test.
- [x] Natural-creature and magical-demonic (parentless) birth paths produce entities with the unmodified class-default public_reputation, verified by an anti-drift test matching the GENETICS-INHERITANCE precedent.
- [x] Applying a heroism_delta or notoriety_delta via process_update() after a birth-seeded value moves the score identically to how it would from the class default (no special-cased floor or persistence tied to birth-seed origin), verified by test.
- [x] The new write path never imports or calls ReputationUpdateService or PublicReputationProfile, verified by a source-text guard test.

## Related Tickets
- TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION
- TCK-20260904-REPUTATION-LOCALITY-SCOPE
- TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA
- TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE
- TCK-20260902-SOCIAL-CANONICAL-HASH-GAP
- TCK-20260619-E33D-REP-DISCOUNTS

## Related Docs
- docs/brainstorm/rpg_feature_atlas.html
- docs/brainstorm/rpg_expected_schemas.html
- docs/mechanics/01_entity_anatomy.md
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md

## Related Stored Artifacts
None

## Related Code Areas
- src/core/builder.py
- src/core/models/social.py
- src/core/updates.py
- src/systems/social_systems/relationships.py
- src/systems/lifecycle_systems/genetics.py
- src/replay/fingerprint.py

## Assumptions / Open Questions
- Exact weighting formula (simple average vs. weighted by some other factor) is a Plan-phase decision, not resolved by investigation.
- This ticket's Plan phase must re-check TCK-20260904-REPUTATION-LOCALITY-SCOPE's actual landed field shape before finalizing the write path, since that ticket must land first per the epic's sequencing constraint.

## Implementation Notes
Followed staging_artifacts/TCK-20260904-INHERITED-REPUTATION-SEED/plan.md exactly, step by step:

1. Added `ReputationService.combine_public_reputation(parent_a, parent_b) -> float` as a new pure
   `@staticmethod` on the existing `ReputationService` class in
   `src/systems/social_systems/reputation.py` — simple arithmetic mean, clamped `[0.0, 2.0]`.
2. Extended `V2EntityBuilder.birth_record()` (`src/core/builder.py`) with two new
   `Optional[float] = None` kwargs, `parent_a_public_reputation`/`parent_b_public_reputation`,
   placed after `parent_a_role`/`parent_b_role`. Added the AND-gated block (both values required)
   between the existing genetics-combine block and the bonds-seeding block, writing via the
   pre-existing `.social(public_reputation=...)` construction-time kwarg. Added the
   `ReputationService` import alongside the existing `GeneticsSystem` import.
3. Threaded `parent_a_public_reputation`/`parent_b_public_reputation` (both
   `Optional[float] = None`) through `EntityGenerator.spawn_humanoid_offspring()`
   (`src/systems/world_systems/generator.py`) into its `.birth_record(...)` call.
   `spawn_natural_creature_offspring()`/`spawn_magical_demonic_entity()` were left untouched, per
   the plan's explicit guard.
4. Wired the real parent values (`a.social.public_reputation`/`b.social.public_reputation`) as new
   keyword arguments at `HumanoidReproductionService.process_reproduction()`'s
   `generator.spawn_humanoid_offspring(...)` call site (`src/world/reproduction_humanoid.py`) — no
   fallback-resolution needed, since `SocialComponent.public_reputation` always holds a real value.
5. Added `test_natural_creature_and_magical_demonic_paths_never_seed_public_reputation` to
   `tests/unit/world/test_natural_creature_reproduction.py`, mirroring the existing
   `..._never_attach_genetic_profile` anti-drift test shape.
6. Added `test_heroism_and_notoriety_deltas_apply_identically_to_birth_seeded_reputation` to
   `tests/unit/social/test_relationships.py`, comparing a `public_reputation=0.6`-seeded
   `SocialComponent` against the class default under identical `heroism_delta`/`notoriety_delta`
   updates via `RelationshipService.process_update()` — proves zero new decay/floor logic.
7. Added `test_reputation_seed_write_path_does_not_reference_reputation_update_service` to
   `tests/architecture/test_social_write_paths.py`, using `inspect.getsource()` on
   `V2EntityBuilder.birth_record` and `ReputationService.combine_public_reputation` to assert
   neither references `ReputationUpdateService`/`PublicReputationProfile`. No edit was needed (or
   made) to `ALLOWED_FILES`/`_WRITE_PATTERN` in that file — the new kwargs' `parent_a_`/`parent_b_`
   prefixes never match the guard's word-boundary regex, exactly as the plan predicted.
8. Added the "Reputation Seed" subsection to `docs/mechanics/01_entity_anatomy.md` §5, immediately
   after "Genetic Inheritance (Combination)", following its exact shape (field type/location, the
   pure combine function, the AND-gate trigger contrasted with genetics' OR-gate, the
   construction-time write, the parentless-path exclusion). Added a new (originally `SOC-267`,
   renumbered to `SOC-271` during the PR merge — a cascade from PR #123's concurrent SOC-265
   collision) entry to
   `docs/parity_ledger/social_narrative.yaml` via `tools/parity_ledger_writer.py` (never
   hand-edited), `status: verified`, cross-referencing `SOC-217` and `SOC-193` (both correctly
   cited as P0 per the architecture review's correction to the investigation), with `test_path`
   citing the new AC1 test. Confirmed via `git diff` that only the one new `SOC-271` block was
   added, no existing entries altered. Ran `python3 tools/parity_index.py build` as the second,
   visible index-rebuild call per the parity-updater precedent.

Two dedicated tests were added for AC1 and AC2 per the task's explicit instruction (not folded into
one test): `test_birth_record_seeds_public_reputation_from_both_parents_average` (AC1, two-parent
seed) and `test_birth_record_public_reputation_falls_back_to_default_with_partial_parent_data`
(AC2, three sub-cases: neither/only-a/only-b) in `tests/unit/progression/test_lifecycle.py`. An
additional integration test,
`test_humanoid_reproduction_seeds_child_public_reputation_from_parents`, was added to
`tests/unit/world/test_reproduction_humanoid_cadence.py` exercising the real
`process_reproduction()` -> `spawn_humanoid_offspring()` -> `birth_record()` call chain, closing
the gap between the unit-level `birth_record()` tests and the one real production caller.

No deviations from the plan. `regional_reputation`, `ReputationUpdateService`,
`PublicReputationProfile`, `RelationshipService.process_update()`'s decay behavior, and
`SocialUpdate`'s field set were all left untouched, per the plan's Scope Guards.

Ran `make knowledge-index-update` (docs/ changed) and `graphify update .` (src/, tests/ changed);
both completed successfully with no code-graph topology changes flagged.

## Test Summary
Ran (via `/home/u24desktop/Working/venv/bin/python3 -m pytest`, since the worktree's own
interpreter lacks `pydantic`):
- `tests/unit/progression/test_lifecycle.py`
- `tests/unit/world/test_natural_creature_reproduction.py`
- `tests/unit/world/test_reproduction_humanoid_cadence.py`
- `tests/unit/social/test_relationships.py`
- `tests/architecture/test_social_write_paths.py`
- `tests/unit/progression/test_genetics.py`
- `tests/unit/domains/` (structural coverage backstop, since `src/core/builder.py` was touched)
- `tests/unit/core/test_entity_integrity.py` (determinism/canonical-hash verification pass)

All 983 tests passed (102 + 881), including all pre-existing tests in the touched files and all
newly added tests. No regressions.

## Files Changed
- src/systems/social_systems/reputation.py
- src/core/builder.py
- src/systems/world_systems/generator.py
- src/world/reproduction_humanoid.py
- tests/unit/world/test_natural_creature_reproduction.py
- tests/unit/social/test_relationships.py
- tests/architecture/test_social_write_paths.py
- tests/unit/progression/test_lifecycle.py
- tests/unit/world/test_reproduction_humanoid_cadence.py
- docs/mechanics/01_entity_anatomy.md
- docs/parity_ledger/social_narrative.yaml (via tools/parity_ledger_writer.py)
- tickets/inprogress/TCK-20260904-INHERITED-REPUTATION-SEED.md (this ticket, created during this run's Scope phase, updated here)
- staging_artifacts/TCK-20260904-INHERITED-REPUTATION-SEED/investigation.md (created during this run's Investigate phase)
- staging_artifacts/TCK-20260904-INHERITED-REPUTATION-SEED/plan.md (created during this run's Plan phase)
- staging_artifacts/TCK-20260904-INHERITED-REPUTATION-SEED/test_plan.md (created during this run's Plan phase)

## Completion Summary
Implemented idea 53's Inherited Reputation birth-seed: a new pure
`ReputationService.combine_public_reputation()` averages both parents' `public_reputation`
(clamped `[0.0, 2.0]`), wired through `V2EntityBuilder.birth_record()`'s new AND-gated
`parent_a_public_reputation`/`parent_b_public_reputation` kwargs (seeding only when both parents'
values are supplied, else falling back to the class default), threaded through
`EntityGenerator.spawn_humanoid_offspring()` and wired with real parent values at
`HumanoidReproductionService.process_reproduction()`'s call site. Parentless natural-creature and
magical-demonic spawn paths are unaffected. All five acceptance criteria are covered by dedicated
tests (two-parent seed, partial-parent fallback, parentless anti-drift, post-birth
heroism/notoriety-delta parity, and a source-text guard against the excluded
ReputationUpdateService/PublicReputationProfile system), plus one integration test on the real
production call chain. Docs updated: a new "Reputation Seed" Mechanics Bible subsection and a new
`SOC-271` parity ledger entry (status: verified, cross-referencing P0 entries SOC-217 and SOC-193).
