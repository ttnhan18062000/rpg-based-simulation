---
status: open
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260619-E62-CULTURE-DRIFT
phase: open
date: 2026-06-19
tags: [culture-drift, myth, regional-culture, doctrine, long-horizon, epic, phase-6]
---

# TCK-20260619-E62-CULTURE-DRIFT

## Title
Epic 6.2 · Culture / Myth Drift (Long Horizon — 18+ months)

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Individual-entity belief/rumor system exists. Nothing at culture scale. No culture-level value/taboo/myth distortion mechanism. Over long campaigns, regional cultures should develop distinct values, taboos, and myths based on their history.

Score: 6/10 · Effort: M · Requires: Epics 5.1 + 5.3

**Note: Phase 6 epics are speculative at planning time. Scope and sequencing must be re-evaluated after Phase 5 is complete.**

## Scope
- **Prerequisites:** TCK-20260619-E51-CHRONICLE (history compiler — culture is derived from narrative history); TCK-20260619-E53-FACTION-DIPLOMACY (political history to distort culture around)
- `CultureState` per region: updated by Chronicle Compiler based on accumulated narrative events
- Culture values feed into entity motivation profiles when they enter a region (doctrine system integration)
- A region with a history of calamity develops fatalistic cultural values; a region with a legendary hero develops a hero-cult

## Out of Scope
- Player-controlled culture
- Language generation
- Real-time cultural debate

## Acceptance Criteria
- In a 5-episode campaign, two regions with different narrative histories produce measurably different entity behavioral distributions in episode 5

## Related Tickets
- TCK-20260619-E51-CHRONICLE (prerequisite)
- TCK-20260619-E53-FACTION-DIPLOMACY (prerequisite)

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § A (Culture/Myth Drift)
- `docs/plans/long_term_development_roadmap.md` § Epic 6.2
- `docs/simulation/domains/belief_and_detour_contract.md`

## Related Code Areas
- `src/core/strategic.py` (doctrine system — cultural values wire in here)
- `src/domains/campaigns/` (CampaignState — CultureState persistence)

## Assumptions / Open Questions
- Re-evaluate full scope after Phase 5 is complete

## Implementation Notes
Scope this epic fresh at Phase 5 completion time. This ticket is a planning placeholder.

When implementing: update `docs/parity_ledger/world_dynamics.yaml` with culture-drift entries. Create `docs/world/culture_drift_contract.md`. Update `docs/mechanics/05_world_evolution.md` with cultural mechanics. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
To be defined at Phase 5 completion.

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
