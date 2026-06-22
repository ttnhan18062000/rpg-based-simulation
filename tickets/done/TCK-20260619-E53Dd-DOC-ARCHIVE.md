---
status: done
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Dd-DOC-ARCHIVE
phase: done
date: 2026-06-23
tags: [faction, docs, archive, faction-contract, grand-strategy, knowledge-index, phase-5]
---

# TCK-20260619-E53Dd-DOC-ARCHIVE

## Title
Epic 5.3Dd · Grand Strategy Doc Archive + V2 Faction Contract

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Archive the legacy `docs/systems/grand_strategy.md` (V1 StrategySystem — not V2 architecture) and create a new authoritative `docs/systems/faction_contract.md` that consolidates V2 FactionState model, FactionDecisionPhase, DiplomaticStateMachine, territorial rules, siege mechanics, and NarrativeLedger significance values into one reference. Regenerate the knowledge index and validate the `test_grand_strategy_doc_archived` acceptance criterion from the E53D epic.

**Requires:** TCK-20260619-E53Dc-COMPILER-INTEGRATION (the pipeline must be verified before the contract doc can be finalized with accurate values). Can run in parallel with E53Dc if doc author is careful to mark chronicle sections as "pending verification."

## Scope

### 1. Archive legacy doc

```bash
mkdir -p docs/archive/
mv docs/systems/grand_strategy.md docs/archive/grand_strategy_v1.md
```

Add a header deprecation notice to the top of `docs/archive/grand_strategy_v1.md`:

```markdown
> **ARCHIVED (2026-06-22):** This document describes the V1 StrategySystem (`src/systems/strategy_system.py`, `src/core/world_state.py`) which was replaced by the V2 Faction & Diplomacy System (Epic 5.3). See `docs/systems/faction_contract.md` for the authoritative V2 reference.
```

### 2. Create `docs/systems/faction_contract.md`

New authoritative V2 contract document. Required sections:

#### 2a. Overview
- Purpose: macroscopic faction simulation via V2 FactionState on AuthoritativeState
- Replaces: V1 StrategySystem (archived at `docs/archive/grand_strategy_v1.md`)
- Source files: `src/core/state.py` (FactionState), `src/engine/faction_decision.py` (FactionDecisionPhase), `src/domains/faction/diplomatic_state_machine.py`, `src/domains/faction/diplomatic_action_handler.py`, `src/engine/military_conflict.py`

#### 2b. FactionState Model
- All fields from E53Aa (faction_id, name, territory, military_strength, tension_level, diplomatic_relations, etc.)
- Authoritative location: `src/core/state.py`
- AuthoritativeState field: `factions: Dict[str, FactionState]`
- Serialization: frozen Pydantic BaseModel

#### 2c. FactionDecisionPhase
- Sub-phase of TickPhase.INIT; runs after WorldEmergencePhase
- Inputs: AuthoritativeState.factions, recent_world_events
- Outputs: List[FactionDirective] (transient, per-tick)
- Key directives: SEEK_ALLIANCE, SEEK_TRADE, MAINTAIN_TENSION, SEEK_PEACE, BETRAY_ALLY
- Source: E53Ab

#### 2d. DiplomaticStateMachine
- 5 diplomatic states: NEUTRAL, FRIENDLY, ALLIED, HOSTILE, WAR
- Transition rules (from E53Bc):
  - NEUTRAL → FRIENDLY: AllianceProposal accepted
  - FRIENDLY → ALLIED: second AllianceProposal accepted
  - ALLIED → HOSTILE: Betrayal executed
  - HOSTILE → WAR: tension_level ≥ 0.8
  - WAR → NEUTRAL: SEEK_PEACE directive + peace treaty accepted
- Source: `src/domains/faction/diplomatic_state_machine.py`

#### 2e. Military Conflict
- MilitaryConflictPhase: sub-phase after FactionDecisionPhase
- SiegeState: attacker_faction_id, defender_faction_id, siege_progress (0.0–1.0), ticks_active
- siege_progress increments +0.05/tick; transfer at ≥ 1.0
- Territory transfer: WorldUpdate.owner_faction_id_set
- War exhaustion: military_strength drain per active WAR pair
- Source: `src/engine/military_conflict.py`

#### 2f. NarrativeLedger Integration
- Significance values (authoritative):

| event_type | significance | Source ticket |
|---|---|---|
| war_declared | 0.95 | E53Bd |
| alliance_formed | 0.80 | E53Bd |
| peace_treaty | 0.75 | E53Bd |
| territory_transferred | 0.85 | E53Cc |
| siege_begins | 0.80 | E53Db |
| betrayal | 0.85 | E53Db |

- All faction WorldEvents flow through CampaignOrchestrator._advance_state()
- Chronicle threshold: 0.5 (all 6 faction event types exceed this)

#### 2g. Chronicle Integration
- ChronicleNamer templates for faction events (from E53Da)
- faction_names / region_names params on ChronicleCompiler.compile()
- ERA_NAMES faction entries

#### 2h. Parity Ledger References
- `docs/parity_ledger/social_narrative.yaml`: SOC-FAC-001 through SOC-FAC-006
- `docs/parity_ledger/substrate.yaml`: WAR-TERR-001 (territory transfer)

### 3. Validate the `test_grand_strategy_doc_archived` acceptance criterion

After the move:

```bash
# Must exist:
test -f docs/archive/grand_strategy_v1.md && echo "PASS: archive exists"
# Must not exist:
test ! -f docs/systems/grand_strategy.md && echo "PASS: original removed"
```

Write a simple pytest test at `tests/unit/docs/test_doc_archive.py`:
```python
import os

def test_grand_strategy_doc_archived():
    assert os.path.exists("docs/archive/grand_strategy_v1.md"), \
        "grand_strategy_v1.md must exist in docs/archive/"
    assert not os.path.exists("docs/systems/grand_strategy.md"), \
        "docs/systems/grand_strategy.md must not exist after archival"
```

### 4. Knowledge index regeneration

```bash
make knowledge-index-update
```

Run after creating `faction_contract.md` and moving/updating `grand_strategy_v1.md` so the agent context search index reflects the new doc structure.

### 5. Update `docs/REGISTRY.yaml`

Add entry for `docs/systems/faction_contract.md`:
```yaml
- path: docs/systems/faction_contract.md
  layer: strategy
  related_code_areas:
    - src/core/state.py
    - src/engine/faction_decision.py
    - src/domains/faction/
    - src/engine/military_conflict.py
  tags: [faction, diplomacy, war, chronicle, narrative-ledger, v2]
  status: authoritative
```

Update (or remove) the existing registry entry for `docs/systems/grand_strategy.md` to point to the archive path.

Run `make docs-registry` after updating REGISTRY.yaml.

## Out of Scope
- Changing any source code (pure doc/archive operation)
- Creating docs for E53A–E53C systems beyond what is referenced in faction_contract.md (those are in stored_artifacts)
- Regenerating the graphify knowledge graph (graphify update . is only needed after src/ changes; doc-only changes use make knowledge-index-update)

## Acceptance Criteria
- `docs/archive/grand_strategy_v1.md` exists with deprecation header
- `docs/systems/grand_strategy.md` does NOT exist
- `docs/systems/faction_contract.md` exists with all 8 required sections (a–h)
- `test_grand_strategy_doc_archived` passes
- `make knowledge-index-update` runs without error
- `docs/REGISTRY.yaml` updated for new faction_contract.md

## Related Tickets
- TCK-20260619-E53D-HISTORY (parent epic)
- TCK-20260619-E53Dc-COMPILER-INTEGRATION (preferred prerequisite — verify significance values before writing contract)
- TCK-20260619-E53Aa-FACTION-STATE (FactionState fields reference)
- TCK-20260619-E53Ab-DECISION-PHASE (FactionDecisionPhase reference)
- TCK-20260619-E53Bc-STATE-MACHINE (DiplomaticStateMachine reference)
- TCK-20260619-E53Bd-LEDGER-WIRING (NarrativeLedger significance values)
- TCK-20260619-E53Cc-TERRITORY-TRANSFER (territory_transferred significance 0.85)
- TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER (siege_begins/betrayal significance values)

## Related Docs
- `docs/systems/grand_strategy.md` (to archive)
- `docs/parity_ledger/social_narrative.yaml` (faction entries)
- `docs/parity_ledger/substrate.yaml` (WAR-TERR-001)
- `docs/REGISTRY.yaml` (add new entry)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53A-FACTION-AGENT/investigation.md`
- `stored_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md`
- `stored_artifacts/TCK-20260619-E53C-WAR/investigation.md`
- `stored_artifacts/TCK-20260619-E53D-HISTORY/investigation.md`

## Related Code Areas
- `docs/systems/` (faction_contract.md new, grand_strategy.md remove)
- `docs/archive/grand_strategy_v1.md` (new archive location)
- `tests/unit/docs/test_doc_archive.py` (new)
- `docs/REGISTRY.yaml`

## Assumptions / Open Questions
- `docs/REGISTRY.yaml` exists and `make docs-registry` is a valid target — confirm before running.
- `tests/unit/docs/` directory may not exist; create it with `__init__.py` if needed.
- The test_grand_strategy_doc_archived test uses relative paths — it must be run from the repo root. Add a `conftest.py` that sets `os.chdir(repo_root)` if the test directory does not already do this.
- `make knowledge-index-update` target: verify it exists in the Makefile before running; if unavailable, use `python3 tools/knowledge_search.py index` as fallback.

## Implementation Notes
- The deprecation notice in `grand_strategy_v1.md` ensures agents that search for "grand_strategy" via MCP knowledge search will find the archive and be redirected to faction_contract.md.
- faction_contract.md should include a "Last verified" frontmatter field set to today's date and updated when the source implementation changes.
- Do NOT delete grand_strategy.md without first confirming no tests import or reference it by path.

## Test Summary
```bash
pytest tests/unit/docs/test_doc_archive.py -x -v
```

## Files Changed
- `docs/archive/grand_strategy_v1.md` — moved from docs/systems/; added ARCHIVED deprecation header
- `docs/systems/grand_strategy.md` — removed (moved to archive)
- `docs/systems/faction_contract.md` — status updated to AUTHORITATIVE; NarrativeLedger Integration, Chronicle Integration, and updated Parity Ledger sections added (E53Da/E53Db/E53Dc coverage)
- `tests/unit/docs/test_doc_archive.py` — 3 new doc archive tests (new file)
- `tests/unit/docs/__init__.py` — new empty init (new directory)
- `docs/REGISTRY.yaml` — grand_strategy.md entry updated to archive path; faction_contract.md entry added as authoritative
- `.cache/knowledge_index/` — regenerated via `make knowledge-index-update`

## Completion Summary
grand_strategy.md archived at docs/archive/grand_strategy_v1.md with deprecation notice. faction_contract.md promoted to AUTHORITATIVE with E53D chronicle/NarrativeLedger sections. Knowledge index regenerated (8 files re-embedded). 3 archive tests pass.
