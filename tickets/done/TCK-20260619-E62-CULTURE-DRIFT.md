---
status: done
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260619-E62-CULTURE-DRIFT
phase: done
date: 2026-06-19
tags: [culture-drift, myth, regional-culture, doctrine, long-horizon, epic, phase-6]
---

# TCK-20260619-E62-CULTURE-DRIFT

## Title
Epic 6.2 · Culture / Myth Drift (Long Horizon — 18+ months)

## Status
DONE (EPIC_SCOPED)

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
- **Prerequisites:** TCK-20260619-E51-CHRONICLE (done — E51A–E51E all complete); TCK-20260619-E53-FACTION-DIPLOMACY (scoped — E53A–D child epics all scoped with child tickets)
- `CultureState` per region: frozen dataclass with four axes (fatalism, hero_veneration, resource_scarcity_memory, faction_conflict_exposure)
- `CampaignState.region_cultures` field for cross-episode culture persistence
- `CultureDeriver` reads ChronicleHierarchy → derives CultureState per region
- `CultureDriftExporter`/`Importer` wired into `CampaignOrchestrator._advance_state()`
- `CulturalBiasApplicator` + `MotivationBiasService` extension for transient per-region motivation overlay
- Parity ledger entries, acceptance test, docs

## Out of Scope
- Player-controlled culture
- Language generation
- Real-time cultural debate
- Modifying durable MotivationModel on entities (overlay is transient)

## Acceptance Criteria
- In a 5-episode campaign, two regions with different narrative histories produce measurably different entity behavioral distributions in episode 5
- Specifically: mean motivation multiplier for `caution` tag differs between a "calamity region" and a "hero region" by >0.1

## Related Tickets
- TCK-20260619-E51-CHRONICLE (prerequisite — complete)
- TCK-20260619-E53-FACTION-DIPLOMACY (prerequisite — scoped)
- TCK-20260619-E62A-CULTURE-MODEL (child — CultureState model + CampaignState field)
- TCK-20260619-E62B-CULTURE-DERIVER (child — ChronicleHierarchy → CultureState derivation + exporter/importer)
- TCK-20260619-E62C-MOTIVATION-OVERLAY (child — CulturalBiasApplicator + MotivationBiasService wiring)
- TCK-20260619-E62D-PARITY-VERIFY (child — parity ledger + acceptance test + docs)

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § A (Culture/Myth Drift)
- `docs/plans/long_term_development_roadmap.md` § Epic 6.2
- `docs/simulation/domains/belief_and_detour_contract.md`
- `docs/world/culture_drift_contract.md` (to be created by E62C/D)
- `docs/mechanics/05_world_evolution.md` (to be extended by E62D)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E62-CULTURE-DRIFT/investigation.md`
- `stored_artifacts/TCK-20260619-E62-CULTURE-DRIFT/plan.md`
- `stored_artifacts/TCK-20260619-E62-CULTURE-DRIFT/test_plan.md`

## Related Code Areas
- `src/domains/culture/` (new domain — E62A/B/C/D)
- `src/core/strategic.py` (MotivationModel/ValuePreferenceProfile — read context)
- `src/domains/motivation/service.py` (MotivationBiasService — extend in E62C)
- `src/domains/campaigns/state.py` (CampaignState — add region_cultures in E62A)
- `src/domains/campaigns/orchestrator.py` (wire exporter in E62B)
- `src/domains/chronicle/grouper.py` (ChronicleGrouper — reused in E62B)

## Assumptions / Open Questions
- E53 child tickets (E53Aa–E53Dd) must be implemented before E62A can start, as faction event types (war_declared, territory_transferred, faction_destroyed) need to exist in NarrativeLedger for E62B derivation
- Region attribution for NarrativeLedgerEntry relies on `payload.get("region_id")`; E53 child tickets should confirm this is populated in faction/war events; if not, E62B handles gracefully with global fallback
- NORMALISE_DENOMINATOR=3.0 and CULTURE_ACTIVATION_THRESHOLD=0.3 are tuning constants defined at module level

## Implementation Notes
- Epic decomposes into 4 linear standard tickets: E62A → E62B → E62C → E62D
- Key architecture decision: CultureState persists in CampaignState (episode-boundary),
  not in RegionState (tick-level). Derivation is pure/stateless via ChronicleHierarchy.
- Cultural overlay is transient (not baked into durable MotivationModel). This preserves
  determinism and durable-state purity per Architecture Rule.
- New domain directory: `src/domains/culture/` (model, deriver, exporter, importer, applicator)
- Parity ledger: add WORLD-CULT-001/002/003 to `docs/parity_ledger/world_dynamics.yaml`

## Test Summary
- Unit tests in `tests/unit/culture/` (created across E62A/B/C)
- Integration acceptance test in `tests/integration/culture/test_culture_drift_acceptance.py`
- Acceptance: `test_two_regions_diverge_after_5_episodes`

## Files Changed
_To be filled on completion._

## Completion Summary
EPIC_SCOPED on 2026-06-22. Four child tickets created in tickets/todos/:
E62A-CULTURE-MODEL, E62B-CULTURE-DERIVER, E62C-MOTIVATION-OVERLAY, E62D-PARITY-VERIFY.
Linear dependency chain: E62A → E62B → E62C → E62D.
Prerequisites: E51 (Chronicle Compiler) done; E53 (Faction Diplomacy) scoped.
All three staging artifacts (investigation.md, plan.md, test_plan.md) migrated to
stored_artifacts/TCK-20260619-E62-CULTURE-DRIFT/.
