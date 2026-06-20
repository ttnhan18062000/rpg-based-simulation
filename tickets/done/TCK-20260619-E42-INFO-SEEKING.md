---
status: done
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260619-E42-INFO-SEEKING
phase: epic_scoped
date: 2026-06-19
tags: [information-seeking, belief, leads, knowledge-gap, paid-info, cognition, epic, phase-4]
---

# TCK-20260619-E42-INFO-SEEKING

## Title
Epic 4.2 · Active Information-Seeking / Belief Economy

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Passive leads and belief/trust/strategic-blocker system exist. Blockers are material-resource-only; leads are coordinate-only — no person/concept leads. Entities are effectively omniscient-by-passive-injection. No deliberate "ask guide/merchant," no paid information transactions, no contradiction-driven replanning.

Score: 8/10 · Effort: M

## Scope
- **Prerequisite:** TCK-20260619-E32-CAMPAIGN-RUNTIME
- `InformationNeed` as a first-class belief state built on `UnknownFact` extension
- `InformationProvider` archetypes: MERCHANT, GUILD_MASTER, ELDER
- Paid information transactions via `ResourceTransferIntent`
- Lead contradiction: `belief_contradiction` event; provider reliability_score decrements
- PERSON_LEAD and CONCEPT_LEAD via `LeadKind` enum migration
- Knowledge staleness decay: `DECAY_RATE=0.0001`, effective certainty at read time
- Child tickets: (a) InformationNeed from UnknownFact, (b) InformationProvider archetypes, (c) paid transactions, (d) contradiction + staleness, (e) PERSON/CONCEPT lead types

## Acceptance Criteria
- In a 600-tick run, at least one HERO entity transitions through: `information_need_identified → information_seeking_project → information_transaction → lead_received → route_scored_with_lead → belief_contradiction (if lead was stale) → information_seeking_retry`

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (prerequisite)
- TCK-20260619-E11-ENTITY-IDENTITY (prerequisite)

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md`
- `docs/simulation/domains/belief_and_detour_contract.md`
- `docs/simulation/domains/information_contract.md`
- `docs/parity_ledger/strategic_cognition.yaml`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260613-DOC-SOCIAL-INTELLIGENCE-SYSTEMS/`
- `stored_artifacts/TCK-20260619-E42-INFO-SEEKING/`

## Related Code Areas
- `src/core/strategic.py:L187` (LeadState)
- `src/core/self_model.py:L65` (UnknownFact — extend with seeking_project_id)
- `src/domains/information/providers.py` (new InformationProviderState)

## Files Changed
- `tickets/todos/TCK-20260619-E42A-INFO-NEED.md` (new child ticket)
- `tickets/todos/TCK-20260619-E42B-INFO-PROVIDER.md` (new child ticket)
- `tickets/todos/TCK-20260619-E42C-PAID-TRANSACTION.md` (new child ticket)
- `tickets/todos/TCK-20260619-E42D-CONTRADICTION.md` (new child ticket)
- `tickets/todos/TCK-20260619-E42E-LEAD-TYPES.md` (new child ticket)
- `staging_artifacts/TCK-20260619-E42-INFO-SEEKING/{investigation,plan,test_plan}.md` (new)

## Completion Summary
Epic scoped into 5 child tickets (E42A → E42B → E42C → E42D → E42E). Key finding: `UnknownFact` at `src/core/self_model.py:L65` IS the InformationNeed model — extend rather than duplicate (add `seeking_project_id`, `priority`). `LeadState.kind` is raw string — E42E formalizes as `LeadKind` enum with PERSON + CONCEPT. Staleness decay: read-time effective_certainty formula, DECAY_RATE=0.0001 (certainty halves over 10000 ticks). Gold transactions via `ResourceTransferIntent(source_kind="INFORMATION_PURCHASE")`.
