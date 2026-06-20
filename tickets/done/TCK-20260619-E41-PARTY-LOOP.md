---
status: done
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E41-PARTY-LOOP
phase: epic_scoped
date: 2026-06-19
tags: [party, social, cooperation, reward-split, escort, betrayal, epic, phase-4]
---

# TCK-20260619-E41-PARTY-LOOP

## Title
Epic 4.1 · Full Party Adventure Loop

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Recruit, contract appraisal, grudge/betrayal hooks exist (`TCK-20260410-PH4-SOCIAL-CONTRACTS`, `TCK-20260501-SOCIAL-LIFECYCLE` done). No sustained multi-tick party lifecycle, class-compatibility scoring, fair reward-split, or escort behavior. Social cohesion currently triggers parties but doesn't sustain them. D01 rates this as `[PARTIAL]`.

Score: 8/10 · Effort: M · Source: `docs/audits/D01_rpg_feature_impact.md` § Full Party Adventure Loop

## Scope
- **Prerequisite:** TCK-20260619-E32-CAMPAIGN-RUNTIME (NarrativeLedger for party history)
- `PartyState` durable model: members, formation_tick, shared_inventory, commitment_contracts[], grievance_log[]
- Party formation: requires mutual compatibility score above threshold (class, personality, prior grievance history)
- Sustained leadership: `PartyLeaderElection` each N ticks based on Charisma-equivalent trait; leadership changes produce morale events
- Reward distribution: `FairShareProtocol` computes each member's share based on contribution metrics
- Defection mechanics: high-grievance members may defect mid-quest (`betrayal_desertion` event); carries reputation penalty
- Escort behavior: one member designated `ESCORT_TARGET`; others score protecting-target routes above own survival routes
- Party dissolution: graceful (quest_completed + reward_distributed) or conflict (grievance_threshold_breached)
- Class synergy bonuses: WARRIOR+MAGE scores better on combat routes than two WARRIORs
- Child tickets: (a) GroupRecord lifecycle extension, (b) sustained lifecycle + leadership election, (c) reward distribution + class synergy, (d) defection + escort behavior

## Out of Scope
- Player-controlled party composition
- Multi-party faction wars (Phase 5)
- Cross-episode party legacy (carried automatically by Campaign Runtime)

## Acceptance Criteria
- In a 600-tick `urban_political` run with HERO entities, at least one party forms, completes a quest together, distributes rewards, and either dissolves gracefully or produces a `betrayal_desertion` event
- Party history appears in `NarrativeLedger`

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (prerequisite: NarrativeLedger)
- TCK-20260619-E11-ENTITY-IDENTITY (prerequisite: HERO entities with class differentiation)

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md` § Full Party Adventure Loop
- `docs/plans/engine_future_epics_roadmap.md` § B
- `docs/plans/long_term_development_roadmap.md` § Epic 4.1
- `docs/mechanics/04_strategic_cognition.md`
- `docs/simulation/domains/social_systems_contract.md`
- `docs/parity_ledger/social_narrative.yaml`
- New doc: `docs/simulation/domains/party_contract.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260410-PH4-SOCIAL-CONTRACTS/`
- `stored_artifacts/TCK-20260501-SOCIAL-LIFECYCLE/`
- `stored_artifacts/TCK-20260619-E41-PARTY-LOOP/`

## Related Code Areas
- `src/core/state.py:L507` (GroupRecord — extend with lifecycle fields)
- `src/core/strategic.py:L159` (ContractState)
- `src/domains/adventure/scoring.py`

## Files Changed
- `tickets/todos/TCK-20260619-E41A-GROUP-LIFECYCLE.md` (new child ticket)
- `tickets/todos/TCK-20260619-E41B-LEADERSHIP.md` (new child ticket)
- `tickets/todos/TCK-20260619-E41C-REWARD-DIST.md` (new child ticket)
- `tickets/todos/TCK-20260619-E41D-DEFECTION-ESCORT.md` (new child ticket)
- `staging_artifacts/TCK-20260619-E41-PARTY-LOOP/{investigation,plan,test_plan}.md` (new)

## Completion Summary
Epic scoped into 4 child tickets (E41A → E41B → E41C → E41D). Key finding: `GroupRecord` at `src/core/state.py:L507` is the correct extension target — no new `PartyState` class needed (avoids state bifurcation). Charisma-equivalent = `sociability` in `PersonalityComponent` (OCEAN Big Five). Leadership election at 100-tick intervals; defection threshold = grievance_log length ≥ 3. FairShareProtocol distributes via `ResourceTransferIntent`, not direct mutation. Escort behavior via PROTECT_TARGET route family scoring (+3.0 urgency bonus). Class synergy: WARRIOR+MAGE → ×1.15 combat, HERO+any → ×1.10 quest.
