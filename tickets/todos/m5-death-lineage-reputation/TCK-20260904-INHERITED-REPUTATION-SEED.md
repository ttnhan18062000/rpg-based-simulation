---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-INHERITED-REPUTATION-SEED
phase: open
date: 2026-09-04
tags: [lifecycle, social]
---

# TCK-20260904-INHERITED-REPUTATION-SEED

## Title
Idea 53 — Inherited Reputation (birth-seed write)

## Status
OPEN

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
- birth_record() called with both parent_a_public_reputation and parent_b_public_reputation supplied yields a child SocialComponent.public_reputation strictly between the two parents' values (not the class default 1.0), verified by a new test.
- birth_record() called with zero or exactly one parent reputation value supplied falls back to the class default, verified by test.
- Natural-creature and magical-demonic (parentless) birth paths produce entities with the unmodified class-default public_reputation, verified by an anti-drift test matching the GENETICS-INHERITANCE precedent.
- Applying a heroism_delta or notoriety_delta via process_update() after a birth-seeded value moves the score identically to how it would from the class default (no special-cased floor or persistence tied to birth-seed origin), verified by test.
- The new write path never imports or calls ReputationUpdateService or PublicReputationProfile, verified by a source-text guard test.

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

## Test Summary

## Files Changed

## Completion Summary
