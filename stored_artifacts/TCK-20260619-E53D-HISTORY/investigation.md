---
ticket_id: TCK-20260619-E53D-HISTORY
phase: scope
date: 2026-06-22
author: agent
---

# Investigation: TCK-20260619-E53D-HISTORY · Faction History Integration

## What Exists

### Chronicle Pipeline (E51 — fully DONE)

All 5 E51 sub-tickets are DONE. The pipeline is:

```
NarrativeLedger → EventSignificanceScorer → ChronicleGrouper → ChronicleNamer → ChronicleRenderer → ChronicleCompiler → REST API
```

Key files:
- `src/domains/chronicle/significance.py` — `EventSignificanceScorer`, `BASE_SIGNIFICANCE` dict, `CHRONICLE_THRESHOLD=0.5`
- `src/domains/chronicle/naming.py` — `ChronicleNamer`, `TEMPLATES` dict, `ERA_NAMES` dict
- `src/domains/chronicle/grouper.py` — hierarchy dataclasses (Incident/Episode/Era)
- `src/domains/chronicle/renderer.py` — `ChronicleRenderer`, `chronicle.json` schema
- `src/domains/chronicle/compiler.py` — `ChronicleCompiler.compile()` (sole public entry)
- `src/api/routes/chronicle.py` — REST endpoints, `_CHRONICLE_REGISTRY`

### E51C Naming (DONE) — Partial Faction Support

`naming.py` TEMPLATES already contains:
```python
"WAR_DECLARED": "The {subject} War Declaration",
"TERRITORY_TRANSFERRED": "The Fall of {subject}",
"ALLIANCE_FORMED": "The Alliance with {subject}",
```

**Gap:** These template keys use UPPERCASE (legacy names from E51C ticket's early draft). E53Bd wiring uses lowercase event_type strings (`war_declared`, `alliance_formed`, `peace_treaty`). The NarrativeLedger entries emitted by E53Bd will have `event_type="war_declared"` — the current TEMPLATES dict will NOT match them, so they will fall through to the `{subject}` fallback template.

### E51A Significance (DONE) — Missing Faction Events

`significance.py` `BASE_SIGNIFICANCE` dict contains **no faction war/diplomatic event types**. The following are missing:
- `war_declared` (spec: 0.95)
- `siege_begins` (spec: 0.8)
- `territory_transferred` (spec: 0.9 per epic scope, 0.85 per E53Cc — use 0.85 from E53Cc as authoritative)
- `alliance_formed` (spec: 0.8)
- `peace_treaty` (spec: 0.75)
- `betrayal` (spec: 0.85)

Without these entries, faction events score 0.1 (the default fallback) and fail the `CHRONICLE_THRESHOLD=0.5` filter — they never appear in the chronicle.

### E53Bd Ledger Wiring (TODO)

Emits `NarrativeLedgerEntry` with these `event_type` values (lowercase):
- `"war_declared"` — significance=0.95
- `"alliance_formed"` — significance=0.8
- `"peace_treaty"` — significance=0.75

### E53Cc Territory Transfer (TODO)

Emits `NarrativeLedgerEntry` with `event_type="territory_transferred"`, significance=0.85 (from E53Cc scope).

### E53C War Epic (TODO child tickets)

E53Ca, E53Cb, E53Cc, E53Cd are all open. `SIEGE_BEGINS` and `BETRAYAL` are in the E53D epic scope but not yet covered by any E53B or E53C child ticket — they need wiring in E53D.

### Grand Strategy Doc

`docs/systems/grand_strategy.md` exists. It describes legacy V1 StrategySystem (src/systems/strategy_system.py, src/core/world_state.py) which is **not the V2 architecture**. This doc must be archived and a new V2 faction_contract.md must be created. No `docs/archive/` directory exists yet.

### FactionSocialMemory (DONE — E43D)

`TCK-20260619-E43D-FACTION-MEMORY` is DONE. It implemented `FactionSocialMemory` for collective hostility persistence. This is separate from the history/chronicle integration — no conflict.

---

## What's Needed

### Gap 1: Significance Scorer — add faction event types (E53Da)

`EventSignificanceScorer` in `significance.py` must register all 6 faction event types in `BASE_SIGNIFICANCE`. Without this, faction events score 0.1 and are filtered out of the chronicle.

| event_type (lowercase) | significance |
|---|---|
| `war_declared` | 0.95 |
| `siege_begins` | 0.8 |
| `territory_transferred` | 0.85 |
| `alliance_formed` | 0.8 |
| `peace_treaty` | 0.75 |
| `betrayal` | 0.85 |

### Gap 2: Namer — fix template key mismatch + add missing events (E53Da)

`ChronicleNamer.TEMPLATES` has uppercase keys (`WAR_DECLARED`, etc.) but incoming event_type strings are lowercase (`war_declared`, etc.). Must:
1. Rename existing uppercase template keys to lowercase to match E53Bd emission
2. Add missing templates: `peace_treaty`, `betrayal`, `siege_begins`
3. Upgrade `WAR_DECLARED` template to use dual-faction format: `"The {source_faction} War against {target_faction}"` (as per E53D epic scope). This requires updating `name_milestone()` to handle `subject_id` as `"factionA:factionB"` format and extract individual faction names from it.
4. Add `ERA_NAMES` entries for faction-dominated eras (`war_declared` → `"The Age of War"`)

### Gap 3: SIEGE_BEGINS and BETRAYAL event emission (E53Db)

Neither E53Bd nor E53C tickets cover `SIEGE_BEGINS` or `BETRAYAL` WorldEvent emission into the NarrativeLedger. These must be wired in E53D:
- `SIEGE_BEGINS` — emitted by `MilitaryConflictPhase` when `SiegeState` is first created (E53Cb prerequisite); harvested in CampaignOrchestrator as `event_type="siege_begins"`, significance=0.8
- `BETRAYAL` — emitted by `DiplomaticActionHandler.handle(BetrayalDirective)` when a BETRAYAL action executes; harvested as `event_type="betrayal"`, significance=0.85

### Gap 4: ChronicleCompiler integration test for faction events (E53Dc)

No end-to-end test exists verifying that faction events (war_declared, territory_transferred) flow from `NarrativeLedger` all the way through `ChronicleCompiler` and produce named milestones. The E51 tests test the pipeline in isolation. A `test_chronicle_names_the_war` test (from E53D ACs) must be authored as a scenario integration test.

### Gap 5: Grand strategy doc archive + V2 faction_contract.md (E53Dd)

The legacy `docs/systems/grand_strategy.md` documents V1 StrategySystem which is not V2 architecture. Must:
1. Create `docs/archive/` directory
2. Move `docs/systems/grand_strategy.md` → `docs/archive/grand_strategy_v1.md`
3. Create `docs/systems/faction_contract.md` — V2 FactionState model, FactionDecisionPhase, DiplomaticStateMachine, diplomatic states, territorial rules, siege mechanics (consolidates E53A–E53C contracts)
4. Run `make knowledge-index-update`

---

## Key Architectural Decisions

### Decision 1: Template key case — lowercase
E53Bd wires NarrativeLedgerEntry with lowercase event_type strings (`war_declared`, `alliance_formed`, `peace_treaty`). E53Cc uses `territory_transferred`. The E51C TEMPLATES dict used uppercase keys in its original ticket draft but the live `naming.py` code has uppercase keys (`WAR_DECLARED`, etc.). **Resolution:** rename all keys to lowercase in naming.py — this is a bug fix, not a behavior change, since no path currently produces entries with those event types.

### Decision 2: Dual-faction subject_id parsing
E53Bd subject_id for dual-faction events uses `"factionA:factionB"` (alphabetically sorted). `ChronicleNamer.name_milestone()` must be extended to split this on `:` when present and resolve both faction names. A new `faction_names: dict[str, str]` optional parameter will be added (keyed by string faction ID), with fallback to raw string if not provided.

### Decision 3: SIEGE_BEGINS / BETRAYAL scoped into E53Db (not piggybacked on E53Ca/E53Bc)
Adding siege/betrayal NarrativeLedger wiring to already-scoped tickets (E53Ca, E53Bc) would expand their scope post-scoping. These go in a dedicated E53D child ticket.

### Decision 4: Significance values — E53Cc authoritative for TERRITORY_TRANSFERRED
The E53D epic spec says 0.9, E53Cc scope says 0.85. E53Cc is the implementing ticket and is authoritative — use 0.85. Record this as implementation note.

### Decision 5: faction_contract.md as a synthesis doc
Rather than creating a thin stub, `faction_contract.md` should consolidate the contracts established by E53A, E53B, E53C into a single authoritative reference (FactionState fields, DiplomaticStateMachine rules, MilitaryConflictPhase behavior, significance values). This avoids agents needing to read 3 stored artifact investigations.

### Decision 6: Parity ledger entries
Add 6 new parity entries to `docs/parity_ledger/social_narrative.yaml` (chronicle path) covering faction event significance and naming. Use ID prefix `SOC-FAC-`.

---

## Dependency Map for Child Tickets

```
[existing] E53Bd (LEDGER-WIRING) ──► E53Da (SIGNIFICANCE + NAMING FIX)
[existing] E53Cc (TERRITORY-TRANSFER) ──►┘
[existing] E53Cb (SIEGE-MODEL) ──► E53Db (SIEGE/BETRAYAL LEDGER)
[existing] E53Bc (STATE-MACHINE) ──►┘
E53Da + E53Db ──► E53Dc (COMPILER INTEGRATION TEST)
E53Dc ──► E53Dd (DOC ARCHIVE + faction_contract.md)
```

E53Da can start as soon as E53Bd is done. E53Db can start as soon as E53Cb and E53Bc are done. E53Dc requires E53Da + E53Db. E53Dd can proceed independently of E53Dc (no code dependency) but logically belongs after the pipeline is verified.
