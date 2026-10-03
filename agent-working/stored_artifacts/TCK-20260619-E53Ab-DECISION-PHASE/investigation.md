---
ticket_id: TCK-20260619-E53Ab-DECISION-PHASE
phase: investigate
date: 2026-06-22
artifact_type: investigation
---

# Investigation — TCK-20260619-E53Ab-DECISION-PHASE (FactionDecisionPhase + FactionDirective)

## Current Behavior

### WorldEmergencePhase Wiring Pattern (Reference)

`WorldEmergencePhase` lives in `src/domains/world_emergence/phase.py` as a stateless class with a single `@staticmethod execute(state, update, recent_events) -> tuple[StateUpdate, WorldEmergenceResult]`. It is called from `src/engine/pipeline.py` inside `AuthoritativeApplyPipeline.refine()` under a `run_phase()` call:

```python
# pipeline.py line ~216
from src.domains.world_emergence.phase import WorldEmergencePhase
recent_world_events = getattr(state, "recent_world_events", [])
update = run_phase("world_emergence", update, lambda u: WorldEmergencePhase.execute(state, u, recent_world_events)[0], "ENABLE_WORLD_EMERGENCE")
```

Key structural properties of WorldEmergencePhase:
- Stateless — no instance variables, no class-level mutable state
- Static `execute()` takes `(state, update, recent_events)` and returns `(StateUpdate, result)`
- Named as a top-level domain class, not a method on a system class
- Registered via `run_phase()` helper in the pipeline (supports feature flags, dependency graph skipping, SHADOW mode)
- Module-level imports go under `TYPE_CHECKING`; runtime imports are done inline inside `execute()` to avoid circular dependencies

### Cadence Gating Pattern in world_dynamics.py

`WorldDynamicsSystem.resolve_dynamics()` uses `should_run()` for cadence gating of sub-sections:

```python
from src.engine.cadence import SystemCadence as DefaultCadence, should_run
cadence = cadence or DefaultCadence()

if should_run(state.tick, None, cadence.world_dynamics):   # every 50 ticks
    # process calamities, ecology, bosses, raids, demographics
    if should_run(state.tick, None, cadence.boss_spawn):   # every 100 ticks (nested gate)
        ...
```

Pattern: `should_run(tick, entity_id=None, cadence_value)` — passes `None` for global systems (not entity-staggered). The cadence field used is from `SystemCadence` (a frozen Pydantic model). Adding a new cadence field to `SystemCadence` is the correct path; it does not change the frozen status of `TickPhase`.

### Kernel Tick Loop Structure

From `src/engine/kernel.py:L295-L354` (`_tick_once_inner`):

```
Phase 1: _phase_init()        — reset stats, collect signals, evaluate Governor policy
Phase 2: _phase_scheduling()  — select work items
Phase 3: _phase_collection()  — execute workers concurrently (read-only snapshot)
Phase 4: _phase_resolution()  — AuthoritativeApplyPipeline.refine() + replay emit
Phase 5: _phase_cleanup()     — telemetry, cache sweep
Phase 6: _phase_advancement() — commit new state
Phase 7: _phase_persistence() — hashes, replay trace
```

`AuthoritativeApplyPipeline.refine()` is called **exclusively** in `_phase_resolution()` (line ~572). All 17 sub-phases of the pipeline (including WorldEmergencePhase) execute inside this single synchronous bottleneck. The kernel's `_phase_resolution()` declares `world` as a write domain (see `docs/engine/kernel.md` Phase Domain Permissions table), making it the only valid location for faction-level state-affecting calls.

`TickPhase` is an enum returned by `get_authoritative_phases()` (`src/engine/phases.py`). It is FROZEN since Phase 4 Baseline Freeze Contract — no new enum members.

### FactionState After E53Aa

Confirmed present at `src/core/state.py:L569-L606`:

```python
@dataclass(frozen=True, slots=True)
class FactionState:
    faction_id: str
    territory: Tuple[str, ...] = ()
    resources: Dict[str, int] = field(default_factory=dict)
    diplomatic_relations: Dict[str, str] = field(default_factory=dict)
    active_doctrines: Tuple[str, ...] = ()
    military_strength: float = 1.0
    tension_level: float = 0.0
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)
```

`AuthoritativeState.factions: Dict[str, FactionState]` field is confirmed by `tests/unit/faction/test_faction_state.py::test_authoritative_state_has_factions_field`. `FactionUpdate` apply-path exists in `src/engine/apply.py` (tension clamped to [0.0, 1.0]).

Parity entries FAC-001 and FAC-002 are `status: verified` — the FactionState layer is fully done.

---

## Wiring Decision

### Decision: Wire in AuthoritativeApplyPipeline as a new `run_phase()` call, adjacent to WorldEmergencePhase

**Verdict: Add `FactionDecisionPhase` as a named phase inside `AuthoritativeApplyPipeline.refine()` in `src/engine/pipeline.py`, immediately after the `world_emergence` call (or just before `strategic_intelligence`), guarded by a `SystemCadence.faction_decision` cadence field.**

Rationale:

1. **Not in world_dynamics.py**: `WorldDynamicsSystem.resolve_dynamics()` owns regional hazards, calamity, spawning, ecology, demographics. It has no faction awareness and follows a different return signature (`StateUpdate`-in/`StateUpdate`-out chaining). Mixing faction logic into `world_dynamics.py` would break single-responsibility and make E53B/C/D harder to separate. It is also called inside `run_phase("world_dynamics", ...)` — adding faction logic there would bury it inside a system that doesn't own it.

2. **Not a new file for wiring**: `faction_decision.py` is the *implementation* home. The wiring call lives in `pipeline.py` — matching every other domain phase (world_emergence, adventure_decision, cooperation, combat_engagement, progression_conversion).

3. **Cadence gate**: Use `cadence.strategic_intelligence` (default 10 ticks) as the gate — faction decisions are "strategic frequency." Alternatively add `faction_decision: int = Field(10, ge=1)` to `SystemCadence` for explicit independence. **Prefer adding a dedicated `faction_decision` field** so E53B/C can tune it independently from `strategic_intelligence`. This is a one-line addition to `src/engine/cadence.py`.

4. **Placement in pipeline sequence**: After `world_emergence` (phase 8 Enhanced RPG) and before `strategic_intelligence` (phase 7 final integrity). This ensures faction directives are available when `strategic_intelligence` runs on the same tick, and any world events processed by WorldEmergencePhase are already reflected in the state view.

5. **Signature**: `FactionDecisionPhase.execute(state, policy)` returns `list[FactionDirective]`. Unlike WorldEmergencePhase, it does NOT need to return a `StateUpdate` because directives are transient — they are passed to E53Ac in the same tick, not written to state. Inside `run_phase()` the lambda must handle the non-StateUpdate return. Either:
   - Store the result in a tick-scoped scratch location (see risk note below), OR
   - Wire it outside `run_phase()` since `run_phase()` expects `StateUpdate` in/out

   **Recommended**: Call it outside `run_phase()` as a direct inline call (like some phases do), but still cadence-gated with `should_run()`. This avoids forcing a fake StateUpdate wrapper. Store directives as a local variable in the `refine()` call scope and thread them to E53Ac's phase call via parameter injection (same pattern as `recent_world_events`).

**Exact code location**: `src/engine/pipeline.py`, inside `AuthoritativeApplyPipeline.refine()`, between the `world_emergence` call (line ~219) and the `strategic_intelligence` call (line ~254).

```python
# --- Enhanced RPG Phase 8b: Faction Decision ---
t_start = time.perf_counter_ns()
faction_directives = []
if should_run(state.tick, None, cadence.faction_decision):
    from src.engine.faction_decision import FactionDecisionPhase
    faction_directives = FactionDecisionPhase.execute(state, cadence)
costs["faction_decision"] = (time.perf_counter_ns() - t_start) / 1e6
```

Then pass `faction_directives` to E53Ac's phase call (E53Ac is a future ticket — placeholder for now).

---

## Mechanics / Engine Constraints

### TickPhase is FROZEN

`TickPhase` enum cannot be extended. Confirmed by E53A-FACTION-AGENT investigation and the Phase 4 Baseline Freeze Contract. `FactionDecisionPhase` is a domain-phase sub-call within `_phase_resolution()`, not a new TickPhase member.

### FactionDirective is Transient — NOT in AuthoritativeState

`FactionDirective` objects are re-derived each decision tick. They are never written to `AuthoritativeState.factions` or any other durable field. They exist as a Python list scoped to the current `refine()` call.

The correct storage for the directive list is as a local variable in `AuthoritativeApplyPipeline.refine()`, threaded as a parameter to E53Ac's future phase call. Do NOT add a `faction_directives` field to `StateUpdate`, `AuthoritativeState`, or any update type.

### GovernorPolicy is NOT the Wiring Point

`GovernorPolicy` is a frozen config dataclass for resource governance (concurrency limits, replay policy, mode). It has no registry of phases and must not be used as the wiring mechanism. The pipeline's `run_phase()` / direct inline call is the correct wiring point.

### Phase Domain Permissions

`_phase_resolution()` declares write access to `entity` and `world` domains. `FactionDecisionPhase.execute()` is **read-only** — it reads `state.factions` and returns a list. It does not produce a `StateUpdate`. This is consistent with the permissions table: RESOLUTION reads proposals/policy/entity and writes entity/world — reading `state.factions` is allowed; emitting a transient list is not a write to authoritative state.

### Import Discipline

`faction_decision.py` must use `from __future__ import annotations` and place `src.core.state` imports under `TYPE_CHECKING`, consistent with `src/domains/campaigns/social_memory.py` and `src/domains/world_emergence/phase.py`. Runtime imports of `AuthoritativeState` go inside method body or stay under TYPE_CHECKING.

---

## Parity Ledger Overlap

### faction.yaml (FAC-001, FAC-002)

Both entries are `status: verified` and relate to `FactionState` persistence and `FactionUpdate` apply-path (E53Aa work). **FactionDecisionPhase does not touch the apply-path** — it is a read-only phase producing transient output. FAC-001 and FAC-002 do not need updating for E53Ab.

A new parity entry **FAC-003** should be added upon completion of E53Ab:
```yaml
- id: FAC-003
  text: >
    FactionDecisionPhase reads state.factions each decision tick and emits
    transient FactionDirective list; directives are not persisted in AuthoritativeState
  status: verified  (after E53Ab implementation)
  priority: P2
  v2_evidence: src/engine/faction_decision.py + src/engine/pipeline.py (faction_decision run phase)
  test_path: tests/unit/faction/test_faction_decision_phase.py
```

### strategic_cognition.yaml

No strategic cognition parity entries are affected. `FactionDecisionPhase` is a faction-level system — it does not modify entity-level `StrategicComponent` or the `StrategicIntelligenceSystem`. Entity-level directive propagation is E53Ac's responsibility.

### world_dynamics.yaml

No world_dynamics parity entries are affected. `FactionDecisionPhase` is not wired into `WorldDynamicsSystem`.

---

## Prior Work

### E53Aa — FactionState (DONE)
- `src/core/state.py:L569` — `FactionState` frozen dataclass confirmed present
- `AuthoritativeState.factions: Dict[str, FactionState]` field confirmed
- `FactionUpdate` + apply-path in `src/engine/apply.py` confirmed (FAC-001, FAC-002 verified)
- Tests: `tests/unit/faction/test_faction_state.py` — all pass

### WorldEmergencePhase Pattern (Reference)
- `src/domains/world_emergence/phase.py` — stateless static `execute()`, reads state, returns typed result
- Called from `pipeline.py` inside `run_phase()` at line ~216
- Import style: direct imports of `AuthoritativeState`, `StateUpdate` at module level (not under TYPE_CHECKING) because `phase.py` is a domain layer that owns its imports
- `FactionDecisionPhase` differs: its return value is `list[FactionDirective]`, not `StateUpdate`, so the `run_phase()` wrapper does not apply directly — use a direct inline call with `should_run()` cadence gate instead

---

## Risks and Open Questions

### Risk 1: run_phase() expects StateUpdate passthrough
`run_phase()` in `pipeline.py` has the signature `(phase_name, update, phase_fn)` where `phase_fn: StateUpdate -> StateUpdate`. `FactionDecisionPhase.execute()` returns `list[FactionDirective]`. Do NOT wrap in a fake StateUpdate. Wire with a direct inline block (cadence gated), consistent with how some phases produce side-channel outputs (e.g. `generator._last_id` assignment after ecology/spawn calls).

### Risk 2: SystemCadence extension requires care
`SystemCadence` is a frozen Pydantic `BaseModel`. Adding `faction_decision: int = Field(10, ge=1)` is safe (it has a default, so all existing call sites pass unchanged). Verify no test or integration constructs `SystemCadence` with positional arguments — they should not, since Pydantic uses keyword args.

### Risk 3: E53Ac consumption point not yet defined
E53Ab produces `list[FactionDirective]` as a local variable. E53Ac must consume it in the same `refine()` invocation. The exact threading mechanism (parameter injection, `run_phase()` closure capture, or a per-tick scratch attribute on state) must be decided. **Recommendation**: capture via closure in the lambda for E53Ac's `run_phase()` call — matches how `recent_world_events` is captured for WorldEmergencePhase.

### Open Question 1: Cadence value
Should `faction_decision` default to 10 (matching `strategic_intelligence`) or 5? The ticket scope says "every 10 ticks, matching strategic_intelligence cadence." Use 10 as default.

### Open Question 2: GovernorPolicy parameter
The ticket signature has `policy: GovernorPolicy` as the second parameter. Confirm at implementation: the pipeline calls `FactionDecisionPhase.execute(state, policy=self._current_policy)` or just `execute(state, cadence)`. Since `policy` is not used in the decision logic described, `cadence` is more useful. Keep `policy: GovernorPolicy` in the signature for extensibility but it may be unused in E53Ab.

---

## Anti-Drift Hazards

1. **DO NOT add a new member to `TickPhase` enum** (`src/engine/phases.py`). Phase 4 Baseline Freeze Contract is absolute.

2. **DO NOT persist `FactionDirective` objects in `AuthoritativeState`** (any field, including `factions`, `pressure_signals`, `recent_world_events`). They are transient per-tick scratch.

3. **DO NOT add `faction_directives` to `StateUpdate`** or any `*Update` dataclass. Directives are not state mutations; they are read-phase outputs consumed within the same `refine()` call.

4. **DO NOT wire through `GovernorPolicy`**. It is a governance config object, not a phase registry.

5. **DO NOT place faction decision logic inside `WorldDynamicsSystem.resolve_dynamics()`**. That system owns regional hazards, ecology, and spawning — not faction cognition.

6. **DO NOT use string constants for directive_kind as an IntEnum**. The ticket explicitly states string constants to keep E53B/C extensible without enum churn.
