---
status: done
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53-FACTION-DIPLOMACY
phase: done
date: 2026-06-19
tags: [faction, diplomacy, war, territory, alliance, siege, grand-strategy, epic, phase-5]
---

# TCK-20260619-E53-FACTION-DIPLOMACY

## Title
Epic 5.3 · Faction & Diplomacy System (fresh build — XL)

## Status
DONE

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
Implement in four sequential phases (each a child epic):

**Phase A — Faction as Agent (E53A-FACTION-AGENT):**
- `FactionState` durable model + `AuthoritativeState.factions`
- `FactionDecisionPhase` at governance layer
- Entity-level directive propagation (GUARD/MERCHANT/HERO scoring)
- Faction awareness: tension_level updates from world events

**Phase B — Diplomacy (E53B-DIPLOMACY):**
- DiplomaticState enum (NEUTRAL/TENSE/HOSTILE/WAR/ALLIED/VASSAL)
- Diplomatic actions as FactionDirective subtypes
- State machine transitions + NarrativeLedger wiring

**Phase C — Territorial Conflict & War (E53C-WAR):**
- MilitaryConflictPhase: war declaration, squad commitment, siege mechanics
- Territory transfer via authoritative pipeline
- War exhaustion draining military_strength

**Phase D — History Integration (E53D-HISTORY):**
- All faction events → NarrativeLedger with significance scores
- ChronicleNamer templates for faction events
- Archive `docs/systems/grand_strategy.md` → `docs/archive/grand_strategy_v1.md`
- Create `docs/systems/faction_contract.md` (V2)

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
- TCK-20260619-E53A-FACTION-AGENT (child epic)
- TCK-20260619-E53B-DIPLOMACY (child epic)
- TCK-20260619-E53C-WAR (child epic)
- TCK-20260619-E53D-HISTORY (child epic)

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § A
- `docs/plans/long_term_development_roadmap.md` § Epic 5.3
- `docs/mechanics/04_strategic_cognition.md` (faction directive scoring)
- `docs/mechanics/02_combat_laws.md` (siege combat formula)
- `docs/mechanics/05_world_evolution.md` (faction-driven evolution)
- `docs/mechanics/regional_sovereignty.md` (faction ownership transfer)
- `docs/engine/governance_logic.md` (FactionDecisionPhase insertion)
- `docs/systems/grand_strategy.md` (scope reference only — archive after Phase A)
- `docs/parity_ledger/world_dynamics.yaml` (faction/political entries)
- `docs/parity_ledger/substrate.yaml` (FactionState persistence)
- New doc: `docs/systems/faction_contract.md` (V2 contract — create in Phase D)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260619-E53-FACTION-DIPLOMACY/`

## Related Code Areas
- `src/content_semantics/faction.py` (catalog data — faction IDs only)
- `src/core/enums.py:L15` (Faction enum)
- `src/engine/policy.py:L10` (GovernorPolicy — governance phase insertion)
- `src/core/state.py` (AuthoritativeState — add FactionState field)

## Assumptions / Open Questions
- How many factions in catalog? → Check `src/content_semantics/faction.py` in E53A
- Does GovernorPolicy support new phases? → Check insertion pattern in E53A before implementing

## Implementation Notes
XL epic. Scope Phase A first (faction as agent) as a child epic, get it done and tested before touching Phase B. Each child epic should be implementable independently without Phase C or D being in progress. Phase D is the cheapest (NarrativeLedger wire-up) and can be threaded in during Phase B.

**Critical:** Do not port legacy `grand_strategy.md` semantics. Build `FactionState` as a V2 typed durable model from scratch. Each child epic (E53A–E53D) will be decomposed into standard tickets at implementation time.

## Test Summary
Per child epic. Key test files:
- `tests/unit/faction/test_faction_state.py` (Phase A)
- `tests/unit/faction/test_diplomacy.py` (Phase B)
- `tests/integration/scenarios/test_faction_campaign.py` (Phase C–D)

## Files Changed
- `tickets/todos/TCK-20260619-E53A-FACTION-AGENT.md`
- `tickets/todos/TCK-20260619-E53B-DIPLOMACY.md`
- `tickets/todos/TCK-20260619-E53C-WAR.md`
- `tickets/todos/TCK-20260619-E53D-HISTORY.md`
- `staging_artifacts/TCK-20260619-E53-FACTION-DIPLOMACY/investigation.md`
- `staging_artifacts/TCK-20260619-E53-FACTION-DIPLOMACY/plan.md`
- `staging_artifacts/TCK-20260619-E53-FACTION-DIPLOMACY/test_plan.md`

## Completion Summary
EPIC_SCOPED. Staged 4 child epics (E53A–E53D): Faction as Agent → Diplomacy → Territorial War → History Integration. E53 is XL — each child is itself an epic to be decomposed into standard tickets at implementation time. Critical constraint preserved: do NOT port grand_strategy.md; build FactionState fresh against V2. Staging artifacts written.
