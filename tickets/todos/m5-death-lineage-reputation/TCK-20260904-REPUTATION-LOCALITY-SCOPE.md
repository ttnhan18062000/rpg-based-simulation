---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-REPUTATION-LOCALITY-SCOPE
phase: open
date: 2026-09-04
tags: [social, determinism]
---

# TCK-20260904-REPUTATION-LOCALITY-SCOPE

## Title
Idea 60 — Reputations Are Local (region-scoped public_reputation)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Design idea 60 (Reputations Are Local, docs/brainstorm/rpg_feature_atlas.html) targets SocialComponent.public_reputation (src/core/models/social.py:51) — a single unscoped float with no location, observer, or region parameter anywhere in its read or write paths (idea 60's own card, citing src/systems/social_systems/relationships.py:92-93). The M5 epic doc's premise that a "competing reputation system" risk was downgraded because "PublicReputationProfile's only mutator has zero call sites anywhere" is CONFIRMED STALE as of 2026-09-04: TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING (DONE, landed 2026-08-28) wired ReputationUpdateService.process_witnessed_event() to a real call site in QuestResolutionSystem.enforce() (src/engine/quests.py:233), for the "successful_escort" event kind only. However, fresh investigation (2026-09-04) confirms this correction does NOT change idea 60's actual scope: PublicReputationProfile (src/core/cognition.py, a per-label dict on RelationshipModel) is structurally distinct from SocialComponent.public_reputation (a plain float) — idea 60's own card and the 2026-09-02 social/relationship-axis proposal (§3.5) both confirm idea 60 targets the latter exclusively and never proposed building on or merging with PublicReputationProfile. This ticket's Investigate phase should record the corrected premise as fresh evidence, not repeat the epic doc's stale claim, while scoping strictly to SocialComponent.public_reputation. Idea 60 is sequenced first within the reputation branch because ideas 53 and 54 (sibling child tickets of the same epic) both write to this same field and must account for whatever shape this ticket leaves it in.

## Scope
- Add region/observer-local scoping to SocialComponent.public_reputation's read and write paths, reusing the shape precedent of the existing SocialComponent.place_attachment field (Dict[RegionID, float], src/core/models/social.py:47, already maintained per-tick by SocialMemoryService) rather than inventing a new locality representation from scratch — exact granularity (per-region vs per-observer vs per-settlement) is a Plan-phase decision.
- Keep RelationshipService.process_update() (src/systems/social_systems/relationships.py) as the sole authoritative write path for the new locality-scoped structure — no second write path introduced.
- Update the three known live consumers of the current scalar field to consume the new shape without breaking existing tests: SocialAppraisalSystem.appraise_contract()'s trust-blend read (src/systems/social_systems/appraisal.py:30-36, currently `public_trust = source_entity.social.public_reputation / 2.0`), apply_reputation_discount() (src/systems/economy_systems/reputation_discount.py), and campaigns/social_memory.py's cross-episode carry-forward.
- Extend EntityState.to_canonical_dict() / CanonicalStateHasher (src/engine/checkpoint.py) and src/replay/fingerprint.py (currently line 69, `reputation={ent.social.public_reputation:.3f}`) to cover the new shape explicitly — public_reputation is currently 1 of the 10-of-15 SocialComponent fields already covered as a scalar; the shape change must preserve that determinism coverage in the same ticket, not leave it silently dropped.
- Document, as a corrected investigation finding, that PublicReputationProfile/ReputationUpdateService (src/core/cognition.py, src/domains/commitment/reputation.py) is a structurally distinct, unrelated field this ticket does not touch, despite now having one real call site (src/engine/quests.py:233).

## Out of Scope
- Any change to PublicReputationProfile, ReputationUpdateService, or QuestResolutionSystem's quest-completion wiring — a separate, unrelated system.
- The 5 already-tracked missing SocialComponent canonical-hash fields (debt_history, salience_history, nemesis_ids, place_attachment, betrayal_records) — tracked separately by TCK-20260902-SOCIAL-CANONICAL-HASH-GAP, not this ticket's concern.
- Idea 53's birth-seed write or idea 54's ClanState.clan_reputation field — sibling child tickets of the same epic that depend on this ticket landing first, not the reverse.
- Idea 55/58 (death-and-lineage branch) — tracked as a separate sibling child ticket.

## Acceptance Criteria
- SocialComponent.public_reputation (or its replacement locality-scoped structure) is read and written exclusively through RelationshipService.process_update(); no second write path exists, verified by a source-text guard test.
- A locality/observer-scoped read for the same entity at two different regions returns two distinguishably different reputation values after region-specific reputation-affecting events, verified by a new test.
- EntityState.to_canonical_dict()'s public_reputation coverage remains present and shape-correct after the change (no silent loss of determinism coverage), verified by an updated canonical-hash test.
- SocialAppraisalSystem.appraise_contract(), apply_reputation_discount(), and campaigns/social_memory.py all consume the new shape without breaking any existing test.
- This ticket's Investigation Notes explicitly record the corrected premise (PublicReputationProfile's real call site as of 2026-09-04, and why it remains structurally unrelated to this ticket's own scope) rather than repeating the epic doc's stale "zero call sites anywhere" claim.

## Related Tickets
- TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION
- TCK-20260828-REPUTATION-WITNESSED-EVENT-WIRING
- TCK-20260619-E33D-REP-DISCOUNTS
- TCK-20260902-SOCIAL-CANONICAL-HASH-GAP

## Related Docs
- docs/brainstorm/rpg_feature_atlas.html
- docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md
- docs/mechanics/03_economic_laws.md
- docs/parity_ledger/social_narrative.yaml
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md

## Related Stored Artifacts
None

## Related Code Areas
- src/core/models/social.py
- src/systems/social_systems/relationships.py
- src/systems/social_systems/appraisal.py
- src/systems/economy_systems/reputation_discount.py
- src/domains/campaigns/social_memory.py
- src/engine/checkpoint.py
- src/replay/fingerprint.py

## Assumptions / Open Questions
- Exact locality granularity (per-region vs per-observer vs per-settlement) is a Plan-phase decision; place_attachment's RegionID-keyed Dict[str, float] shape is the recommended default per investigation, not a mandate.
- This ticket must land before idea 53's and idea 54's own child tickets (both depend on this ticket's final field shape) — sequencing enforced via SEQUENCE.md for this batch.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
