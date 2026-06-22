---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Da-SIGNIFICANCE-NAMING
phase: done
date: 2026-06-22
tags: [faction, chronicle, significance, naming, narrative-ledger, phase-5]
---

# TCK-20260619-E53Da-SIGNIFICANCE-NAMING

## Title
Epic 5.3Da · Chronicle Faction Event Significance + Namer Template Fix

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`EventSignificanceScorer` currently has no faction war/diplomatic event types in `BASE_SIGNIFICANCE`, so all faction events score 0.1 (below `CHRONICLE_THRESHOLD=0.5`) and are silently excluded from the chronicle. `ChronicleNamer.TEMPLATES` has uppercase keys (`WAR_DECLARED`) but E53Bd emits lowercase `event_type` strings (`war_declared`), causing a key-miss fallback. This ticket fixes both gaps and upgrades the war/alliance naming templates to use the dual-faction `subject_id` format.

**Requires:** TCK-20260619-E53Bd-LEDGER-WIRING (so the event_type strings being fixed here are confirmed); TCK-20260619-E51A-SIGNIFICANCE and TCK-20260619-E51C-NAMING (already DONE — modifying their output files)

## Scope

### 1. `src/domains/chronicle/significance.py` — add faction event types to `BASE_SIGNIFICANCE`

Add 6 entries to the `BASE_SIGNIFICANCE` dict (lowercase keys to match E53Bd emission):

```python
# Faction war / diplomatic events (E53D)
"war_declared":           0.95,
"siege_begins":           0.80,
"territory_transferred":  0.85,
"alliance_formed":        0.80,
"peace_treaty":           0.75,
"betrayal":               0.85,
```

No other changes to `significance.py`.

### 2. `src/domains/chronicle/naming.py` — fix template key case + add missing templates

**2a. Rename uppercase keys to lowercase** in `TEMPLATES` dict:
- `"WAR_DECLARED"` → `"war_declared"`
- `"TERRITORY_TRANSFERRED"` → `"territory_transferred"`
- `"ALLIANCE_FORMED"` → `"alliance_formed"`

**2b. Upgrade war/alliance templates** to dual-faction format:
```python
"war_declared":          "The {source_faction} War against {target_faction}",
"territory_transferred": "The Conquest of {region_name}",
"alliance_formed":       "The {source_faction}–{target_faction} Alliance",
```

**2c. Add missing faction templates:**
```python
"peace_treaty": "The Peace of {source_faction} and {target_faction}",
"betrayal":     "The Betrayal of {source_faction} by {target_faction}",
"siege_begins": "The Siege of {region_name}",
```

**2d. Add era names for faction-dominated eras** to `ERA_NAMES`:
```python
"war_declared":          "The Age of War",
"alliance_formed":       "The Age of Alliances",
"territory_transferred": "The Age of Conquest",
```

**2e. Extend `name_milestone()` to handle dual-faction subject_id**

The `subject_id` for faction events uses `"factionA:factionB"` (alphabetically sorted, colon-separated). For region events (`siege_begins`, `territory_transferred`) the `subject_id` is the `region_id` string and the payload carries `attacker`/`defender` faction IDs.

Extend `name_milestone()` signature:

```python
@staticmethod
def name_milestone(
    entry: NarrativeLedgerEntry,
    entity_names: dict[int, str],
    faction_names: dict[str, str] | None = None,
    region_names: dict[str, str] | None = None,
) -> str:
```

Resolution logic (added before template.format() call):
- If `":"` in `entry.subject_id`: split on first `":"` → `source_id, target_id`; resolve each via `faction_names.get(x, x)` → `source_faction`, `target_faction`
- Else if template uses `{region_name}`: resolve `region_names.get(entry.subject_id, entry.subject_id)` → `region_name`
- Else: existing entity int-cast resolution (unchanged)

`template.format()` call receives all of: `subject`, `source_faction`, `target_faction`, `region_name`, `tick` — extras are silently ignored by Python's str.format_map or via `**kwargs`; use a dict approach:

```python
fmt_vars = dict(
    subject=subject,
    source_faction=source_faction,
    target_faction=target_faction,
    region_name=region_name,
    tick=entry.tick,
)
return template.format(**fmt_vars)
```

### 3. `docs/parity_ledger/social_narrative.yaml` — add 6 parity entries

Add entries `SOC-FAC-001` through `SOC-FAC-006` for each faction event type:
- `id: SOC-FAC-001`, `text: "war_declared events score 0.95 in EventSignificanceScorer"`, `status: verified`, `priority: P1`
- `id: SOC-FAC-002`, `text: "alliance_formed events score 0.80 in EventSignificanceScorer"`, `status: verified`, `priority: P1`
- `id: SOC-FAC-003`, `text: "peace_treaty events score 0.75 in EventSignificanceScorer"`, `status: verified`, `priority: P1`
- `id: SOC-FAC-004`, `text: "betrayal events score 0.85 in EventSignificanceScorer"`, `status: verified`, `priority: P1`
- `id: SOC-FAC-005`, `text: "territory_transferred events score 0.85 in EventSignificanceScorer"`, `status: verified`, `priority: P1`
- `id: SOC-FAC-006`, `text: "siege_begins events score 0.80 in EventSignificanceScorer"`, `status: verified`, `priority: P1`

Each entry requires `v2_evidence` pointing to `src/domains/chronicle/significance.py` and `test_path` pointing to the test below.

## Out of Scope
- SIEGE_BEGINS and BETRAYAL NarrativeLedger wiring (E53Db — this ticket only registers them in the scorer/namer)
- End-to-end ChronicleCompiler integration test (E53Dc)
- Doc archive (E53Dd)
- Any changes to `ChronicleGrouper`, `ChronicleRenderer`, or `ChronicleCompiler`

## Acceptance Criteria
- `EventSignificanceScorer.score(entry)` returns ≥ 0.9 for `event_type="war_declared"` — entry passes `CHRONICLE_THRESHOLD`
- `EventSignificanceScorer.score(entry)` returns 0.75 for `event_type="peace_treaty"`
- `EventSignificanceScorer.score(entry)` returns 0.85 for `event_type="territory_transferred"`
- `ChronicleNamer.name_milestone(entry, entity_names={})` with `event_type="war_declared"`, `subject_id="ALPHA:BETA"` returns `"The ALPHA War against BETA"` (with faction_names fallback to raw ID)
- `ChronicleNamer.name_milestone(entry, entity_names={})` with `event_type="alliance_formed"`, `subject_id="ALPHA:BETA"` returns `"The ALPHA–BETA Alliance"`
- `ChronicleNamer.name_milestone(entry, entity_names={})` with `event_type="territory_transferred"`, `subject_id="border_region"` returns `"The Conquest of border_region"`
- `test_faction_war_declared_event_in_narrative_ledger` passes (significance ≥ 0.9, from E53D AC)
- No regressions in existing chronicle unit tests (`tests/unit/chronicle/`)

## Related Tickets
- TCK-20260619-E53D-HISTORY (parent epic)
- TCK-20260619-E53Bd-LEDGER-WIRING (required — establishes lowercase event_type strings)
- TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER (blocked on this)
- TCK-20260619-E53Dc-COMPILER-INTEGRATION (blocked on this)
- TCK-20260619-E51A-SIGNIFICANCE (extending its output file)
- TCK-20260619-E51C-NAMING (extending its output file)

## Related Docs
- `docs/simulation/domains/chronicle_contract.md` (Significance Scoring Formula, Naming sections)
- `docs/parity_ledger/social_narrative.yaml` (add SOC-FAC-001..006)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md` (E53Bd significance values)
- `stored_artifacts/TCK-20260619-E53C-WAR/investigation.md` (territory_transferred significance 0.85)

## Related Code Areas
- `src/domains/chronicle/significance.py` (BASE_SIGNIFICANCE dict)
- `src/domains/chronicle/naming.py` (TEMPLATES dict, ERA_NAMES dict, name_milestone())
- `docs/parity_ledger/social_narrative.yaml`
- `tests/unit/chronicle/test_significance.py` (add faction event tests)
- `tests/unit/chronicle/test_naming.py` (add faction naming tests)

## Assumptions / Open Questions
- The existing `tests/unit/chronicle/` test files exist and test the pipeline in isolation; verify filenames before creating new test files.
- `subject_id` for `siege_begins` and `territory_transferred` is the `region_id` string (not a dual-faction colon-pair); confirm from E53Cb/E53Cc implementation when resolving.
- `template.format(**fmt_vars)` with extra keys raises `KeyError` only if the template string uses an unknown key — using `str.format_map` with a defaultdict or pre-filtering fmt_vars is safer; prefer `str.format_map(collections.defaultdict(str, fmt_vars))` to avoid KeyError on templates with unexpected fields.

## Implementation Notes
- Added 6 faction event types to BASE_SIGNIFICANCE (war_declared=0.95, siege_begins=0.80, territory_transferred=0.85, alliance_formed=0.80, peace_treaty=0.75, betrayal=0.85).
- Renamed TEMPLATES uppercase keys (WAR_DECLARED→war_declared, TERRITORY_TRANSFERRED→territory_transferred, ALLIANCE_FORMED→alliance_formed) to match E53Bd lowercase emission. Safe: no code path emits uppercase event_type strings.
- Upgraded dual-faction templates to use {source_faction}/{target_faction}; added peace_treaty, betrayal, siege_begins templates.
- Added ERA_NAMES: war_declared→"The Age of War", alliance_formed→"The Age of Alliances", territory_transferred→"The Age of Conquest".
- Extended name_milestone() with faction_names/region_names optional params; switched to format_map(defaultdict(str)) to avoid KeyError on templates with unknown keys.
- Updated TC-14 in test_chronicle_compiler.py to use lowercase template keys and dual-faction/region expected values.
- Created tests/unit/chronicle/test_significance.py (9 tests) and tests/unit/chronicle/test_naming.py (15 tests).
- Updated SOC-CHRON-001 and SOC-CHRON-003 in social_narrative.yaml; added SOC-FAC-001..006.
- territory_transferred significance is 0.85 (from E53Cc, implementing ticket), not 0.9 (epic spec approximation).

## Test Summary
```bash
pytest tests/unit/chronicle/test_significance.py -x -v
pytest tests/unit/chronicle/test_naming.py -x -v
pytest tests/unit/chronicle/ -x -v
```

## Files Changed
- src/domains/chronicle/significance.py — added 6 faction event types to BASE_SIGNIFICANCE
- src/domains/chronicle/naming.py — fixed TEMPLATES case, added dual-faction/region templates, ERA_NAMES, extended name_milestone() signature with faction_names/region_names, switched to format_map(defaultdict)
- tests/unit/chronicle/test_chronicle_compiler.py — updated TC-14 for lowercase keys and faction/region cases
- tests/unit/chronicle/test_significance.py (new) — 9 tests for faction significance values
- tests/unit/chronicle/test_naming.py (new) — 15 tests for faction naming templates
- docs/parity_ledger/social_narrative.yaml — updated SOC-CHRON-001 and SOC-CHRON-003; added SOC-FAC-001..006

## Completion Summary
Added 6 faction event types (war_declared, siege_begins, territory_transferred, alliance_formed, peace_treaty, betrayal) to EventSignificanceScorer.BASE_SIGNIFICANCE; fixed TEMPLATES uppercase→lowercase keys to match E53Bd lowercase emission; upgraded name_milestone() with dual-faction colon-pair resolution and region_names support; 51 tests passing.
