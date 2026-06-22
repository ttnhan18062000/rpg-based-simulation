# Faction System Contract

**Status**: DRAFT — E53Ba complete (DiplomaticState enum + migration). Pending E53Bb–Bd for full diplomacy coverage.

**Tickets**: E53Aa (FactionState), E53Ab (FactionDecisionPhase), E53Ac (directive propagation),
E53Ad (tension update), E53Ba (DiplomaticState enum), E53Bb–Bd (diplomacy actions), E53C (war).

---

## FactionState Schema

Defined in `src/core/state.py`. Field on `AuthoritativeState.factions: Dict[str, FactionState]`.

```
FactionState(frozen=True, slots=True)
  faction_id:            str                    — catalog-registered faction ID
  territory:             Tuple[str, ...]        — region IDs controlled by this faction
  resources:             Dict[str, int]         — resource stockpiles
  diplomatic_relations:  Dict[str, DiplomaticState]  — other faction_id → typed relation (E53Ba)
  active_doctrines:      Tuple[str, ...]        — active doctrine IDs
  military_strength:     float  (default 1.0)  — relative military power [0.0, ∞)
  tension_level:         float  (default 0.0)  — internal/external tension [0.0, 1.0]
```

**Mutation path**: `FactionUpdate` records accumulated in `StateUpdate.faction_updates`,
applied by `apply.py`. Never mutated in-place.

---

## FactionUpdate Schema

Defined in `src/core/updates.py`.

```
FactionUpdate(frozen=True, slots=True)
  faction_id:                str
  tension_delta:             float = 0.0       — clamped to keep tension in [0.0, 1.0]
  military_strength_set:     Optional[float]   — set absolute value if provided
  territory_add:             Tuple[str, ...]   — regions to add
  territory_remove:          Tuple[str, ...]   — regions to remove
  resources_delta:           Dict[str, int]    — accumulates per region
  diplomatic_relations_set:  Dict[str, DiplomaticState]  — overwrites matching keys (E53Ba)
  active_doctrines_set:      Optional[Tuple[str, ...]]
```

---

## DiplomaticState Enum (E53Ba)

Defined in `src/core/enums.py` as `DiplomaticState(str, Enum)`.

| Value | Meaning |
|---|---|
| `NEUTRAL` | No active relationship |
| `TENSE` | Strained relations; war risk elevated |
| `HOSTILE` | Active antagonism; combat likely |
| `WAR` | Declared war state |
| `ALLIED` | Mutual cooperation pact |
| `VASSAL` | Subordinate relationship |

**Serialization**: `FactionState.to_canonical_dict()` emits plain string values (`"ALLIED"`, etc.) for JSON
compatibility. `FactionState.from_dict()` coerces strings back via `DiplomaticState(v)`. The apply-path
(`src/engine/apply.py`) also coerces any raw string values during merge for robustness.

**Absence = NEUTRAL**: absence of a key in `diplomatic_relations` implies NEUTRAL — do not populate all pairs at construction.

---

## FactionDirective Schema

Defined in `src/engine/faction_decision.py`. **Transient** — never persisted.

```
FactionDirective(frozen=True, slots=True)
  faction_id:      str
  directive_kind:  str   — one of: DEFEND_BORDER | TRADE_ROUTE | COMMISSION_QUEST
  target_faction:  Optional[str]
  target_region:   Optional[str]
  priority:        float = 1.0
  created_tick:    int   = 0
```

---

## Directive Kinds

Constants defined in `src/engine/faction_constants.py`.

| Constant | Value | Emission condition |
|---|---|---|
| `DEFEND_BORDER` | `"DEFEND_BORDER"` | `tension_level > 0.5` AND `territory` non-empty |
| `TRADE_ROUTE` | `"TRADE_ROUTE"` | `military_strength > 0.7` AND `tension_level < 0.3` |
| `COMMISSION_QUEST` | `"COMMISSION_QUEST"` | `territory` non-empty (unconditional secondary) |

`DEFEND_BORDER` and `TRADE_ROUTE` are mutually exclusive per faction per tick (if/elif).
`COMMISSION_QUEST` is always emitted when territory is non-empty regardless of tension.

---

## Tension Mechanics

- `tension_level` is a float clamped to `[0.0, 1.0]` by the apply-path (`apply.py:345`).
- **RESOURCE_DEPLETED → +0.1 per event** (E53Ad): `FactionAwarenessService.compute_tension_updates()`
  scans `state.recent_world_events` for `WorldEventCategory.RESOURCE_DEPLETED` events whose
  `region_id` is in the faction's `territory`. Emits one `FactionUpdate(tension_delta=+0.1)`
  per matching event per faction. Multiple events in the same tick are additive; final
  tension is capped at 1.0 by the apply-path.
  **One-tick lag**: `state.recent_world_events` contains the previous tick's event window
  (state is frozen at tick entry — same lag as all WorldEmergencePhase signals).
- Decreases from: `FactionUpdate.tension_delta` with negative value (E53B+).
- Threshold effects: `> 0.5` triggers `DEFEND_BORDER` directive.

---

## Directive Propagation to Entity Scoring (E53Ac)

`FactionDecisionPhase.execute()` runs every tick before `AdventureDecisionPhase` in the
pipeline. Its output (`list[FactionDirective]`) is passed as `faction_directives` parameter
through `AdventureDecisionPhase.apply()` → `AdventureDecisionService.decide()` →
`AdventureRouteScorer.score()`.

### Urgency Adjustments

| Entity role | Route family | Condition | Urgency delta |
|---|---|---|---|
| `GUARD` | `HUNT_WEAK_ENEMY` | Any `DEFEND_BORDER` directive exists | `+2.0` |
| `SHOPKEEPER` | `GATHER_RESOURCE`, `SELL_LOOT_FOR_GOLD` | Any faction has `diplomatic_relations[*] == DiplomaticState.ALLIED` | `+1.5` |
| `HERO` | `QUEST_OPPORTUNITY` | Any `COMMISSION_QUEST` directive exists | `+3.0` |

Notes:
- If `faction_directives=None`, no adjustment is applied (backward-compatible default).
- `HUNT_WEAK_ENEMY` is used as the patrol proxy because `RouteFamily.PATROL` does not exist.
  This is an intentional design choice documented in `docs/guidelines/v2_intentional_divergences.md`.
- Urgency deltas are additive on top of the need-urgency calculation. Final scores above 1.0
  are expected and correct when multiple urgency sources compound.

---

## Pipeline Position

```
pipeline.py:refine()
  ...
  [Phase 8b]  FactionDecisionPhase.execute(state) → faction_directives  (every tick)
  [Phase 8c]  FactionAwarenessService.compute_tension_updates(state, events) → faction_updates
  [Phase 8d]  compute_transitions(factions) → transition_updates            (E53Bc)
              compute_common_enemy_pairs(factions) → alliance proposals      (E53Bc)
              events_from_transitions(...) → WorldEvent list                 (E53Bd)
              run_phase("diplomatic_transitions", ..., world_events_add=...) (E53Bd)
  [Phase 8e]  MilitaryConflictPhase.execute(state) → StateUpdate            (E53Ca–Cd)
              ├─ Orphan siege cleanup (WAR→NEUTRAL, siege_state_clear)       (E53Cd)
              ├─ get_war_pairs() → List[(fid_a, fid_b)]                      (E53Ca)
              ├─ War exhaustion drain: FactionUpdate(military_strength_set)  (E53Cd)
              ├─ WAR_ENDED_EXHAUSTION WorldEvent at ms < 0.3 crossing        (E53Cd)
              └─ Per WAR pair:
                 ├─ TERRITORY_TRANSFERRED: WorldUpdate(siege_state_clear) +  (E53Cc)
                 │  FactionUpdate(territory_add/remove) + WorldEvent
                 ├─ Siege initiation: WorldUpdate(siege_state_set)           (E53Cb)
                 ├─ Siege degradation: service_availability_delta=-0.05,     (E53Cb)
                 │  siege_progress_delta=+0.05
                 ├─ Defender reinforcement (≥3 GUARD): +0.02/-0.02 offset    (E53Cb)
                 └─ Squad commitment: GroupRecord(roles=FACTION_SQUAD)       (E53Cb)
  [Phase 3]   AdventureDecisionPhase.apply(state, faction_directives=..., factions=...)
  ...
```

---

## Diplomatic WorldEvent Emission (E53Bd)

Phase 8d emits `WorldEvent` objects into `StateUpdate.world_events_add` for the following transitions:

| Transition | WorldEventCategory | significance |
|---|---|---|
| HOSTILE → WAR | `FACTION_WAR_DECLARED` | 0.95 |
| WAR → NEUTRAL (exhaustion) | `FACTION_PEACE_TREATY` | 0.75 |
| Alliance proposal accepted | `FACTION_ALLIANCE_FORMED` | 0.80 |

`WorldEvent.subject` encodes the faction pair as `":".join(sorted([fid_a, fid_b]))` for deterministic
narrative ledger deduplication. One event is emitted per pair per tick.

`CampaignOrchestrator._extract_narrative_entries()` maps these via `_SIGNIFICANCE_MAP` to
`NarrativeLedgerEntry` records with `event_type` values: `war_declared`, `peace_treaty`, `alliance_formed`.

**Known deferral (E53Da):** Chronicle `naming.py` uses uppercase event type keys (`WAR_DECLARED`) while
`_SIGNIFICANCE_MAP` emits lowercase (`war_declared`). Alignment is tracked in the E53Da ticket.

---

## Military Conflict WorldEvent Emission (E53Ca–Cd)

Phase 8e (`MilitaryConflictPhase`) emits additional `WorldEvent` objects:

| Event | WorldEventCategory | significance | subject format |
|---|---|---|---|
| Siege complete → ownership transfer | `TERRITORY_TRANSFERRED` | 0.85 | `"{attacker}:{defender}:{region_id}"` |
| War exhaustion crosses 0.3 threshold | `WAR_ENDED_EXHAUSTION` | 0.80 | `"{fid_a}:{fid_b}"` |

### SiegeState lifecycle

1. **Initiation** (tick 1 of WAR): `WorldUpdate.siege_state_set = SiegeState(attacker, defender, progress=0.0, started_tick)` on the contested region.
2. **Degradation** (each tick): `service_availability_delta=-0.05`, `siege_progress_delta=+0.05`. Defender reinforcement (≥3 GUARD entities) applies `+0.02` offset to both.
3. **Transfer** (tick where `siege_progress >= 1.0`): `siege_state_clear=True`, `service_availability_delta=+1.0`, `FactionUpdate(territory_add/remove)`, `TERRITORY_TRANSFERRED` WorldEvent.
4. **Orphan cleanup** (any tick where siege exists but factions are no longer at WAR): `siege_state_clear=True`, `service_availability_delta=+1.0`.

**Note on `RegionState.owner_faction_id`:** This field is `Optional[int]` and is NOT updated during territory transfer. The authoritative ownership record is `FactionState.territory: Tuple[str, ...]`. The int/str type mismatch is a known limitation (FAC-010).

### War exhaustion

Each WAR faction drains `military_strength` by `0.001/tick` (flat, deduped per faction). When `military_strength` crosses below `0.3`, `WAR_ENDED_EXHAUSTION` is emitted. The autonomous `WAR→NEUTRAL` transition fires via Phase 8d `DiplomaticStateMachine.compute_transitions()` when both faction `military_strength < 0.3` on the prior state.

---

## Parity Ledger

See `docs/parity_ledger/faction.yaml` (FAC-001 through FAC-011, FACTION-TENSION-001) and
`docs/parity_ledger/strategic_cognition.yaml` (FACTION-DIR-001).
