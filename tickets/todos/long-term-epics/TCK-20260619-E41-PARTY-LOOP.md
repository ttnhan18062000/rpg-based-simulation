---
status: open
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E41-PARTY-LOOP
phase: open
date: 2026-06-19
tags: [party, social, cooperation, reward-split, escort, betrayal, epic, phase-4]
---

# TCK-20260619-E41-PARTY-LOOP

## Title
Epic 4.1 · Full Party Adventure Loop

## Status
OPEN

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
- Child tickets: (a) PartyState model, (b) sustained lifecycle + leadership election, (c) reward distribution protocol, (d) defection + escort behavior

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
- `docs/mechanics/04_strategic_cognition.md` (party scoring — class synergy bonuses and escort behavior are route-scoring modifications; update with new scoring terms)
- `docs/mechanics/02_combat_laws.md` (class synergy bonuses affect combat resolution outcomes; verify combat modifier ranges before adding synergy values)
- `docs/simulation/domains/social_systems_contract.md` (update with PartyState, FairShareProtocol, escort behavior contract)
- `docs/parity_ledger/social_narrative.yaml` (party/cooperation entries — update to `verified`)
- New doc: `docs/simulation/domains/party_contract.md` (PartyState model, lifecycle, reward distribution, defection rules, class synergy table)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260410-PH4-SOCIAL-CONTRACTS/`
- `stored_artifacts/TCK-20260501-SOCIAL-LIFECYCLE/`
- `stored_artifacts/TCK-20260424-PH3-M2-GROUP-COORDINATION/`

## Related Code Areas
- `src/core/state.py:L507` (GroupRecord — existing group state, extend or replace)
- `src/core/strategic.py:L159` (ContractState — existing social contract)
- `src/domains/adventure/scoring.py` (compatibility + escort scoring)

## Assumptions / Open Questions
- Does `GroupRecord` (`src/core/state.py:L507`) cover the durable party state needed, or is `PartyState` a new model? Compare GroupRecord fields to PartyState spec
- What is "Charisma-equivalent trait" in the OCEAN model? Map to `sociability` or a derived field

## Implementation Notes
Prior work (`TCK-20260424-PH3-M2-GROUP-COORDINATION`) established group formation. Read that stored artifact's investigation.md before implementing to avoid duplicating the formation logic. This epic adds *sustained lifecycle* on top.

After implementation: create `docs/simulation/domains/party_contract.md`. Update `docs/simulation/domains/social_systems_contract.md` with PartyState and lifecycle sections. Update `docs/parity_ledger/social_narrative.yaml` — add party lifecycle entries with `status: verified` and `test_path`. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
- New file `tests/unit/social/test_party_lifecycle.py`:
  - `test_party_formation_requires_compatibility_threshold()` — two entities below compatibility score; assert no party formed
  - `test_fair_share_protocol_distributes_by_contribution()` — unit test with known contribution values; assert reward splits correctly
  - `test_betrayal_desertion_fires_on_high_grievance()` — inject grievance above threshold; assert `betrayal_desertion` event and reputation penalty
  - `test_escort_target_route_scores_above_survival()` — ESCORT_TARGET designated; assert protecting-target routes scored higher than own survival routes
- New file `tests/integration/scenarios/test_party_lifecycle.py`:
  - `test_party_survives_two_quests()` — 600-tick `urban_political` run; assert party forms, completes 2 quests, ≥1 `NarrativeLedger` party entry
  - `test_party_dissolves_gracefully_after_quest_completion()`

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
