---
status: done
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E43-SOCIAL-MEMORY
phase: epic_scoped
date: 2026-06-19
tags: [social-memory, reputation, cross-episode, campaign-consequence, relationship-decay, epic, phase-4]
---

# TCK-20260619-E43-SOCIAL-MEMORY

## Title
Epic 4.3 · Social Memory as Campaign Consequence

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Reputation and commitment are solid within one run. Nothing persists betrayal/rescue/cooperation history across episodes. Requires `CampaignState.NarrativeLedger` (Epic 3.2) as the storage layer — this epic is explicitly blocked on that foundation.

Score: 8/10 · Effort: M

## Scope
- **Prerequisite:** TCK-20260619-E32-CAMPAIGN-RUNTIME (NarrativeLedger — hard block)
- `SocialMemoryRecord` + `InteractionRecord` dataclasses
- `SocialMemoryExporter` (end-of-episode hook) + `SocialMemoryImporter` (start-of-episode hook) wired into `CampaignOrchestrator._advance_state()`
- `SocialMemoryDecay`: friendship half-life ~3 episodes (40% loss/ep), grudge half-life ~7 episodes (10% loss/ep)
- `FactionSocialMemory`: collective hostility persists across episodes even when all members die
- Consequence events: `LEGENDARY_ARRIVAL`, `KNOWN_TRAITOR_SPOTTED`, `OLD_DEBT_COLLECTED`
- Child tickets: (a) SocialMemoryRecord model, (b) Exporter+Importer hooks, (c) decay mechanics, (d) faction memory, (e) consequence events

## Acceptance Criteria
- In a 2-episode campaign, an entity that completes a quest for Faction A in episode 1 receives a faction reputation bonus in episode 2 that measurably increases its starting score with Faction A's affiliated NPCs

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (prerequisite — hard block)
- TCK-20260619-E51-CHRONICLE (unlocked: chronicle reads social memory events from NarrativeLedger)

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md` § Social Memory as Campaign Consequence
- `docs/simulation/domains/social_systems_contract.md`
- `docs/parity_ledger/social_narrative.yaml`
- New doc: `docs/simulation/domains/social_memory_contract.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260613-DOC-SOCIAL-INTELLIGENCE-SYSTEMS/`
- `stored_artifacts/TCK-20260619-E43-SOCIAL-MEMORY/`

## Related Code Areas
- `src/systems/social_systems/memory.py:L6` (SocialMemoryService — existing place attachment; do NOT extend for cross-episode; use new file)
- `src/domains/campaigns/social_memory.py` (new)
- `src/domains/campaigns/orchestrator.py` (add exporter/importer hooks)

## Files Changed
- `tickets/todos/TCK-20260619-E43A-SOCIAL-MEM-MODEL.md` (new child ticket)
- `tickets/todos/TCK-20260619-E43B-EXPORT-IMPORT.md` (new child ticket)
- `tickets/todos/TCK-20260619-E43C-DECAY.md` (new child ticket)
- `tickets/todos/TCK-20260619-E43D-FACTION-MEMORY.md` (new child ticket)
- `tickets/todos/TCK-20260619-E43E-CONSEQUENCE-EVENTS.md` (new child ticket)
- `staging_artifacts/TCK-20260619-E43-SOCIAL-MEMORY/{investigation,plan,test_plan}.md` (new)

## Completion Summary
Epic scoped into 5 child tickets (E43A → E43B → E43C/E43D parallel → E43E). Key finding: `SocialMemoryService` at `src/systems/social_systems/memory.py:L6` handles place attachment + nemesis promotion — it does NOT handle cross-episode memory; new `src/domains/campaigns/social_memory.py` is the right home. Exporter/Importer are orchestration hooks, NOT embedded in AuthoritativeState. Decay constants: FRIENDSHIP_DECAY=0.40 (friendship half-life ~3 ep), GRUDGE_DECAY=0.10 (grudge half-life ~7 ep). Faction collective hostility persists in `FactionSocialMemory` regardless of member deaths.
