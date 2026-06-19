---
status: open
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E43-SOCIAL-MEMORY
phase: open
date: 2026-06-19
tags: [social-memory, reputation, cross-episode, campaign-consequence, relationship-decay, epic, phase-4]
---

# TCK-20260619-E43-SOCIAL-MEMORY

## Title
Epic 4.3 · Social Memory as Campaign Consequence

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Reputation and commitment are solid within one run. Nothing persists betrayal/rescue/cooperation history across episodes. Requires `CampaignState.NarrativeLedger` (Epic 3.2) as the storage layer — this epic is explicitly blocked on that foundation.

Score: 8/10 · Effort: M · Source: `docs/plans/engine_future_epics_roadmap.md` § B, `docs/audits/D01_rpg_feature_impact.md`

## Scope
- **Prerequisite:** TCK-20260619-E32-CAMPAIGN-RUNTIME (NarrativeLedger — the storage layer this epic writes into and reads from)
- `SocialMemoryRecord` as a durable cross-episode model: entity_id, interaction_history[], reputation_events[], relationship_scores{entity_id: float}
- Cross-episode reputation transfer: at episode end, `SocialMemoryExporter` serializes entity reputation delta into `CampaignState`; at episode start, `SocialMemoryImporter` applies legacy reputation
- Relationship decay: old scores decay toward neutral over episodes; betrayals decay slower than cooperations (grudge half-life > friendship half-life)
- Faction memory: faction reputation tracks separately; a faction that was wronged maintains collective hostility even if key individual members died
- Social consequence events: `LEGENDARY_ARRIVAL`, `KNOWN_TRAITOR_SPOTTED`, `OLD_DEBT_COLLECTED`
- Child tickets: (a) SocialMemoryRecord model, (b) SocialMemoryExporter/Importer + NarrativeLedger integration, (c) relationship decay mechanics, (d) faction memory, (e) consequence events

## Out of Scope
- Procedural relationship narrative generation
- Player-facing relationship screen
- Cross-campaign (beyond one campaign) social memory

## Acceptance Criteria
- In a 2-episode campaign, an entity that completes a quest for Faction A in episode 1 receives a faction reputation bonus in episode 2 that measurably increases its starting score with Faction A's affiliated NPCs

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (prerequisite — hard block)
- TCK-20260619-E51-CHRONICLE (unlocked: chronicle reads social memory events from NarrativeLedger)

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md` § Social Memory as Campaign Consequence
- `docs/plans/engine_future_epics_roadmap.md` § B
- `docs/plans/long_term_development_roadmap.md` § Epic 4.3
- `docs/mechanics/04_strategic_cognition.md` (social memory feeds into scoring — legacy reputation affects route scoring weights; update scoring documentation if new reputation terms are added)
- `docs/simulation/domains/social_systems_contract.md` (update with SocialMemoryRecord, cross-episode exporter/importer, consequence event types)
- `docs/parity_ledger/social_narrative.yaml` (cross-episode reputation entries — add as `verified`)
- New doc: `docs/simulation/domains/social_memory_contract.md` (SocialMemoryRecord schema, decay rates, faction memory model, consequence events)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260613-DOC-SOCIAL-INTELLIGENCE-SYSTEMS/`
- `stored_artifacts/TCK-20260501-SOCIAL-LIFECYCLE/`

## Related Code Areas
- `src/core/strategic.py:L159` (ContractState — reputation history baseline)
- `src/domains/campaigns/schema.py:L43` (CampaignEvent — extend with social memory events)
- `src/domains/campaigns/` (CampaignState — add SocialMemoryRecord storage)

## Assumptions / Open Questions
- How is entity reputation currently stored per-run? Check `src/core/state.py` for reputation or social score field
- What is the "grudge half-life" decay rate? Derive from game design intent, not arbitrary constant

## Implementation Notes
The `SocialMemoryExporter` at episode end and `SocialMemoryImporter` at episode start should be implemented as campaign orchestration hooks, not embedded in `AuthoritativeState`. This keeps the cross-episode logic cleanly separated from the per-episode simulation.

After implementation: create `docs/simulation/domains/social_memory_contract.md` documenting SocialMemoryRecord schema, decay constants, faction memory rules, and consequence event types. Update `docs/simulation/domains/social_systems_contract.md`. Update `docs/parity_ledger/social_narrative.yaml` with cross-episode reputation entries. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
- New file `tests/unit/social/test_social_memory.py`:
  - `test_social_memory_record_serializes_to_campaign_state()` — SocialMemoryExporter output round-trips through CampaignState correctly
  - `test_betrayal_decay_slower_than_cooperation()` — inject betrayal and cooperation events at ep1; advance 3 episodes; assert betrayal score decays more slowly
  - `test_faction_hostility_persists_after_key_member_death()` — kill all known members of Faction A, assert collective hostility persists in episode 2
- New file `tests/integration/scenarios/test_social_memory.py`:
  - `test_reputation_transfer_across_episodes()` — complete quest for Faction A ep1; assert starting reputation bonus with Faction A NPCs in ep2
  - `test_known_traitor_event_fires_on_encounter()` — entity betrayed Faction B in ep1; encounter Faction B NPC in ep2; assert `KNOWN_TRAITOR_SPOTTED` event

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
