---
ticket_id: TCK-20260619-E32B-CAMPAIGN-STATE
phase: test_plan
date: 2026-06-21
---

# Test Plan: CampaignState Data Model

## Regression Surface (existing tests that must pass)

These tests must pass without modification after E32B — they cover the campaign domain
that E32B adds to but does not change.

| Test file | Coverage |
|---|---|
| `tests/integration/campaigns/test_phase9_campaign_runner.py` | `SimulationAnalysisRunner` end-to-end runs (5 tests) |
| `tests/integration/campaigns/test_phase9_life_arc_campaigns.py` | Life arc classification in full campaign runs (2 tests) |
| `tests/perf/test_phase9_campaign_semantic_budget.py` | Campaign semantic budget gate (1 test) |
| `tests/unit/campaigns/test_phase9_campaign_spec.py` | `CampaignSpecLoader` parsing |
| `tests/unit/campaigns/test_phase9_behavior_change_proof_detector.py` | `BehaviorChangeProofDetector` |
| `tests/unit/campaigns/test_phase9_forbidden_behavior_detector.py` | `ForbiddenBehaviorDetector` |
| `tests/unit/campaigns/test_phase9_life_arc_classifier.py` | `LifeArcClassifier` |
| `tests/unit/campaigns/test_phase9_route_diversity_analyzer.py` | `RouteDiversityAnalyzer` |
| `tests/unit/campaigns/test_phase9_semantic_campaign_scorecard.py` | `CampaignScorecardEvaluator` |
| `tests/unit/campaigns/test_phase9_campaign_report_generator.py` | Report generation |

Scoped regression command:
```bash
pytest tests/unit/campaigns/ tests/integration/campaigns/ tests/perf/test_phase9_campaign_semantic_budget.py -x -v
```

---

## New Tests Required (per Acceptance Criteria)

### Test file: `tests/unit/campaigns/test_campaign_state.py`

All tests are pure unit tests — no kernel, no `AuthoritativeState`, no simulation run.
All state is constructed directly from typed literals.

---

#### AC-1: `CampaignState` constructs without error

```python
def test_campaign_state_constructs():
    """CampaignState can be constructed from minimal arguments."""
    state = CampaignState(
        campaign_id="test-campaign",
        episode_index=0,
        episode_history=[],
        persistent_entities={},
        persistent_factions={},
        world_timeline=[],
        narrative_ledger=[],
    )
    assert state.campaign_id == "test-campaign"
    assert state.episode_index == 0
    assert state.persistent_entities == {}
```

---

#### AC-2: `CampaignState` serializes to JSON (round-trip)

```python
def test_campaign_state_json_round_trip():
    """CampaignState → to_dict() → JSON → from_dict() produces equivalent object."""
    import json
    ecf = EntityCarryForward(
        entity_id=1,
        level=3,
        xp=120,
        equipment={"slots": {"MAIN_HAND": "sword_iron"}, "durability": {"MAIN_HAND": 0.9}},
        reputation=0.8,   # or dict — depends on OQ-1 resolution
        alive=True,
    )
    state = CampaignState(
        campaign_id="test",
        episode_index=1,
        episode_history=[],
        persistent_entities={1: ecf},
        persistent_factions={},
        world_timeline=[],
        narrative_ledger=[],
    )
    raw = json.dumps(state.to_dict(), sort_keys=True)
    restored = CampaignState.from_dict(json.loads(raw))
    assert restored.campaign_id == state.campaign_id
    assert restored.episode_index == state.episode_index
    assert restored.persistent_entities[1].level == 3
    assert restored.persistent_entities[1].xp == 120
```

---

#### AC-3: `EntityCarryForward` includes all required fields

```python
def test_entity_carry_forward_fields():
    """EntityCarryForward has entity_id, level, xp, equipment, reputation, alive."""
    ecf = EntityCarryForward(
        entity_id=42,
        level=5,
        xp=500,
        equipment={"slots": {}, "durability": {}},
        reputation=1.2,
        alive=True,
    )
    assert ecf.entity_id == 42
    assert ecf.level == 5
    assert ecf.xp == 500
    assert ecf.alive is True
```

---

#### AC-4: Dead entities representable (`alive=False`)

```python
def test_entity_carry_forward_dead():
    """Dead entities have alive=False and can be stored in CampaignState."""
    dead = EntityCarryForward(
        entity_id=7,
        level=2,
        xp=50,
        equipment={},
        reputation=0.5,
        alive=False,
    )
    state = CampaignState(
        campaign_id="test",
        episode_index=1,
        episode_history=[],
        persistent_entities={7: dead},
        persistent_factions={},
        world_timeline=[],
        narrative_ledger=[],
    )
    assert state.persistent_entities[7].alive is False
```

---

#### AC-5: Destroyed factions representable (`alive=False`)

```python
def test_faction_carry_forward_destroyed():
    """Destroyed factions have alive=False and can be stored in CampaignState."""
    faction = FactionCarryForward(
        faction_id="iron_guild",
        alive=False,
        tension=0.0,
    )
    state = CampaignState(
        campaign_id="test",
        episode_index=2,
        episode_history=[],
        persistent_entities={},
        persistent_factions={"iron_guild": faction},
        world_timeline=[],
        narrative_ledger=[],
    )
    assert state.persistent_factions["iron_guild"].alive is False
```

---

#### AC-6: `EntityCarryForward` is frozen (immutable)

```python
def test_entity_carry_forward_is_frozen():
    """EntityCarryForward is a frozen dataclass — mutation raises FrozenInstanceError."""
    import dataclasses
    ecf = EntityCarryForward(
        entity_id=1, level=1, xp=0, equipment={}, reputation=1.0, alive=True,
    )
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        ecf.level = 99
```

---

#### AC-7: `FactionCarryForward` is frozen (immutable)

```python
def test_faction_carry_forward_is_frozen():
    """FactionCarryForward is a frozen dataclass."""
    import dataclasses
    fcf = FactionCarryForward(faction_id="test_faction", alive=True, tension=0.3)
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        fcf.tension = 0.9
```

---

#### AC-8: `CampaignState` is mutable (episode accumulation)

```python
def test_campaign_state_is_mutable():
    """CampaignState is a plain (non-frozen) dataclass — episode_index can be advanced."""
    state = CampaignState(
        campaign_id="test", episode_index=0,
        episode_history=[], persistent_entities={},
        persistent_factions={}, world_timeline=[], narrative_ledger=[],
    )
    state.episode_index = 1
    assert state.episode_index == 1
```

---

#### AC-9: `to_dict()` output is JSON-serializable (no enum keys, no non-primitives)

```python
def test_campaign_state_to_dict_is_json_safe():
    """to_dict() output passes json.dumps without TypeError."""
    import json
    ecf = EntityCarryForward(
        entity_id=1, level=3, xp=120,
        equipment={"slots": {"MAIN_HAND": "sword"}, "durability": {"MAIN_HAND": 0.9}},
        reputation=1.0, alive=True,
    )
    state = CampaignState(
        campaign_id="test", episode_index=0,
        episode_history=[], persistent_entities={1: ecf},
        persistent_factions={}, world_timeline=[], narrative_ledger=[],
    )
    raw = json.dumps(state.to_dict())  # must not raise
    assert isinstance(raw, str)
```

---

#### AC-10: Import smoke test

```python
def test_campaign_state_importable():
    """CampaignState and related types are importable from src.domains.campaigns.state."""
    from src.domains.campaigns.state import (
        CampaignState,
        EntityCarryForward,
        FactionCarryForward,
        EpisodeSummary,
        WorldTimelineEntry,
        NarrativeLedgerEntry,
    )
```

---

## Scoped Pytest Commands

```bash
# Run only the new E32B unit tests (fast, no kernel):
pytest tests/unit/campaigns/test_campaign_state.py -x -v

# Run full campaign test surface (regression + new):
pytest tests/unit/campaigns/ tests/integration/campaigns/ \
       tests/perf/test_phase9_campaign_semantic_budget.py -x -v

# Import smoke only:
python3 -c "from src.domains.campaigns.state import CampaignState; print('OK')"
```

---

## Anti-Drift Test Guards

### Guard 1: `CampaignState` must NOT be frozen

If E32B accidentally marks `CampaignState` as `frozen=True`, test AC-8 (mutability) will
fail immediately. This protects against the pattern where a developer applies the repo's
default `@dataclass(frozen=True, slots=True)` to `CampaignState` by reflex.

### Guard 2: `EntityCarryForward` and `FactionCarryForward` MUST be frozen

Tests AC-6 and AC-7 verify this. If they are accidentally made mutable, E32C's extraction
logic could silently mutate a carry-forward snapshot. The frozen constraint must hold.

### Guard 3: JSON round-trip determinism (AC-2)

The round-trip test explicitly uses `json.dumps(state.to_dict(), sort_keys=True)`. If
`to_dict()` produces non-deterministic ordering (e.g., unsorted dict keys), this test
will not catch it directly — but any checkpoint-restore test in E32C that compares
outputs will. Consider adding an explicit key-order assertion in AC-2 if needed.

### Guard 4: No imports of kernel or authoritative pipeline in `state.py`

`src/domains/campaigns/state.py` must not import anything from `src/engine/` or
`src/core/state.py` — it is a pure data model. Add a test guard:

```python
def test_campaign_state_module_has_no_engine_imports():
    """state.py must not import from src.engine or src.core.state."""
    import ast, pathlib
    src = pathlib.Path("src/domains/campaigns/state.py").read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, 'module', '') or ''
            assert not module.startswith('src.engine'), \
                f"Illegal engine import in state.py: {module}"
            assert module != 'src.core.state', \
                f"Illegal core state import in state.py: {module}"
```

### Guard 5: `NarrativeLedgerEntry` stub only

The `narrative_ledger: list[NarrativeLedgerEntry]` field exists in `CampaignState` but
`NarrativeLedgerEntry` must be defined as a minimal stub in E32B (fields TBD in E32D).
Test AC-10 (import smoke) will confirm the type is importable. Any test that attempts to
populate `narrative_ledger` with real data in E32B's test file should be rejected as
out-of-scope — E32D owns that behavior.
