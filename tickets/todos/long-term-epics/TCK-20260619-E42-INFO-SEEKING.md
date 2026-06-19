---
status: open
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260619-E42-INFO-SEEKING
phase: open
date: 2026-06-19
tags: [information-seeking, belief, leads, knowledge-gap, paid-info, cognition, epic, phase-4]
---

# TCK-20260619-E42-INFO-SEEKING

## Title
Epic 4.2 · Active Information-Seeking / Belief Economy

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Passive leads and belief/trust/strategic-blocker system exist. Blockers are material-resource-only; leads are coordinate-only — no person/concept leads. Entities are effectively omniscient-by-passive-injection. No deliberate "ask guide/merchant," no paid information transactions, no contradiction-driven replanning.

Score: 8/10 · Effort: M · Source: `docs/plans/engine_future_epics_roadmap.md` § B, `docs/audits/D01_rpg_feature_impact.md`

## Scope
- **Prerequisite:** TCK-20260619-E32-CAMPAIGN-RUNTIME (cross-episode lead staleness; NarrativeLedger)
- `InformationNeed` as a first-class belief state: entity recognizes a gap (missing lead for resource X) and generates an `information_seeking` project kind
- `InformationProvider` archetypes: MERCHANT, GUILD_MASTER, ELDER — each with `reliability_score` and `knowledge_age`; can answer queries about resource locations, faction tensions, entity whereabouts
- Paid information transactions: entity pays gold/reputation for a lead; provider receives gold/reputation; lead has quality (exact/approximate/rumored)
- Lead contradiction: entity arrives, finds lead wrong (node depleted, entity dead, faction hostile), generates `belief_contradiction` event; provider reputation decreases; revised seeking project starts
- Extend existing lead system (`src/core/strategic.py:L187` LeadState) to support `PERSON_LEAD` and `CONCEPT_LEAD` types (not just coordinate leads)
- Knowledge staleness decay: leads age, confidence degrades each tick; entity scores information_seeking routes higher as stale leads accumulate
- Child tickets: (a) InformationNeed belief state, (b) InformationProvider archetypes, (c) paid transaction + lead quality, (d) lead contradiction + replanning, (e) PERSON/CONCEPT lead types

## Out of Scope
- Deliberate deception/misinformation propagation (future)
- Collective rumor networks (Phase 6 culture drift)
- Player information queries

## Acceptance Criteria
- In a 600-tick run, at least one HERO entity transitions through: `information_need_identified → information_seeking_project → information_transaction → lead_received → route_scored_with_lead → belief_contradiction (if lead was stale) → information_seeking_retry`

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (prerequisite)
- TCK-20260619-E11-ENTITY-IDENTITY (prerequisite: personality drives information-seeking appetite)

## Related Docs
- `docs/audits/D01_rpg_feature_impact.md`
- `docs/plans/engine_future_epics_roadmap.md` § B
- `docs/plans/long_term_development_roadmap.md` § Epic 4.2
- `docs/simulation/domains/belief_and_detour_contract.md` (update with InformationNeed, PERSON_LEAD, CONCEPT_LEAD, knowledge staleness decay)
- `docs/simulation/domains/intelligence_system_contract.md` (update with InformationProvider archetypes and paid transaction contract)
- `docs/parity_ledger/strategic_cognition.yaml` (leads / knowledge-seeking entries — update to `verified`)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260613-DOC-SOCIAL-INTELLIGENCE-SYSTEMS/`

## Related Code Areas
- `src/core/strategic.py:L187` (LeadState — extend with PERSON/CONCEPT types)
- `src/core/self_model.py:L49` (KnowledgeFact, UnknownFact — information gap detection)
- `src/core/self_model.py:L169` (KnowledgeModelComponent)
- `src/domains/adventure/scoring.py` (information_seeking project scoring)

## Assumptions / Open Questions
- Does `UnknownFact` at `src/core/self_model.py:L65` already model the "entity knows it doesn't know X" concept (known-unknown), or does `InformationNeed` need to be a new model?
- How is `knowledge_age` tracked? Check if `KnowledgeFact` has a `created_tick` field

## Implementation Notes
Read `belief_and_detour_contract.md` and `intelligence_system_contract.md` (in stored_artifacts) carefully — they document precise behavioral semantics. The existing `BeliefEntry` model may already support some of what `InformationNeed` needs. Avoid duplicating the belief model.

After implementation: update `docs/simulation/domains/belief_and_detour_contract.md` with InformationNeed, PERSON_LEAD, CONCEPT_LEAD types, and staleness decay. Update `docs/simulation/domains/intelligence_system_contract.md` with InformationProvider archetypes. Update `docs/parity_ledger/strategic_cognition.yaml` for lead/information entries. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
- New file `tests/unit/cognition/test_information_seeking.py`:
  - `test_information_need_generates_seeking_project()` — inject a missing lead for resource X; assert `information_seeking` project kind generated
  - `test_paid_transaction_transfers_gold_and_lead()` — unit test with known entity gold; assert gold decremented, lead received, provider gold incremented
  - `test_lead_staleness_decay_reduces_confidence()` — advance N ticks after lead creation; assert confidence < 1.0
  - `test_person_and_concept_lead_types_accepted()` — assert PERSON_LEAD and CONCEPT_LEAD are valid LeadState types
- New file `tests/integration/scenarios/test_information_seeking.py`:
  - `test_belief_contradiction_on_stale_lead()` — inject stale coordinate lead pointing to depleted node; entity arrives; assert `belief_contradiction` event
  - `test_full_seeking_cycle_in_600_tick_run()` — 600-tick run with InformationProvider entity; assert `information_need_identified` → `information_transaction` → `lead_received` trace

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
