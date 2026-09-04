---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260904-CLAN-REPUTATION-ASSOCIATION
phase: open
date: 2026-09-04
tags: [social]
---

# TCK-20260904-CLAN-REPUTATION-ASSOCIATION

## Title
Idea 54 — Guilt by Association (ClanState.clan_reputation)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Design idea 54 (Guilt by Association) is gated on M2's idea 36 (Clan) existing as real state — confirmed satisfied: TCK-20260831-CLAN-STATE-SCHEMA is DONE and fully wired into the authoritative pipeline via TCK-20260903-CLAN-LIFECYCLE-SUCCESSION (also DONE). Investigation (2026-09-04) found the concern's own framing (inherited from the epic doc's paraphrase — "one member's act propagating to clan-mates") does not match the real idea-54 schema card: the actual proposal is a NEW ClanState.clan_reputation: float field, tracked independently the same way an individual's own public_reputation is, read by strangers judging an unfamiliar member — not a mechanism that mutates every clan-mate's own SocialComponent.public_reputation. This ticket must scope from the real schema card, not the epic doc's inaccurate paraphrase. Confirmed: ClanState (src/core/state.py:751-766) has member_entity_ids: Tuple[int,...] but no entity_id -> clan_id reverse lookup exists anywhere — any trigger logic needs either an O(n_clans) scan or a new index, a real open scoping question. This ticket depends on TCK-20260904-REPUTATION-LOCALITY-SCOPE (idea 60) landing first, per the epic's own sequencing constraint, though idea 60 and idea 54 write to structurally distinct fields (SocialComponent.public_reputation vs. the new ClanState.clan_reputation) — this ticket's Plan phase must independently re-confirm whether that dependency is load-bearing or just a hedge, since the two fields may not actually interact.

## Scope
- Add a new ClanState.clan_reputation: float field (src/core/state.py) — the clan's own aggregate score, tracked independently from any individual member's SocialComponent.public_reputation, following the Durable State Rule (typed model, stable AuthoritativeState location, defined lifecycle, tests) already satisfied by TCK-20260903-CLAN-LIFECYCLE-SUCCESSION's wiring for the rest of ClanState.
- Wire real, already-detected reputation-affecting events to also produce a ClanUpdate adjusting the acting entity's clan's clan_reputation: contract betrayal (src/systems/social_systems/contracts.py, notoriety_delta=0.5/betrayal_increment=1) and party defection (src/systems/social_systems/party_lifecycle.py:196, notoriety_delta=2.0). Apply only through apply.py's existing clan_updates path — never a direct ClanState mutation. Do NOT wire through ReputationUpdateService/QuestResolutionSystem — that touches the wrong (unrelated) field.
- Resolve the entity_id -> clan_id lookup gap: either add a real reverse index or explicitly accept an O(n_clans) scan over state.clans.values() — a Plan-phase decision, not resolved by investigation.
- Extend the stranger-judgment read path (SocialAppraisalSystem or equivalent, src/systems/social_systems/appraisal.py) so an observer with no direct personal trust/familiarity history toward a given clan member blends that member's clan's clan_reputation into their caution/trust prior, distinguishably different from how the same observer judges a member they do have direct history with.
- Any propagation/aggregation logic touching ClanState.member_entity_ids must iterate in a fixed sorted order (never raw tuple iteration) for determinism.

## Out of Scope
- Per-member reputation propagation to clan-mates' own SocialComponent.public_reputation — the epic doc's original framing was inaccurate; this ticket does not mutate individual members' own reputation fields.
- Wiring through ReputationUpdateService, PublicReputationProfile, or QuestResolutionSystem's quest-completion path — a structurally separate, unrelated field/system.
- Idea 60's public_reputation locality-scoping change or idea 53's birth-seed write — sibling/prerequisite child tickets of the same epic.

## Acceptance Criteria
- ClanState gains a clan_reputation: float field with to_canonical_dict()/from_dict() round-trip test coverage, mirroring the existing test_clan_state_serialization_round_trip pattern.
- A contract-betrayal or party-defection event that produces a SocialUpdate reputation delta on the acting entity also produces a measurable ClanUpdate change to clans[clan_id].clan_reputation, applied only through apply.py's clan_updates path, verified by a new test.
- A stranger entity with no personal trust/familiarity history toward a given clan member reads a caution/trust prior that incorporates that member's clan's clan_reputation, distinguishably different from how the same stranger judges a member they do have direct history with, verified by a new test.
- Any propagation/aggregation over member_entity_ids produces bit-identical ClanUpdate output across repeated runs, verified by a determinism test.
- This ticket introduces zero writes to any individual member's own SocialComponent.public_reputation — verified by a source-text guard test, confirming the scope correction (clan-level field, not member-propagation) actually held.

## Related Tickets
- TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION
- TCK-20260904-REPUTATION-LOCALITY-SCOPE
- TCK-20260831-CLAN-STATE-SCHEMA
- TCK-20260903-CLAN-LIFECYCLE-SUCCESSION

## Related Docs
- docs/brainstorm/rpg_expected_schemas.html
- docs/brainstorm/rpg_feature_atlas.html
- docs/guidelines/intentional_divergences.md
- docs/mechanics/04_strategic_cognition.md
- docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md

## Related Stored Artifacts
None

## Related Code Areas
- src/core/state.py
- src/core/models/social.py
- src/systems/social_systems/relationships.py
- src/systems/social_systems/contracts.py
- src/systems/social_systems/party_lifecycle.py
- src/systems/social_systems/clan_lifecycle.py
- src/systems/social_systems/appraisal.py

## Assumptions / Open Questions
- reputation_weight_on_stranger_judgment (the schema card's second proposed field) has no proposed formula/anchor in the source card — an open design question for Plan phase.
- Whether to add a real entity->clan reverse index or accept an O(n_clans) scan is undecided — Plan-phase decision.
- ClanState is not currently referenced in replay/fingerprint.py, so clan_reputation likely doesn't need canonical-hash coverage — this must be explicitly re-confirmed during Investigate/Plan, not assumed.
- Whether this ticket's dependency on idea 60 landing first is load-bearing (the two fields are structurally distinct) should be independently re-confirmed by this ticket's own Plan phase rather than inherited unquestioned from the epic doc's blanket sequencing note.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
