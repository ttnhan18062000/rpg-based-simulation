---
status: open
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53-FACTION-DIPLOMACY
phase: open
date: 2026-06-19
tags: [faction, diplomacy, war, territory, alliance, siege, grand-strategy, epic, phase-5]
---

# TCK-20260619-E53-FACTION-DIPLOMACY

## Title
Epic 5.3 · Faction & Diplomacy System (fresh build — XL)

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
This is the single largest missing system. Zero engine code exists — `src/content_semantics/faction.py` is catalog data, not behavior. `docs/systems/grand_strategy.md` is cited only to establish that no macro-political layer currently exists; it is NOT a design or porting source. Build fresh against V2 architecture.

Score: 10/10 · Effort: XL · Source: `docs/plans/engine_future_epics_roadmap.md` § A (Headline Finding)

## Scope
Implement in four sequential phases (each a cluster of child standard tickets):

**Phase A — Faction as Agent:**
- `FactionState` durable model: territory[], resources[], diplomatic_relations{faction_id: TensionLevel}, active_doctrines[], military_strength
- `FactionDecisionPhase`: runs at governance layer; produces faction-level directives (expand territory, seek alliance, respond to threat, commission quests)
- Faction directives propagate to entity scoring: GUARD entities near contested border score patrol routes higher; MERCHANT near allied region scores trade routes higher
- Faction awareness: factions observe world events (resource depletion, calamity, entity deaths) and update tension levels

**Phase B — Diplomacy:**
- Diplomatic actions: treaty offer, trade agreement, non-aggression pact, alliance, betrayal
- Diplomatic states: NEUTRAL, TENSE, HOSTILE, WAR, ALLIED, VASSAL
- Diplomatic events flow through `NarrativeLedger`

**Phase C — Territorial Conflict & War:**
- War declaration triggers `MilitaryConflictPhase`: faction commits entity squads to contested regions
- Siege mechanics: besieging faction depletes target region's service availability over N ticks; defender responds with reinforcement
- Territory transfer: after siege victory, region changes faction ownership; sovereignty entries update
- War exhaustion: military_strength depletes; both sides incentivized to end long wars

**Phase D — History Integration:**
- All faction-level events flow to `NarrativeLedger`
- Chronicle Compiler names wars and alliances ("The Thornwood War of Year 3")

Child tickets: one child epic per phase (A, B, C, D), each decomposed into standard tickets at implementation time.

## Out of Scope
- Player faction control
- Real-time strategy layer
- Culture/ideology generation (Phase 6 Epic 6.2)
- Cross-campaign faction legacy (via Epic 4.3 extension)
- `grand_strategy.md` is NOT a design source — do not port any legacy code or semantics

## Acceptance Criteria
- In a 3-episode campaign with ≥3 factions, at least one war is declared, fought over 2+ episodes, and resolved with territory transfer
- Chronicle Compiler names the war
- `FactionDecisionPhase` runs at governance layer and produces entity-level directive propagation each tick

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (prerequisite: NarrativeLedger, multi-episode state)
- TCK-20260619-E21-RESOURCE-ECOLOGY (prerequisite: resource pressure drives territorial conflict)
- TCK-20260619-E51-CHRONICLE (unlocked: chronicle names faction wars)
- TCK-20260619-E62-CULTURE-DRIFT (unlocked after this)
- TCK-20260619-E63-FEATURE-PACKS (unlocked after this)

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § A (Headline Finding + Section A)
- `docs/plans/long_term_development_roadmap.md` § Epic 5.3
- `docs/mechanics/04_strategic_cognition.md` (FactionDecisionPhase produces entity-level directives that modify route scoring — update with faction directive scoring terms)
- `docs/mechanics/02_combat_laws.md` (Phase C territorial war uses combat resolution for siege mechanics — faction squads must use standard damage formula; verify before implementing MilitaryConflictPhase)
- `docs/mechanics/05_world_evolution.md` (add faction-driven evolution documentation)
- `docs/mechanics/regional_sovereignty.md` (update sovereignty to include faction ownership transfer)
- `docs/engine/governance_logic.md` (update when FactionDecisionPhase is added at governance layer)
- `docs/systems/grand_strategy.md` (scope reference only — establishes absence, NOT design source; archive to `docs/archive/` after Phase A complete)
- `docs/parity_ledger/world_dynamics.yaml` (faction/political entries — add as `verified`)
- `docs/parity_ledger/substrate.yaml` (FactionState persistence entries)
- New doc: `docs/systems/faction_contract.md` (V2 FactionState model, FactionDecisionPhase, diplomatic states, territorial rules, siege mechanics)

## Related Stored Artifacts
- (none — fresh build)

## Related Code Areas
- `src/content_semantics/faction.py` (catalog data — reference for faction IDs only)
- `src/core/enums.py:L15` (Faction enum)
- `src/engine/policy.py:L10` (GovernorPolicy — governance phase insertion point)
- `src/core/state.py` (AuthoritativeState — add FactionState)

## Assumptions / Open Questions
- How many factions exist in current catalog data? Check `src/content_semantics/faction.py` for the count
- Does `GovernorPolicy` support adding new phases, or does `FactionDecisionPhase` need to be registered differently?

## Implementation Notes
XL epic. Scope Phase A first (faction as agent) as a child epic, get it done and tested before touching Phase B. Each child epic should be implementable independently without Phase C or D being in progress. Phase D is the cheapest (NarrativeLedger wire-up) and can be threaded in during Phase B.

**Critical:** Do not port legacy `grand_strategy.md` semantics. The legacy system used a different state model and combat resolution. Build `FactionState` as a V2 typed durable model from scratch.

After each phase: create or update `docs/systems/faction_contract.md` (fresh V2 contract — not `grand_strategy.md`). Update `docs/engine/governance_logic.md` when FactionDecisionPhase is added. Update `docs/parity_ledger/world_dynamics.yaml` with faction entries. Update `docs/parity_ledger/substrate.yaml` for FactionState persistence. Run `make knowledge-index-update` after docs/ changes. Consider archiving `docs/systems/grand_strategy.md` to `docs/archive/` once Phase A is complete.

## Test Summary
Per child ticket/epic. Key test files:
- New `tests/unit/faction/test_faction_state.py` (Phase A):
  - `test_faction_decision_phase_produces_directive()` — FactionDecisionPhase with mocked world state; assert at least one directive output
  - `test_faction_tension_increases_on_resource_depletion()` — inject depletion event; assert tension level rises
- New `tests/unit/faction/test_diplomacy.py` (Phase B):
  - `test_diplomatic_state_transitions()` — assert valid transitions: NEUTRAL→TENSE→HOSTILE→WAR→ALLIED
  - `test_alliance_reduces_shared_territory_threat_score()`
- New `tests/integration/scenarios/test_faction_campaign.py` (Phase C):
  - `test_war_declared_and_resolved_with_territory_transfer()` — 3-episode campaign with 3 factions; assert war_declared → sieges → territory_transferred events
  - `test_chronicle_names_the_war()` — ChronicleCompiler names the war after Phase D integration

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
