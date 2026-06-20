---
status: open
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53D-HISTORY
phase: open
date: 2026-06-20
tags: [faction, history-integration, narrative-ledger, chronicle, grand-strategy-archive, epic, phase-5]
---

# TCK-20260619-E53D-HISTORY

## Title
Epic 5.3D · Faction History Integration (child epic — S)

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
Ensures all faction-level events flow into `NarrativeLedger` with correct significance scores, enabling `ChronicleCompiler` (E51) to name wars and alliances. Also archives the legacy `grand_strategy.md` doc.

**Requires:** TCK-20260619-E53C-WAR (can start during E53B for diplomatic events)

## Scope

Wire faction events to `NarrativeLedger`:
- `WAR_DECLARED` (significance=0.95), `SIEGE_BEGINS` (0.8), `TERRITORY_TRANSFERRED` (0.9)
- `ALLIANCE_FORMED` (0.8), `PEACE_TREATY` (0.75), `BETRAYAL` (0.85)

Ensure `ChronicleNamer` (E51C) has templates for faction events:
- `WAR_DECLARED` → `"The {source_faction} War against {target_faction}"`
- `TERRITORY_TRANSFERRED` → `"The Conquest of {region_name}"`
- `ALLIANCE_FORMED` → `"The {source_faction}–{target_faction} Alliance"`

**Archive docs/systems/grand_strategy.md**:
```bash
mkdir -p docs/archive/
mv docs/systems/grand_strategy.md docs/archive/grand_strategy_v1.md
```
Create `docs/systems/faction_contract.md` (V2 FactionState model, FactionDecisionPhase, diplomatic states, territorial rules, siege mechanics). Run `make knowledge-index-update`.

## Acceptance Criteria
- `test_faction_war_declared_event_in_narrative_ledger` passes (significance ≥ 0.9)
- `test_chronicle_names_the_war` passes (ChronicleCompiler + E51 integration)
- `test_grand_strategy_doc_archived` passes: `docs/archive/grand_strategy_v1.md` exists; `docs/systems/grand_strategy.md` does NOT

## Related Tickets
- TCK-20260619-E53-FACTION-DIPLOMACY (parent epic)
- TCK-20260619-E53C-WAR (required for territorial events)
- TCK-20260619-E51C-NAMING (ChronicleNamer templates — ensure faction event templates are added)

## Related Docs
- `docs/systems/faction_contract.md` (new V2 contract — create on completion)
- `docs/parity_ledger/world_dynamics.yaml` (add faction entries as verified)
- `docs/parity_ledger/substrate.yaml` (FactionState persistence)

## Related Code Areas
- `src/domains/campaigns/state.py` (NarrativeLedger — wire faction events)
- `src/domains/chronicle/naming.py` (add faction event templates)
- `docs/systems/grand_strategy.md` (archive to docs/archive/)

## Test Summary
```bash
pytest tests/unit/faction/test_faction_state.py::test_faction_war_declared_event_in_narrative_ledger -x -v
pytest tests/integration/scenarios/test_faction_campaign.py::test_chronicle_names_the_war -x -v -m slow
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
