---
ticket_id: TCK-20260619-E53C-WAR
phase: scope
date: 2026-06-22
---

# Investigation — TCK-20260619-E53C-WAR (Epic 5.3C · Territorial Conflict & War)

## What Exists

### Predecessor epics (E53A, E53B) — scoped but not yet implemented
- **E53A child tickets** (E53Aa–E53Ad) define: `FactionState` frozen dataclass in `src/core/state.py`, `FactionUpdate` in `src/core/updates.py`, `FactionDecisionPhase` sub-phase (run inside `TickPhase.INIT`), directive propagation to entity scoring, `FactionAwarenessService` for tension updates.
- **E53B child tickets** (E53Ba–E53Bd) define: `DiplomaticState` str enum, `DiplomaticStateMachine`, diplomatic `FactionDirective` subtypes, `WorldEvent` emission for `WAR_DECLARED` / `ALLIANCE_FORMED` / `PEACE_TREATY`, and `NarrativeLedger` wiring via `CampaignOrchestrator`.
- E53C's `MilitaryConflictPhase` **depends on both sets being complete** before implementation begins.

### RegionState (src/core/state.py:L208)
- `owner_faction_id: Optional[int]` already exists — the foreign-key bridge between territory and faction.
- No `service_availability`, `siege_state`, or `siege_progress` field exists today; these must be added.
- `RegionState` is `frozen=True, slots=True` — adding fields follows the same pattern as E52A's `population_cohorts` addition.

### WorldUpdate (src/core/updates.py:L747)
- `owner_faction_id_set: Optional[int]` already exists in `WorldUpdate` — the authoritative channel for territory transfer.
- The apply-path in `src/engine/apply_plan.py:L119` already handles this field (`own = r_upd.owner_faction_id_set if ... else reg.owner_faction_id`).
- **RegionSovereigntyUpdate is not needed as a new type** — `WorldUpdate.owner_faction_id_set` already covers the territory transfer. The ticket scope uses the term loosely; the implementation must use `WorldUpdate`.
- `service_availability_delta` and `siege_progress_set` fields must be added to `WorldUpdate` for siege mechanics.

### GroupRecord (src/core/state.py:L514)
- `GroupRecord.roles: Dict[int, str]` maps `entity_id → role_name`.
- The ticket scope calls for `GroupRecord.roles["FACTION_SQUAD"]` — but `roles` is keyed by entity_id (int), not role name. This means squad commitment adds participating entities with role value `"FACTION_SQUAD"`.
- No special new type needed; the existing `GroupRecord` model is the durable holder.

### FactionState (planned, not yet built — E53Aa)
- Will have: `military_strength: float`, `tension_level: float`, `diplomatic_relations: Dict[str, DiplomaticState]`, `territory: List[str]`, `active_doctrines: List[str]`.
- E53C needs: `military_strength` (for war exhaustion), access to `diplomatic_relations` (to identify WAR-state faction pairs), and the ability to produce `FactionUpdate.military_strength_delta`.

### FactionDecisionPhase (planned — E53Ab)
- Runs as a sub-phase inside `TickPhase.INIT`, similar to `WorldEmergencePhase` pattern.
- E53C adds `MilitaryConflictPhase` as a second sub-phase, running **after** `FactionDecisionPhase` in the same tick slot.
- Receives: `AuthoritativeState`, recent `WorldEvent` list.
- Produces: `StateUpdate` with `WorldUpdate` deltas (siege progress, service availability), `GroupRecord` mutations (squad commitment), and eventually `FactionUpdate` (war exhaustion, military_strength delta).

### Authoritative pipeline (src/engine/apply_plan.py)
- The apply-path already handles `WorldUpdate.owner_faction_id_set` at L119.
- New fields (`service_availability_delta`, `siege_progress_set`) added to `WorldUpdate` will slot into `apply_plan.py` following the merge pattern already in place.
- `FactionUpdate.military_strength_delta` apply-path is part of E53Aa scope; E53C extends it with war exhaustion logic.

### NarrativeLedger / WorldEvent pipeline (E53Bd — planned)
- E53Bd will wire `WAR_DECLARED` as a `WorldEvent` into `NarrativeLedger`.
- E53C produces additional events: `SIEGE_STARTED`, `TERRITORY_TRANSFERRED`, `WAR_ENDED_EXHAUSTION` — these should also flow through the same `WorldEvent → NarrativeLedger` pipeline.

### Chronicle naming (E53D — blocked on E53C)
- `src/domains/chronicle/naming.py:L39` already has `"WAR_DECLARED": "The {subject} War Declaration"` template.
- E53D will extend this to name full wars and alliances ("The Thornwood War of Year 3"). E53C does not touch `naming.py`.

### Combat formula (docs/mechanics/02_combat_laws.md)
- Faction squads use standard entity combat — no special-casing. The ticket scope is explicit: "Do NOT special-case siege combat." Entity scoring (via E53Ac directive propagation) drives GUARD + WARRIOR entities to contest regions; their combat resolves through the existing pipeline.

### Integration test fixture
- `tests/integration/scenarios/test_faction_campaign.py` does not exist yet; it must be created as part of E53Cc (the integration test + territory transfer ticket).

## What Is Needed

Four implementation units as child standard tickets:

| Child | Scope | Key artifacts touched |
|---|---|---|
| E53Ca | `MilitaryConflictPhase` registration: phase class skeleton, engine wiring, `WAR_DECLARED` event detection | `src/engine/military_conflict.py`, `src/engine/kernel.py` or cadence wiring |
| E53Cb | Squad commitment + siege state model: `SiegeState` frozen dataclass, `RegionState.siege_state` field, `service_availability` field on `RegionState`, `WorldUpdate.service_availability_delta`, squad `GroupRecord` mutation | `src/core/state.py`, `src/core/updates.py`, `src/engine/military_conflict.py` |
| E53Cc | Territory transfer via authoritative pipeline: `siege_progress` accumulation, `WorldUpdate.owner_faction_id_set` trigger at `siege_progress ≥ 1.0`, `TERRITORY_TRANSFERRED` WorldEvent, integration test `test_war_declared_and_territory_transferred` | `src/engine/military_conflict.py`, `src/engine/apply_plan.py`, `tests/integration/scenarios/test_faction_campaign.py` |
| E53Cd | War exhaustion + peace triggers: `military_strength -= 0.001/tick` at war, peace condition `military_strength < 0.3`, `WAR_ENDED_EXHAUSTION` WorldEvent, `DiplomaticState` transition WAR→NEUTRAL via existing state machine, unit test `test_war_exhaustion_ends_conflict` | `src/engine/military_conflict.py`, `src/domains/faction/diplomatic_state_machine.py` |

## Key Architectural Decisions

### Decision 1: MilitaryConflictPhase is a sub-phase of TickPhase.INIT
`TickPhase` is frozen (Phase 4 Baseline Freeze Contract). `MilitaryConflictPhase` runs as a second sub-phase within `TickPhase.INIT`, **after** `FactionDecisionPhase`. It is stateless (static `execute(state, recent_events)` method), following the `WorldEmergencePhase` pattern exactly. Wiring via `SystemCadence` or explicit call from `world_dynamics.py` / `kernel.py` to be resolved at E53Ca implementation time.

### Decision 2: SiegeState is a durable sub-record on RegionState
`SiegeState(attacker_faction_id: str, siege_progress: float, started_tick: int)` is a frozen dataclass that lives as `RegionState.siege_state: Optional[SiegeState]`. `None` means no active siege. This gives siege state full inspection visibility, deterministic serialization, and a clear lifecycle (start / progress / end). Alternative (flat fields on `RegionState`) was rejected: a composite struct is cleaner and avoids `Optional` proliferation on `RegionState`.

### Decision 3: service_availability as a float field on RegionState
`service_availability: float = 1.0` (range 0.0–1.0) is added to `RegionState`. The besieging faction's `MilitaryConflictPhase` emits `WorldUpdate.service_availability_delta = -0.05` per tick. The apply-path clamps to [0.0, 1.0]. Defender reinforcement emits a positive delta. This is a standard delta field following the pattern of `retaliation_pressure_delta` in `WorldUpdate`.

### Decision 4: Territory transfer uses existing WorldUpdate.owner_faction_id_set
No new `RegionSovereigntyUpdate` type is needed. When `siege_progress ≥ 1.0`, `MilitaryConflictPhase` emits `WorldUpdate(region_id=..., owner_faction_id_set=attacker_faction_id_int, siege_progress_reset=True)`. The existing apply-path at `apply_plan.py:L119` handles `owner_faction_id_set`. A new `siege_state_clear_set: bool` field on `WorldUpdate` signals the apply-path to zero out `RegionState.siege_state`.

### Decision 5: Squad commitment uses existing GroupRecord
No new data model needed for squad commitment. `MilitaryConflictPhase` identifies GUARD + WARRIOR entities near a contested region (using `AuthoritativeState.entities`) and produces a `StateUpdate` that upserts a `GroupRecord` with role `"FACTION_SQUAD"` for each committed entity. Entity scoring (E53Ac) already boosts patrol routes for entities with this role.

### Decision 6: War exhaustion is applied in MilitaryConflictPhase, triggers DiplomaticStateMachine
`MilitaryConflictPhase` emits `FactionUpdate.military_strength_delta = -0.001` for every faction pair in `DiplomaticState.WAR`. Peace trigger: when `military_strength < 0.3`, emit a `FactionDirective` (kind=`SEEK_PEACE`) that the existing `DiplomaticStateMachine` processes to transition WAR→NEUTRAL. This avoids duplicating state machine logic in `MilitaryConflictPhase`.

### Decision 7: Dependency chain is strictly linear
E53Ca → E53Cb → E53Cc → E53Cd. Each ticket depends on the prior. E53Ca creates the phase shell; E53Cb adds the siege model it operates on; E53Cc wires territory transfer which requires siege_progress; E53Cd adds exhaustion which requires the WAR diplomatic state (E53Bc) and the phase to operate within.

## Risk Notes

- **E53A + E53B must be complete before E53Ca begins.** `FactionState`, `FactionUpdate`, `DiplomaticState.WAR`, and `FactionDecisionPhase` are all required by `MilitaryConflictPhase`. The child tickets should note this hard dependency.
- `RegionState` uses `slots=True` — adding `siege_state` and `service_availability` fields must follow exact field-addition pattern (see E52A for precedent).
- `owner_faction_id: Optional[int]` is typed as `int` but `FactionState.faction_id` will be `str` (catalog-registered, per E53A investigation). The apply-path will need to handle the `str→int` coercion or `owner_faction_id` must be migrated to `str`. This must be resolved in E53Ca's investigation phase before touching `apply_plan.py`.
- The 3-faction, 3-episode integration test (`test_war_declared_and_territory_transferred`) will require a scenario fixture with 3 factions; no such fixture exists yet. E53Cc must author it.
