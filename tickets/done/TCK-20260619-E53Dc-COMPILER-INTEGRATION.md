---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Dc-COMPILER-INTEGRATION
phase: done
date: 2026-06-23
tags: [faction, chronicle, integration-test, compiler, named-milestones, phase-5]
---

# TCK-20260619-E53Dc-COMPILER-INTEGRATION

## Title
Epic 5.3Dc · ChronicleCompiler Faction Event Integration Tests

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Author two integration tests that validate faction events flow end-to-end from `NarrativeLedger` through `ChronicleCompiler` and produce named milestones. The existing E51 tests exercise the chronicle pipeline in isolation with generic event types. This ticket adds tests using faction-specific event types (`war_declared`, `territory_transferred`) to verify the full pipeline with significance scoring and naming together.

**Requires:** TCK-20260619-E53Da-SIGNIFICANCE-NAMING (scorer and namer must support faction events); TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER (siege_begins entries must be producible — needed for the second AC test)

## Scope

### 1. Test file: `tests/unit/chronicle/test_faction_chronicle.py` (new)

#### Test 1: `test_faction_war_declared_event_in_narrative_ledger`

Verifies the significance threshold: a `war_declared` entry scores ≥ 0.9 and is `chronicle_worthy`.

```python
def test_faction_war_declared_event_in_narrative_ledger():
    entry = NarrativeLedgerEntry(
        event_type="war_declared",
        significance=0.95,
        subject_id="ALPHA:BETA",
        tick=10,
        episode=0,
        payload={"from_faction": "ALPHA", "to_faction": "BETA"},
        entry_id="0:10:war_declared:ALPHA:BETA",
    )
    assert EventSignificanceScorer.score(entry) >= 0.9
    assert EventSignificanceScorer.is_chronicle_worthy(entry) is True
```

#### Test 2: `test_chronicle_names_the_war`

Verifies the full `ChronicleCompiler` pipeline produces a named milestone for a `war_declared` event.

Setup:
- Construct a `CampaignState` (or compatible `NarrativeLedger` stub) containing exactly one `NarrativeLedgerEntry` with `event_type="war_declared"`, `significance=0.95`, `subject_id="ALPHA:BETA"`, `tick=5`, `episode=0`
- Call `ChronicleCompiler.compile(campaign_id="test_war", ledger=ledger, entity_names={}, faction_names={"ALPHA": "Alpha Kingdom", "BETA": "Beta Empire"}, region_names={}, output_dir=tmp_path)`
- Load `(tmp_path / "chronicle.json")` and assert:
  - `len(data["named_milestones"]) >= 1`
  - The first named milestone's `"name"` equals `"The Alpha Kingdom War against Beta Empire"`
  - The milestone's `"event_type"` equals `"war_declared"`
  - The milestone's `"significance"` equals `0.95`

#### Test 3: `test_chronicle_names_territory_transfer`

Verifies `territory_transferred` events produce a named milestone.

Setup similar to Test 2:
- One `NarrativeLedgerEntry` with `event_type="territory_transferred"`, `significance=0.85`, `subject_id="border_region"`, `tick=20`, `episode=0`
- Compile with `region_names={"border_region": "The Border Wastes"}`
- Assert named milestone name equals `"The Conquest of The Border Wastes"`

#### Test 4: `test_chronicle_era_named_age_of_war` (optional — add if ERA_NAMES supports war_declared)

Verifies era naming for war-dominated eras:
- Multiple `war_declared` entries across 3+ episodes → `ChronicleGrouper` produces an era where `dominant_event_type="war_declared"` → `ChronicleNamer.name_era()` returns `"The Age of War"`

### 2. `ChronicleCompiler.compile()` interface — verify `faction_names` and `region_names` parameters

If `ChronicleCompiler.compile()` does not already accept `faction_names: dict[str, str]` and `region_names: dict[str, str]` keyword arguments, add them (defaulting to `{}`) and thread them through to `ChronicleNamer.name_milestone()`. No other changes to the compiler.

Verify the current signature in `src/domains/chronicle/compiler.py` before modifying.

### 3. Parity ledger update — `docs/parity_ledger/social_narrative.yaml`

Update parity entries `SOC-FAC-001`..`SOC-FAC-005` (added in E53Da) with `test_path` pointing to `tests/unit/chronicle/test_faction_chronicle.py::test_faction_war_declared_event_in_narrative_ledger` (and others as appropriate). Change status to `verified` once tests pass.

## Out of Scope
- Scenario-level simulation integration tests (those live in `tests/integration/scenarios/` and require the full faction pipeline from E53A–E53C; they are out of scope here — this ticket uses direct `NarrativeLedger` construction)
- SIEGE_BEGINS / BETRAYAL naming tests (those can be added to this file as a follow-on once E53Db is done, or as a separate test PR; not required for ACs here)
- REST API tests for faction milestones (already covered by E51E's existing test suite pattern — extend `tests/api/test_chronicle_api.py` only if needed)

## Acceptance Criteria
- `test_faction_war_declared_event_in_narrative_ledger` passes (significance ≥ 0.9, is_chronicle_worthy=True)
- `test_chronicle_names_the_war` passes: ChronicleCompiler produces `named_milestone.name == "The Alpha Kingdom War against Beta Empire"`
- `test_chronicle_names_territory_transfer` passes: named milestone name == `"The Conquest of The Border Wastes"`
- No regressions in `tests/unit/chronicle/` (all existing tests still pass)

## Related Tickets
- TCK-20260619-E53D-HISTORY (parent epic)
- TCK-20260619-E53Da-SIGNIFICANCE-NAMING (required — significance + naming must be correct)
- TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER (required for full 6-event coverage — but Test 1–3 ACs above only need E53Da)
- TCK-20260619-E53Dd-DOC-ARCHIVE (blocked on this for verification step)

## Related Docs
- `docs/simulation/domains/chronicle_contract.md` (full pipeline spec, chronicle.json schema, named_milestones format)
- `docs/parity_ledger/social_narrative.yaml`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53B-DIPLOMACY/investigation.md`
- `stored_artifacts/TCK-20260619-E53C-WAR/investigation.md`

## Related Code Areas
- `src/domains/chronicle/compiler.py` (add faction_names/region_names params if absent)
- `src/domains/chronicle/naming.py` (name_milestone — verify dual-faction subject_id resolution)
- `src/domains/chronicle/significance.py` (verify faction event types registered)
- `src/domains/campaigns/state.py` (NarrativeLedgerEntry — read constructor signature)
- `tests/unit/chronicle/test_faction_chronicle.py` (new)
- `docs/parity_ledger/social_narrative.yaml`

## Assumptions / Open Questions
- `ChronicleCompiler.compile()` current signature: read `src/domains/chronicle/compiler.py` to determine if `faction_names` / `region_names` params must be added or are already present.
- `NarrativeLedgerEntry` constructor: verify field names (`event_type`, `significance`, `subject_id`, `tick`, `episode`, `payload`, `entry_id`) from `src/domains/campaigns/state.py` before writing test fixtures.
- If `ChronicleCompiler` writes to files (output_dir pattern), tests should use `tmp_path` pytest fixture; if it returns in-memory data, adjust accordingly.
- ERA_NAMES test (Test 4) requires ≥ 3 episodes of war-dominant events — determine the minimum ledger size needed for `ERA_EPISODE_MIN=3` grouper threshold before implementing.

## Implementation Notes
- Keep tests deterministic and self-contained: construct `NarrativeLedgerEntry` objects directly, do not depend on running the full faction simulation pipeline.
- The `test_chronicle_names_the_war` test is named in the E53D epic acceptance criteria — it must pass exactly as named.
- If `ChronicleCompiler.compile()` already has a `faction_names` parameter from a prior ticket's implementation, do not add it again; just verify and use it.

## Test Summary
```bash
pytest tests/unit/chronicle/test_faction_chronicle.py -x -v
pytest tests/unit/chronicle/ -x -v
```

## Files Changed
- `src/domains/chronicle/compiler.py` — added `faction_names` and `region_names` params to `compile()`; threaded to renderer calls
- `src/domains/chronicle/renderer.py` — added `faction_names`/`region_names` params to `render_markdown()` and `render_json()`; passed to `ChronicleNamer.name_milestone()`
- `tests/unit/chronicle/test_faction_chronicle.py` — 5 new integration tests (new file)
- `docs/parity_ledger/social_narrative.yaml` — added SOC-CHRON-006

## Completion Summary
ChronicleCompiler now resolves faction and region display names in named milestones via optional `faction_names`/`region_names` params threaded through the compiler → renderer → namer chain. 5 new integration tests; 56 chronicle tests passing, zero regressions.
