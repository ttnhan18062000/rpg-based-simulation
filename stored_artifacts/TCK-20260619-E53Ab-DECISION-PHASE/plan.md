---
ticket_id: TCK-20260619-E53Ab-DECISION-PHASE
phase: plan
date: 2026-06-22
artifact_type: plan
---

# Implementation Plan — TCK-20260619-E53Ab-DECISION-PHASE (FactionDecisionPhase + FactionDirective)

## Overview

Four ordered steps. Each is independently verifiable. Steps 1 and 2 are independent of each other and can be verified before Step 3 begins. Step 4 depends on Steps 1–3 (tests exercise all three).

```
Step 1 ──► Step 3 ──► Step 4
Step 2 ──►
```

---

## Step 1 — Add `faction_decision` cadence field to `SystemCadence`

**File:** `src/engine/cadence.py`

**Change:** Add one field to the `SystemCadence` Pydantic model, in the `# Strategic / Cognition (High Cost)` section, after `social_memory`:

```python
    faction_decision: int = Field(10, ge=1)
```

Default value: 10 ticks, matching `strategic_intelligence` cadence. This gives E53B/C an independent tuning knob without touching `strategic_intelligence`.

**Scope guards:**
- Do NOT modify `should_run()`.
- Do NOT change any existing cadence field defaults.
- Do NOT alter `model_config = ConfigDict(frozen=True)` — adding a field with a default is safe for frozen Pydantic models; all existing call sites pass unchanged because Pydantic uses keyword args.

**Verification:**
```bash
python3 -c "from src.engine.cadence import SystemCadence; c = SystemCadence(); assert c.faction_decision == 10; print('OK')"
```
Passes without error. All existing `SystemCadence()` construction in tests and integration code is unaffected (no positional-arg construction exists for this model).

---

## Step 2 — Create `src/engine/faction_decision.py`

**File:** `src/engine/faction_decision.py` (new file)

**Contents:**

### FactionDirective (frozen dataclass)

```python
@dataclass(frozen=True, slots=True)
class FactionDirective:
    faction_id: str
    directive_kind: str        # "DEFEND_BORDER" | "TRADE_ROUTE" | "COMMISSION_QUEST"
    target_faction: Optional[str] = None
    target_region: Optional[str] = None
    priority: float = 1.0
    created_tick: int = 0
```

Fields match the ticket spec exactly. `directive_kind` is a plain string (NOT an IntEnum) — required per ticket to keep E53B/C extensible without enum churn.

### FactionDecisionPhase (stateless class)

```python
class FactionDecisionPhase:
    @staticmethod
    def execute(
        state: AuthoritativeState,
        policy: GovernorPolicy | None,
    ) -> list[FactionDirective]:
        directives: list[FactionDirective] = []
        for faction_id, fs in state.factions.items():
            if fs.tension_level > 0.5 and len(fs.territory) > 0:
                directives.append(FactionDirective(
                    faction_id=faction_id,
                    directive_kind="DEFEND_BORDER",
                    priority=fs.tension_level,
                    created_tick=state.tick,
                ))
            elif fs.military_strength > 0.7 and fs.tension_level < 0.3:
                directives.append(FactionDirective(
                    faction_id=faction_id,
                    directive_kind="TRADE_ROUTE",
                    priority=1.0,
                    created_tick=state.tick,
                ))
            if len(fs.territory) > 0:
                directives.append(FactionDirective(
                    faction_id=faction_id,
                    directive_kind="COMMISSION_QUEST",
                    priority=fs.tension_level,
                    created_tick=state.tick,
                ))
        return directives
```

**Decision on DEFEND_BORDER vs COMMISSION_QUEST mutual exclusion:**
The ticket spec says COMMISSION_QUEST fires on `len(territory) > 0` unconditionally, but the test `test_faction_decision_phase_commission_quest` isolates COMMISSION_QUEST by using `tension_level=0.4` (below the DEFEND_BORDER threshold of `> 0.5`) and asserts `defend_directives == []`. This means DEFEND_BORDER and COMMISSION_QUEST may co-emit when `tension_level > 0.5` and `territory` non-empty. The test for COMMISSION_QUEST excludes the DEFEND_BORDER condition by construction. Use `if/elif` for the first two branches, then an unconditional `if` for COMMISSION_QUEST — this satisfies all five test cases. (See Resolved Question 1.)

**Import discipline:**
- Top of file: `from __future__ import annotations`
- `from typing import TYPE_CHECKING, Optional`
- `if TYPE_CHECKING:` guard for `from src.core.state import AuthoritativeState` and `from src.engine.policy import GovernorPolicy`
- Runtime: `state.factions` access is duck-typed; no runtime import of `AuthoritativeState` needed.

**Scope guards:**
- Do NOT import from `src.engine.world_dynamics`.
- Do NOT import from `src.engine.phases` (TickPhase must not be referenced here).
- Do NOT define an enum or IntEnum for `directive_kind`.
- `policy` parameter accepted but intentionally unused in E53Ab — it exists for E53B/C compatibility per the ticket.

**Verification:**
```bash
python3 -c "from src.engine.faction_decision import FactionDirective, FactionDecisionPhase; print('import OK')"
```

---

## Step 3 — Wire `FactionDecisionPhase` into `pipeline.py:refine()`

**File:** `src/engine/pipeline.py`

**Location:** Inside `AuthoritativeApplyPipeline.refine()`, immediately after the `world_emergence` block (line ~219) and before the `# --- Phase 6: Economy & Evolution ---` comment (line ~221).

**Change:** Insert the following block between `costs["world_emergence"]` and the Phase 6 comment:

```python
        # --- Enhanced RPG Phase 8b: Faction Decision ---
        t_start = time.perf_counter_ns()
        faction_directives: list = []
        if should_run(state.tick, None, cadence.faction_decision):
            from src.engine.faction_decision import FactionDecisionPhase
            faction_directives = FactionDecisionPhase.execute(state, policy=None)
        costs["faction_decision"] = (time.perf_counter_ns() - t_start) / 1e6
```

**Why not `run_phase()`:** `run_phase()` has the signature `(phase_name, update, phase_fn)` where `phase_fn: StateUpdate -> StateUpdate`. `FactionDecisionPhase.execute()` returns `list[FactionDirective]`, not a `StateUpdate`. Wrapping it in a fake `StateUpdate` would violate the architecture rule (directives must never enter `StateUpdate`). Use a direct inline block with `should_run()` gating — consistent with how `recent_world_events` is captured and with the `generator._last_id` assignment pattern already in the pipeline.

**Policy parameter:** `refine()` is a `@staticmethod` — no `self` exists. Pass `policy=None` in the wiring call; this is acceptable in E53Ab since the parameter is unused and reserved for E53B/C injection via a future signature extension.

**Scope guards:**
- Do NOT add `faction_directives` to `StateUpdate` or any `*Update` dataclass.
- Do NOT add a new `TickPhase` enum member (`src/engine/phases.py` is frozen).
- Do NOT wire through `GovernorPolicy` as a phase registry.
- Do NOT call into `WorldDynamicsSystem` from this block.
- `faction_directives` is a local variable in `refine()` — it goes out of scope at the end of the call. E53Ac will capture it via closure when its phase call is added (same pattern as `recent_world_events` for WorldEmergencePhase).

**Verification:**
```bash
python3 -c "
from src.core.state import AuthoritativeState
from src.engine.pipeline import AuthoritativeApplyPipeline
print('pipeline import OK')
"
```
Also: `pytest tests/architecture/test_phase_domain_permissions.py -x -v` must pass.

---

## Step 4 — Write `tests/unit/faction/test_faction_decision_phase.py`

**File:** `tests/unit/faction/test_faction_decision_phase.py` (new file)

The `tests/unit/faction/__init__.py` already exists. No new `__init__.py` needed.

**Tests to implement (5 from test_plan.md + 3 anti-drift guards = 8 total):**

### Primary tests (acceptance criteria)

1. `test_faction_decision_phase_produces_directive` — `tension_level=0.7`, `territory=("region_01",)` → DEFEND_BORDER emitted for `faction_a`.
2. `test_faction_decision_phase_no_factions_returns_empty` — `state.factions={}` → returns `[]`.
3. `test_faction_directive_frozen` — assigning to `FactionDirective.faction_id` raises `FrozenInstanceError`.
4. `test_faction_decision_phase_trade_route` — `military_strength=0.8`, `tension_level=0.2`, empty territory → TRADE_ROUTE emitted, DEFEND_BORDER NOT emitted.
5. `test_faction_decision_phase_commission_quest` — `territory=("region_02",)`, `tension_level=0.4` → COMMISSION_QUEST with `priority ≈ 0.4`, DEFEND_BORDER NOT emitted.

### Anti-drift guards

6. `test_faction_directive_not_in_state_update` — `StateUpdate` has no `faction_directives` attribute.
7. `test_faction_decision_phase_returns_list_not_state_update` — `execute()` returns `list`, not `StateUpdate`.
8. `test_faction_directive_has_slots` — `FactionDirective` has `__slots__`.

**Test inputs follow test_plan.md exactly.** Use `AuthoritativeState(tick=..., seed=0, factions={...})` construction (no mocks needed — `FactionState` is a frozen dataclass).

**Scope guards:**
- Do NOT import from `src.engine.pipeline` in this test file — unit tests for `FactionDecisionPhase` must not depend on the pipeline wiring.
- Do NOT test cadence gating in this file — that is a pipeline integration concern.
- All tests must be deterministic and import-isolated.

**Verification:**
```bash
pytest tests/unit/faction/test_faction_decision_phase.py -x -v
```
All 8 tests must pass.

---

## Full Pre-Commit Validation

After all four steps are complete:

```bash
# New tests
pytest tests/unit/faction/test_faction_decision_phase.py -x -v

# Regression: faction domain
pytest tests/unit/faction/ -x -v

# Architecture guards
pytest tests/architecture/test_phase_domain_permissions.py -x -v
```

Do NOT run `pytest tests/` (full suite).

---

## Parity Ledger Update

After tests pass, add entry FAC-003 to `docs/parity_ledger/faction.yaml` (create if not present):

```yaml
- id: FAC-003
  text: >
    FactionDecisionPhase reads state.factions each decision tick and emits
    transient FactionDirective list; directives are not persisted in AuthoritativeState
  status: verified
  priority: P2
  v2_evidence: "src/engine/faction_decision.py + src/engine/pipeline.py (faction_decision inline block)"
  test_path: tests/unit/faction/test_faction_decision_phase.py
  divergence_note: ""
```

---

## Acceptance Criteria Mapping

| Acceptance Criterion (from ticket) | Step | Test |
|---|---|---|
| `test_faction_decision_phase_produces_directive` passes | Steps 2, 3, 4 | `test_faction_decision_phase_produces_directive` |
| `test_faction_decision_phase_no_factions_returns_empty` passes | Steps 2, 4 | `test_faction_decision_phase_no_factions_returns_empty` |
| `test_faction_directive_frozen` passes | Steps 2, 4 | `test_faction_directive_frozen` |
| Cadenced call present in pipeline; no directives if no factions | Steps 1, 3 | Implicit in `test_faction_decision_phase_no_factions_returns_empty` |

---

## Dependency Map

```
Step 1 (cadence.py field)
  └─► Step 3 (pipeline.py wiring — reads cadence.faction_decision)

Step 2 (faction_decision.py — FactionDirective + FactionDecisionPhase)
  └─► Step 3 (pipeline.py wiring — imports FactionDecisionPhase)
  └─► Step 4 (tests — imports FactionDirective + FactionDecisionPhase)

Step 3 (pipeline.py wiring)
  └─► Step 4 (tests — cadence gating guard references pipeline behavior indirectly)
```

Steps 1 and 2 are independent. Step 3 requires both. Step 4 requires Steps 1–3.

---

## Scope Guards (Summary)

**DO NOT touch:**
- `src/engine/phases.py` — TickPhase enum is frozen (Phase 4 Baseline Freeze Contract)
- `src/engine/world_dynamics.py` — faction logic must not enter this system
- `src/core/updates.py` / any `*Update` dataclass — `FactionDirective` is transient, never in state updates
- `src/core/state.py` — `AuthoritativeState` and `FactionState` are complete (E53Aa done)
- `src/engine/policy.py` — `GovernorPolicy` is not a phase registry; `policy` is passed in but not used in E53Ab

---

## Resolved Questions

### Resolved Question 1: DEFEND_BORDER and COMMISSION_QUEST co-emission

The ticket spec lists:
- `tension_level > 0.5 and territory non-empty` → DEFEND_BORDER
- `military_strength > 0.7 and tension_level < 0.3` → TRADE_ROUTE
- `len(territory) > 0` → COMMISSION_QUEST (priority = tension_level)

The test `test_faction_decision_phase_commission_quest` uses `tension_level=0.4` and asserts DEFEND_BORDER is NOT emitted, isolating the COMMISSION_QUEST path. The test `test_faction_decision_phase_produces_directive` uses `tension_level=0.7` and only asserts DEFEND_BORDER is present (does not forbid COMMISSION_QUEST co-emission).

**Decision:** Use `if/elif` for DEFEND_BORDER vs TRADE_ROUTE (they are mutually exclusive by their conditions), then an unconditional `if` for COMMISSION_QUEST. This means a faction can emit both DEFEND_BORDER and COMMISSION_QUEST in the same tick when conditions overlap — the COMMISSION_QUEST test avoids this overlap by design. This satisfies all five test cases exactly.

### Resolved Question 2: Cadence value default

Use 10 ticks (matching `strategic_intelligence`). Per investigation "Open Question 1" — the ticket scope says "every 10 ticks, matching strategic_intelligence cadence."

### Resolved Question 3: `policy` parameter usage in E53Ab

`policy: GovernorPolicy | None` is accepted in the `execute()` signature for E53B/C compatibility but is unused in E53Ab. Pass `policy=None` at all call sites (tests and pipeline wiring). No defensive check on `policy` is needed in E53Ab — the parameter is reserved for E53B/C.

---

## Unresolved Questions

**None requiring human input.** All decisions are resolved above based on investigation findings, existing repo patterns, and test plan constraints.

---

## Deviations

**None.** All four steps executed exactly as planned. No deviations from the plan:
- Step 1: `faction_decision` field added after `social_memory` as specified.
- Step 2: `faction_decision.py` created with exact dataclass, constants, and logic from plan.
- Step 3: Inline block inserted between `costs["world_emergence"]` and Phase 6 comment exactly as specified; `policy=None` used.
- Step 4: 11 tests written (8 specified + 3 anti-drift guards from plan.md Section 4); all pass.
