---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Ab-DECISION-PHASE
phase: done
date: 2026-06-22
tags: [faction, faction-decision-phase, faction-directive, engine-phase, phase-5]
---

# TCK-20260619-E53Ab-DECISION-PHASE

## Title
Epic 5.3Ab · FactionDecisionPhase + FactionDirective

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implement `FactionDecisionPhase` — a stateless domain phase that reads `AuthoritativeState.factions` and emits `FactionDirective` structs representing faction-level strategic intentions. Wire it into the engine tick loop cadenced via `SystemCadence`. Depends on E53Aa (FactionState + FactionUpdate must exist first).

## Scope

**FactionDirective** (new frozen dataclass in `src/engine/faction_decision.py`):
```python
@dataclass(frozen=True, slots=True)
class FactionDirective:
    faction_id: str
    directive_kind: str        # e.g. "DEFEND_BORDER", "TRADE_ROUTE", "COMMISSION_QUEST"
    target_faction: Optional[str] = None
    target_region: Optional[str] = None
    priority: float = 1.0
    created_tick: int = 0
```

**FactionDecisionPhase** (new in `src/engine/faction_decision.py`):
```python
class FactionDecisionPhase:
    @staticmethod
    def execute(
        state: AuthoritativeState,
        policy: GovernorPolicy,
    ) -> list[FactionDirective]:
        """
        For each FactionState in state.factions:
          - If tension_level > 0.5 and territory non-empty: emit DEFEND_BORDER directive
          - If military_strength > 0.7 and tension_level < 0.3: emit TRADE_ROUTE directive
          - If len(territory) > 0: emit COMMISSION_QUEST directive (priority = tension_level)
        Returns list of FactionDirective (one or more per faction).
        """
```

**Engine wiring**: Call `FactionDecisionPhase.execute()` inside the kernel tick loop (or `world_dynamics.py`) gated on a `SystemCadence` interval (e.g. every 10 ticks, matching `strategic_intelligence` cadence). The result list of `FactionDirective` objects must be stored transiently per tick (not durable state) for E53Ac to consume in the same tick. Suggest storing them on a per-tick scratch object or passing them directly to the scoring layer; do NOT persist directives in `AuthoritativeState` (they are re-derived each decision tick).

Decide the exact wiring point by reading `src/engine/kernel.py` tick loop and `src/engine/world_dynamics.py` before implementing. Follow whichever pattern minimizes coupling (most likely: a call in `world_dynamics.py` or a new `faction_dynamics.py` system, similar to how `WorldEmergencePhase` is orchestrated).

## Out of Scope
- FactionState model (E53Aa — prerequisite)
- Directive propagation to entity scoring (E53Ac)
- Tension update from events (E53Ad)
- Diplomatic/war decisions (E53B, E53C)

## Acceptance Criteria
- `test_faction_decision_phase_produces_directive` passes:
  - Given a FactionState with tension_level=0.7 and territory=("region_01",), `FactionDecisionPhase.execute()` returns at least one `FactionDirective` with directive_kind="DEFEND_BORDER"
- `test_faction_decision_phase_no_factions_returns_empty` passes:
  - Given `state.factions={}`, `execute()` returns `[]` without error
- `test_faction_directive_frozen` passes:
  - `FactionDirective` is immutable (frozen dataclass, slots=True)
- Engine wiring: cadenced call present in kernel/world_dynamics; no directives emitted if no factions exist

## Related Tickets
- TCK-20260619-E53A-FACTION-AGENT (parent epic)
- TCK-20260619-E53Aa-FACTION-STATE (prerequisite — FactionState must exist)
- TCK-20260619-E53Ac-DIRECTIVE-PROP (depends on this — consumes FactionDirective list)

## Related Docs
- `docs/engine/kernel.md` (6-phase loop; FactionDecisionPhase runs within existing phases)
- `docs/engine/governance_logic.md` (governance insertion patterns)
- `docs/mechanics/04_strategic_cognition.md` (directive priority semantics)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53A-FACTION-AGENT/investigation.md`

## Related Code Areas
- `src/engine/faction_decision.py` (new file)
- `src/engine/kernel.py` (tick loop — read before wiring)
- `src/engine/world_dynamics.py` (likely wiring point)
- `src/engine/policy.py` (GovernorPolicy — cadence gating)
- `tests/unit/faction/test_faction_decision_phase.py` (new file)

## Assumptions / Open Questions
- `TickPhase` enum is FROZEN — no new TickPhase values. FactionDecisionPhase runs inside an existing phase as a sub-phase call.
- `FactionDirective` objects are transient (per-tick scratch) — not persisted in `AuthoritativeState`. Re-derived each decision cadence tick.
- Directive kinds ("DEFEND_BORDER", "TRADE_ROUTE", "COMMISSION_QUEST") are string constants defined in `faction_decision.py`; do NOT use an IntEnum to keep E53B/E53C extensible without enum churn.
- `GovernorPolicy` is a config dataclass — phase wiring does NOT go through it. The cadence gate uses `SystemCadence.strategic_intelligence` or a dedicated faction cadence field (confirm at implementation time).

## Implementation Notes
- Follow `WorldEmergencePhase` as the structural reference: stateless static `execute()`, reads state, returns a plain Python list (not StateUpdate).
- Keep `faction_decision.py` import-clean: no module-level imports of `src.core.state` beyond `TYPE_CHECKING` — consistent with the import discipline in `social_memory.py`.
- The FactionDirective list produced here feeds directly into E53Ac (directive propagation). Pass it as a parameter to the scoring layer in the same tick; do not store it anywhere durable.

### Implemented (E53Ab)
- Added `faction_decision: int = Field(10, ge=1)` to `SystemCadence` in `src/engine/cadence.py` (Strategic/Cognition section, after `social_memory`).
- Created `src/engine/faction_decision.py` with `FactionDirective` (frozen dataclass, slots=True), string constants `DEFEND_BORDER`/`TRADE_ROUTE`/`COMMISSION_QUEST`, and `FactionDecisionPhase.execute()`.
- Wired inline block into `src/engine/pipeline.py:refine()` after `costs["world_emergence"]`, using `should_run(state.tick, None, cadence.faction_decision)` with `policy=None`.
- `faction_directives` is a local variable in `refine()` — transient, not in StateUpdate or AuthoritativeState.
- Added parity ledger entry FAC-003 in `docs/parity_ledger/faction.yaml`.
- 11 tests written and passing (8 primary + 3 anti-drift guards).

## Test Summary
```bash
pytest tests/unit/faction/test_faction_decision_phase.py -x -v
```

## Files Changed
- `src/engine/cadence.py` — added `faction_decision: int = Field(10, ge=1)` to SystemCadence
- `src/engine/faction_decision.py` — new file: `FactionDirective` frozen dataclass (slots=True), string constants DEFEND_BORDER/TRADE_ROUTE/COMMISSION_QUEST, `FactionDecisionPhase.execute()`
- `src/engine/pipeline.py` — wired inline faction_decision cadence-gated block in `refine()` between world_emergence and Phase 6; `faction_directives` stored as transient local variable (never enters StateUpdate)
- `docs/parity_ledger/faction.yaml` — added FAC-003 entry (verified)
- `tests/unit/faction/test_faction_decision_phase.py` — 11 new tests (8 primary + 3 anti-drift guards)

## Completion Summary
FactionDirective frozen dataclass and FactionDecisionPhase.execute() created in src/engine/faction_decision.py (DEFEND_BORDER/TRADE_ROUTE/COMMISSION_QUEST logic); faction_decision cadence (default 10) added to SystemCadence in cadence.py; wired inline in pipeline.py:refine() between world_emergence and Phase 6 as cadence-gated local variable (never enters StateUpdate); 11 new tests in tests/unit/faction/test_faction_decision_phase.py; FAC-003 added to docs/parity_ledger/faction.yaml. All 28 tests pass (11 new + 17 regression). Architecture guards pass.
