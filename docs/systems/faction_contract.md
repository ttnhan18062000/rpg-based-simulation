---
status: authoritative
layer: systems
authority: P1
audience: developer
last_verified: 2026-06-23
---

# Faction System Contract

**Status**: AUTHORITATIVE — E53A–E53D complete. Last verified: 2026-06-23.
Replaces: `docs/archive/grand_strategy_v1.md`.

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
  directive_kind:  str   — one of: DEFEND_BORDER | TRADE_ROUTE | COMMISSION_QUEST | EXPAND_TERRITORY
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
| `EXPAND_TERRITORY` | `"EXPAND_TERRITORY"` | mean `compute_regional_scarcity()` (`src/domains/demographics/cohort.py`) over `fs.territory` > `0.7` AND a faction-less region exists (`RegionState.owner_faction_id is None`) |

`DEFEND_BORDER` and `TRADE_ROUTE` are mutually exclusive per faction per tick (if/elif).
`COMMISSION_QUEST` is always emitted when territory is non-empty regardless of tension.
`EXPAND_TERRITORY` is independent of (not mutually exclusive with) the other three — a faction
under both high tension and population pressure emits both `DEFEND_BORDER` and
`EXPAND_TERRITORY` the same tick. Target resolution deterministically picks the lowest-id
faction-less region (`_resolve_expand_territory_target`, sorted `state.regions` iteration);
`compute_population_density()` is read too but only contributes to `priority` scaling, never to
the gate itself. Target resolution is scoped to `RegionState.owner_faction_id` only — no
Camp/Nest-as-conquest-target or City-ownership-aware (idea 35) logic (TCK-20260904-FACTION-EXPAND-DIRECTIVE).

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

`FactionDecisionPhase.execute()` runs every tick, producing `list[FactionDirective]`. **As of
TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE this list is no longer threaded into the live
adventure-routing call path.** The dedicated `AdventureDecisionPhase` pipeline stage that used to
receive `faction_directives` as a direct `apply()` argument has been deleted; the surviving tier-5
entry point, `AdventureGoalScorer.score(entity, state)` (`src/ai/goals/adventure_scorer.py`), has
no `state.faction_directives` attribute to read and calls `AdventureDecisionService.decide()` with
`faction_directives=None` unconditionally (see `docs/mechanics/04_strategic_cognition.md` §6.10,
which discloses the same gap). The urgency-adjustment table below remains an accurate description
of `AdventureRouteScorer.score()`'s own scoring logic when `faction_directives` is supplied (e.g.
via direct test calls), but describes a condition that does not occur in a live tick today — a
disclosed simplification, not implemented parity.

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
              faction_directives (including EXPAND_TERRITORY) is additionally threaded, same
              tick, into the later "world_dynamics" phase (pipeline.py:343,
              WorldDynamicsSystem.resolve_dynamics() → CampService.process_camps()) — a second,
              real consumption point alongside the (disclosed-dead) urgency-scoring path
              described under "Directive Propagation to Entity Scoring"
              (TCK-20260904-FACTION-EXPAND-DIRECTIVE).
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
  [Tier 5]    AdventureGoalScorer.score(entity, state)  (faction_directives NOT threaded — see
              "Directive Propagation to Entity Scoring" above; runs via
              StrategicIntelligenceSystem.evaluate_strategic_intent(), not a dedicated pipeline
              phase — AdventureDecisionPhase was deleted by
              TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE)
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

## NarrativeLedger Integration (E53Bd / E53Cc / E53Db)

All faction WorldEvents are harvested by `CampaignOrchestrator._extract_narrative_entries()` into
`NarrativeLedgerEntry` records. Only categories present in `_SIGNIFICANCE_MAP` are recorded.

### Significance values (authoritative — all verified)

| event_type | significance | WorldEventCategory | Source ticket |
|---|---|---|---|
| `war_declared` | 0.95 | `FACTION_WAR_DECLARED` | E53Bd |
| `alliance_formed` | 0.80 | `FACTION_ALLIANCE_FORMED` | E53Bd |
| `peace_treaty` | 0.75 | `FACTION_PEACE_TREATY` | E53Bd |
| `territory_transferred` | 0.85 | `TERRITORY_TRANSFERRED` | E53Cc |
| `war_ended_exhaustion` | 0.80 | `WAR_ENDED_EXHAUSTION` | E53Cd |
| `siege_begins` | 0.80 | `SIEGE_BEGINS` | E53Db |
| `betrayal` | 0.85 | `BETRAYAL` | E53Db |

Chronicle threshold: `CHRONICLE_THRESHOLD = 0.5` — all 7 faction event types exceed this.

### SIEGE_BEGINS emission

Emitted by `MilitaryConflictPhase.execute()` in `src/engine/military_conflict.py` on the first tick
a siege is established on a region (`reg.siege_state is None` before the update).
`WorldEvent.subject = contested_region_id` (enables `ChronicleNamer` region template: `"The Siege of {region_name}"`).

### BETRAYAL emission

Detected by `events_from_transitions(betrayal_updates=[...])` in `src/domains/faction/diplomatic_state_machine.py`.
`betrayal_updates` contains `FactionUpdate` records that move a relation from `ALLIED` → `HOSTILE`
(via `DiplomaticActionHandler._handle_betrayal()`). `WorldEvent.subject = ":".join(sorted([betrayer_id, betrayed_id]))`.

---

## Chronicle Integration (E53Da / E53Dc)

### ChronicleNamer templates for faction events

Defined in `src/domains/chronicle/naming.py`:

| event_type | Template | subject format |
|---|---|---|
| `war_declared` | `The {source_faction} War against {target_faction}` | `"fid_a:fid_b"` |
| `alliance_formed` | `The {source_faction}–{target_faction} Alliance` | `"fid_a:fid_b"` |
| `peace_treaty` | `The Peace of {source_faction} and {target_faction}` | `"fid_a:fid_b"` |
| `betrayal` | `The Betrayal of {source_faction} by {target_faction}` | `"fid_a:fid_b"` |
| `territory_transferred` | `The Conquest of {region_name}` | `region_id` |
| `siege_begins` | `The Siege of {region_name}` | `region_id` |

For dual-faction templates, `subject_id` encodes the sorted pair `"sorted_fid_a:sorted_fid_b"`.
`source_faction`/`target_faction` are resolved via `faction_names` dict (fallback to raw ID).

### Era names for faction events

| event_type | ERA_NAMES value |
|---|---|
| `war_declared` | `"The Age of War"` |
| `alliance_formed` | `"The Age of Alliances"` |
| `territory_transferred` | `"The Age of Conquest"` |

### ChronicleCompiler.compile() params (E53Dc)

```python
compiler.compile(
    campaign_state,
    output_dir="...",
    entity_names={int: str},    # entity id → display name
    faction_names={str: str},   # faction_id → display name
    region_names={str: str},    # region_id → display name
)
```

Both `faction_names` and `region_names` default to `None` (backward-compatible).

---

## Parity Ledger

- `docs/parity_ledger/social_narrative.yaml` — SOC-FAC-001 through SOC-FAC-010, SOC-CHRON-001 through SOC-CHRON-006
- `docs/parity_ledger/faction.yaml` — FAC-001 through FAC-011, FACTION-TENSION-001
- `docs/parity_ledger/strategic_cognition.yaml` — FACTION-DIR-001
