---
ticket_id: TCK-20260619-E53Ab-DECISION-PHASE
phase: investigate
date: 2026-06-22
artifact_type: test_plan
---

# Test Plan — TCK-20260619-E53Ab-DECISION-PHASE (FactionDecisionPhase + FactionDirective)

## Regression Surface

The following existing tests must continue to pass after E53Ab is implemented. Do not run the full suite — scope to these files:

| File | What it covers | Why at risk |
|---|---|---|
| `tests/unit/faction/test_faction_state.py` | FactionState, FactionUpdate, AuthoritativeState.factions field | E53Ab imports from same state.py; any circular import or accidental mutation of FactionState would fail here |
| `tests/architecture/test_phase_domain_permissions.py` | Phase domain permissions (RPG-INFRA-155/156/157) | If FactionDecisionPhase writes to world/entity domains improperly, or if run_phase() is wired incorrectly, this guard fires |
| `tests/unit/engine/test_pipeline.py` (if present) | AuthoritativeApplyPipeline.refine() | Verify no regression in pipeline sub-phase ordering or cost tracking |

Scoped regression run:
```bash
pytest tests/unit/faction/ tests/architecture/test_phase_domain_permissions.py -x -v
```

---

## New Tests Required

File: `tests/unit/faction/test_faction_decision_phase.py`

All tests are deterministic, isolated, and import only from `src.engine.faction_decision` and `src.core.state`. They do NOT require a full `AuthoritativeState` construction — use minimal dataclasses or mocks.

---

### test_faction_decision_phase_produces_directive

**Purpose**: Verify that a faction with `tension_level=0.7` and non-empty `territory` emits a `DEFEND_BORDER` directive.

**Inputs**:
- `FactionState(faction_id="faction_a", tension_level=0.7, territory=("region_01",), military_strength=1.0)`
- `state.factions = {"faction_a": <above>}`

**Expected**:
- `execute()` returns a list with at least one `FactionDirective` where `directive_kind == "DEFEND_BORDER"` and `faction_id == "faction_a"`

**Acceptance criterion from ticket**: Directly maps to `test_faction_decision_phase_produces_directive` in `## Acceptance Criteria`.

```python
def test_faction_decision_phase_produces_directive():
    from src.engine.faction_decision import FactionDecisionPhase, FactionDirective
    from src.core.state import FactionState, AuthoritativeState

    fs = FactionState(faction_id="faction_a", tension_level=0.7, territory=("region_01",), military_strength=1.0)
    state = AuthoritativeState(tick=0, seed=0, factions={"faction_a": fs})

    directives = FactionDecisionPhase.execute(state, policy=None)

    kinds = {d.directive_kind for d in directives if d.faction_id == "faction_a"}
    assert "DEFEND_BORDER" in kinds
```

---

### test_faction_decision_phase_no_factions_returns_empty

**Purpose**: Verify that an empty `state.factions` produces an empty list without error.

**Inputs**:
- `state.factions = {}`

**Expected**:
- `execute()` returns `[]`
- No exception raised

**Acceptance criterion from ticket**: Directly maps to `test_faction_decision_phase_no_factions_returns_empty`.

```python
def test_faction_decision_phase_no_factions_returns_empty():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import AuthoritativeState

    state = AuthoritativeState(tick=0, seed=0)
    assert state.factions == {}

    result = FactionDecisionPhase.execute(state, policy=None)
    assert result == []
```

---

### test_faction_directive_frozen

**Purpose**: Verify that `FactionDirective` is a frozen dataclass — assignment after creation raises `FrozenInstanceError`.

**Inputs**:
- Construct a `FactionDirective` with known field values

**Expected**:
- `pytest.raises(FrozenInstanceError)` on attribute assignment

**Acceptance criterion from ticket**: `test_faction_directive_frozen` — `FactionDirective` is immutable (frozen dataclass, slots=True).

```python
def test_faction_directive_frozen():
    from dataclasses import FrozenInstanceError
    from src.engine.faction_decision import FactionDirective

    d = FactionDirective(faction_id="faction_a", directive_kind="DEFEND_BORDER", created_tick=5)
    with pytest.raises(FrozenInstanceError):
        d.faction_id = "other"
```

---

### test_faction_decision_phase_trade_route

**Purpose**: Verify that a faction with high `military_strength` and low `tension_level` emits a `TRADE_ROUTE` directive (not DEFEND_BORDER).

**Inputs**:
- `FactionState(faction_id="faction_b", military_strength=0.8, tension_level=0.2, territory=())`
- `state.factions = {"faction_b": <above>}`

**Expected**:
- Returned list contains a `FactionDirective` with `directive_kind == "TRADE_ROUTE"` and `faction_id == "faction_b"`

**Rationale**: Covers the branch `military_strength > 0.7 and tension_level < 0.3 → TRADE_ROUTE`. Complements the DEFEND_BORDER test to ensure all three directive paths are exercised.

```python
def test_faction_decision_phase_trade_route():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import FactionState, AuthoritativeState

    fs = FactionState(faction_id="faction_b", military_strength=0.8, tension_level=0.2, territory=())
    state = AuthoritativeState(tick=10, seed=0, factions={"faction_b": fs})

    directives = FactionDecisionPhase.execute(state, policy=None)

    kinds = {d.directive_kind for d in directives if d.faction_id == "faction_b"}
    assert "TRADE_ROUTE" in kinds
    assert "DEFEND_BORDER" not in kinds
```

---

### test_faction_decision_phase_commission_quest

**Purpose**: Verify that a faction with non-empty `territory` emits a `COMMISSION_QUEST` directive with `priority == tension_level`.

**Inputs**:
- `FactionState(faction_id="faction_c", territory=("region_02",), tension_level=0.4, military_strength=0.5)`
- `state.factions = {"faction_c": <above>}`

**Expected**:
- Returned list contains a `FactionDirective` with `directive_kind == "COMMISSION_QUEST"`, `faction_id == "faction_c"`, and `priority == 0.4` (== tension_level)

**Rationale**: Covers the `len(territory) > 0 → COMMISSION_QUEST with priority=tension_level` branch. Note: `tension_level=0.4` is below the `> 0.5` DEFEND_BORDER threshold, so DEFEND_BORDER should NOT appear, isolating the COMMISSION_QUEST path.

```python
def test_faction_decision_phase_commission_quest():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import FactionState, AuthoritativeState

    fs = FactionState(faction_id="faction_c", territory=("region_02",), tension_level=0.4, military_strength=0.5)
    state = AuthoritativeState(tick=5, seed=0, factions={"faction_c": fs})

    directives = FactionDecisionPhase.execute(state, policy=None)

    quest_directives = [d for d in directives if d.faction_id == "faction_c" and d.directive_kind == "COMMISSION_QUEST"]
    assert len(quest_directives) >= 1
    assert quest_directives[0].priority == pytest.approx(0.4)
    defend_directives = [d for d in directives if d.faction_id == "faction_c" and d.directive_kind == "DEFEND_BORDER"]
    assert defend_directives == []
```

---

## Scoped Pytest Commands

Run only the new faction decision tests (fastest, use during development):
```bash
pytest tests/unit/faction/test_faction_decision_phase.py -x -v
```

Run full faction test suite (regression + new):
```bash
pytest tests/unit/faction/ -x -v
```

Run architecture guards:
```bash
pytest tests/architecture/test_phase_domain_permissions.py -x -v
```

Combined scope for pre-commit validation:
```bash
pytest tests/unit/faction/ tests/architecture/test_phase_domain_permissions.py -x -v
```

Do NOT run `pytest tests/` (full suite) — scope to faction domain and architecture guards only.

---

## Anti-Drift Test Guards

The following test assertions must be included to prevent future drift from the anti-drift hazards in the investigation:

### Guard 1: FactionDirective is NOT in StateUpdate
```python
def test_faction_directive_not_in_state_update():
    """Ensure FactionDirective is not accidentally added to StateUpdate."""
    from src.core.updates import StateUpdate
    assert not hasattr(StateUpdate, "faction_directives"), (
        "FactionDirective must never be added to StateUpdate — directives are transient"
    )
```

### Guard 2: FactionDecisionPhase.execute() does not return StateUpdate
```python
def test_faction_decision_phase_returns_list_not_state_update():
    from src.engine.faction_decision import FactionDecisionPhase
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate

    state = AuthoritativeState(tick=0, seed=0)
    result = FactionDecisionPhase.execute(state, policy=None)
    assert isinstance(result, list), "FactionDecisionPhase.execute() must return list[FactionDirective], not StateUpdate"
    assert not isinstance(result, StateUpdate)
```

### Guard 3: FactionDirective slots=True
```python
def test_faction_directive_has_slots():
    from src.engine.faction_decision import FactionDirective
    assert hasattr(FactionDirective, "__slots__"), "FactionDirective must use slots=True for memory efficiency"
```

### Guard 4: No TickPhase extension (regression guard, already covered by architecture tests)
Architecture test `tests/architecture/test_phase_domain_permissions.py` covers this. No additional assertion needed in unit tests.
