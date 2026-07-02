---
status: epic_scoped
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53D-HISTORY
phase: scoped
date: 2026-06-22
tags: [faction, history-integration, narrative-ledger, chronicle, grand-strategy-archive, epic, phase-5]
---

# TCK-20260619-E53D-HISTORY

## Title
Epic 5.3D · Faction History Integration (child epic — S)

## Status
EPIC_SCOPED

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
- `WAR_DECLARED` (significance=0.95), `SIEGE_BEGINS` (0.8), `TERRITORY_TRANSFERRED` (0.85*)
- `ALLIANCE_FORMED` (0.8), `PEACE_TREATY` (0.75), `BETRAYAL` (0.85)

*Note: TERRITORY_TRANSFERRED significance is 0.85 (from E53Cc, the implementing ticket), not 0.9 as originally estimated in this epic spec. E53Cc is authoritative.

Ensure `ChronicleNamer` (E51C) has templates for faction events:
- `war_declared` → `"The {source_faction} War against {target_faction}"`
- `territory_transferred` → `"The Conquest of {region_name}"`
- `alliance_formed` → `"The {source_faction}–{target_faction} Alliance"`

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

### Parent
- TCK-20260619-E53-FACTION-DIPLOMACY (parent epic)

### Required By This Epic
- TCK-20260619-E53C-WAR (required for territorial events)
- TCK-20260619-E51C-NAMING (ChronicleNamer templates — already DONE; E53Da extends its output file)

### Child Tickets (scoped 2026-06-22)
- TCK-20260619-E53Da-SIGNIFICANCE-NAMING — EventSignificanceScorer + ChronicleNamer fix (lowercase keys, dual-faction subject_id, 6 event types); parity SOC-FAC-001..006
- TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER — WorldEvent emission for SIEGE_BEGINS and BETRAYAL; CampaignOrchestrator harvesting
- TCK-20260619-E53Dc-COMPILER-INTEGRATION — ChronicleCompiler faction event integration tests (test_faction_war_declared_event_in_narrative_ledger, test_chronicle_names_the_war, test_chronicle_names_territory_transfer)
- TCK-20260619-E53Dd-DOC-ARCHIVE — grand_strategy.md archive + V2 faction_contract.md + knowledge-index-update + test_grand_strategy_doc_archived

### Dependency Order
```
E53Bd (existing) → E53Da
E53Cc (existing) → E53Da
E53Cb (existing) → E53Db
E53Bc (existing) → E53Db
E53Da + E53Db → E53Dc
E53Dc → E53Dd (preferred; can run in parallel with care)
```

## Related Docs
- `docs/systems/faction_contract.md` (new V2 contract — created in E53Dd)
- `docs/parity_ledger/social_narrative.yaml` (SOC-FAC-001..006 — added in E53Da)
- `docs/parity_ledger/substrate.yaml` (WAR-TERR-001 — added in E53Cc)
- `stored_artifacts/TCK-20260619-E53D-HISTORY/investigation.md`

## Related Code Areas
- `src/domains/chronicle/significance.py` (BASE_SIGNIFICANCE — E53Da)
- `src/domains/chronicle/naming.py` (TEMPLATES, ERA_NAMES, name_milestone() — E53Da)
- `src/domains/chronicle/compiler.py` (faction_names/region_names params — E53Dc)
- `src/domains/world_emergence/schema.py` (SIEGE_BEGINS, BETRAYAL constants — E53Db)
- `src/engine/military_conflict.py` (SIEGE_BEGINS emission — E53Db)
- `src/domains/faction/diplomatic_action_handler.py` (BETRAYAL emission — E53Db)
- `docs/systems/grand_strategy.md` (archive to docs/archive/ — E53Dd)
- `docs/systems/faction_contract.md` (new — E53Dd)

## Assumptions / Open Questions
- TERRITORY_TRANSFERRED significance: 0.85 from E53Cc (authoritative), not 0.9 from epic spec.
- E51C naming.py uppercase keys (WAR_DECLARED etc.) are a bug that E53Da must fix — no existing emitter uses those keys so it is safe to rename.
- E53Db must verify DiplomaticActionHandler file path from E53Bb's implementation before writing BETRAYAL emission code.

## Implementation Notes
- Scoped into 4 child standard tickets: E53Da (significance+naming), E53Db (siege/betrayal ledger), E53Dc (integration tests), E53Dd (doc archive).
- Key finding: naming.py already has uppercase template keys that must be lowercased to match E53Bd event_type strings. Significance scorer entirely missing faction event types.
- ChronicleNamer.name_milestone() must be extended to handle dual-faction "factionA:factionB" subject_id and region_id subject_id patterns.

## Test Summary
```bash
pytest tests/unit/chronicle/test_faction_chronicle.py -x -v
pytest tests/unit/docs/test_doc_archive.py -x -v
```

## Files Changed
- `tickets/inprogress/TCK-20260619-E53D-HISTORY.md` → `tickets/done/TCK-20260619-E53D-HISTORY.md`
- `tickets/todos/TCK-20260619-E53Da-SIGNIFICANCE-NAMING.md` (new)
- `tickets/todos/TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER.md` (new)
- `tickets/todos/TCK-20260619-E53Dc-COMPILER-INTEGRATION.md` (new)
- `tickets/todos/TCK-20260619-E53Dd-DOC-ARCHIVE.md` (new)
- `staging_artifacts/TCK-20260619-E53D-HISTORY/investigation.md` (new → stored_artifacts)

## Completion Summary
Scoped 2026-06-22. Produced 4 child standard tickets (E53Da–E53Dd) covering: (1) significance scorer + namer template fix, (2) siege/betrayal ledger wiring, (3) ChronicleCompiler integration tests, (4) grand_strategy doc archive + V2 faction_contract.md. Key finding: naming.py TEMPLATES has uppercase keys but E53Bd will emit lowercase event_type strings — this mismatch is the primary gap E53Da must fix. Significance scorer entirely missing all 6 faction event types.
