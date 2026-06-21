---
ticket_id: TCK-20260619-E53B-DIPLOMACY
phase: scope
date: 2026-06-22
---

# Investigation — TCK-20260619-E53B-DIPLOMACY (Epic 5.3B · Faction Diplomacy)

## What Exists

### FactionState + FactionUpdate (E53Aa — sibling, OPEN)
- `FactionState` frozen dataclass will live in `src/core/state.py` adjacent to `GroupRecord` (~L514).
- Fields relevant to diplomacy: `diplomatic_relations: Dict[str, str]` (faction_id → relation label string), `military_strength: float`, `tension_level: float`.
- `FactionUpdate.diplomatic_relations_set: Dict[str, str]` already planned as the mutation channel for diplomatic state changes.
- `AuthoritativeState.factions: Dict[str, FactionState]` will be the registry.
- **E53Ba must depend on E53Aa completing first** — it formalizes the `diplomatic_relations` string labels into typed `DiplomaticState` enum values.

### FactionDecisionPhase (E53Ab — sibling, OPEN)
- Will run as a sub-phase at `TickPhase.INIT` (TickPhase enum is FROZEN — no new phases allowed).
- Produces `FactionDirective` transient objects per tick.
- `FactionDirective` subtypes are the extension point for diplomatic actions (E53Bb adds diplomatic subclasses here).

### FactionAwarenessService (E53Ad — sibling, OPEN)
- Listens to world events and updates `tension_level` via `FactionUpdate`.
- Diplomatic state transitions (NEUTRAL→TENSE→HOSTILE) depend on `tension_level` already being populated by E53Ad; E53Bc must gate on this.

### NarrativeLedger (E32D — DONE)
- `NarrativeLedger` is a query/export facade over `CampaignState.narrative_ledger: List[NarrativeLedgerEntry]`.
- `NarrativeLedgerEntry.event_type` is a free string; existing values: `"quest_completed"`, `"entity_death"`, `"faction_shift"`, `"calamity"`.
- New event types needed: `"alliance_formed"`, `"war_declared"`, `"peace_treaty"` — no schema change required, just new string constants.
- `NarrativeLedgerEntry.significance` is a float 0.0–1.0 already, so no model changes needed.
- **Diplomatic events must flow through `CampaignOrchestrator._advance_state()`** — the orchestrator collects `AuthoritativeState.recent_world_events` and converts them to ledger entries. The diplomatic wiring must emit `WorldEvent` objects (from `src/domains/world_emergence/schema.py`) that the orchestrator can harvest.

### WorldEvent schema (existing)
- `WorldEvent` in `src/domains/world_emergence/schema.py` at L39 — already consumed by `CampaignOrchestrator`.
- Diplomatic events (ALLIANCE_FORMED, WAR_DECLARED, PEACE_TREATY) should be emitted as `WorldEvent` objects with a `category` and `payload` so the existing pipeline picks them up without new wiring paths.

### Grand Strategy (legacy, out of scope)
- `docs/systems/grand_strategy.md` has a crude `war_status: Dict[int, bool]` + `aggression` float approach.
- **Do not port this.** Build fresh with typed `DiplomaticState` enum and authoritative `FactionUpdate` path per V2 architecture.
- `src/systems/strategy_system.py` is legacy; leave it untouched.

## What Is Needed

| Gap | Where | Ticket |
|---|---|---|
| `DiplomaticState` str enum | `src/core/enums.py` or new `src/core/diplomatic.py` | E53Ba |
| Migrate `FactionState.diplomatic_relations` values from `str` to `DiplomaticState` | `src/core/state.py` + `src/core/updates.py` | E53Ba |
| `DiplomaticAction` dataclasses (TreatyOffer, TradeAgreement, NonAggressionPact, AllianceProposal, Betrayal) as `FactionDirective` subtypes | `src/engine/faction_decision.py` | E53Bb |
| `DiplomaticActionHandler` — applies diplomatic actions to `FactionState` via `FactionUpdate`, enforces acceptance/rejection logic | new `src/domains/faction/diplomatic_actions.py` | E53Bb |
| State machine transition logic: compute new `DiplomaticState` from tension + military_strength; produce `FactionUpdate` per pair | new `src/domains/faction/diplomatic_state_machine.py` | E53Bc |
| Wire state machine into `FactionDecisionPhase` (runs at INIT sub-phase) | `src/engine/faction_decision.py` | E53Bc |
| Emit `WorldEvent` for ALLIANCE_FORMED / WAR_DECLARED / PEACE_TREATY from state machine | same as above | E53Bd |
| `CampaignOrchestrator` harvests diplomatic `WorldEvent` → `NarrativeLedgerEntry` with correct significance values | `src/domains/campaigns/orchestrator.py` | E53Bd |

## Key Architectural Decisions

1. **DiplomaticState placement**: Add to `src/core/enums.py` alongside existing `Faction`, `EntityRole` enums — avoids a new module for a simple enum. This keeps the type accessible to both `src/core/state.py` and `src/engine/`.

2. **Transition authority**: The state machine (`DiplomaticStateMachine`) is pure logic — it reads `FactionState` objects and returns `FactionUpdate` objects. It does NOT mutate state directly. The `FactionDecisionPhase` calls the machine and collects updates, which flow through the authoritative apply path. This follows the same pattern as `FactionAwarenessService` (E53Ad).

3. **Diplomatic action handling**: `DiplomaticAction` subtypes are `FactionDirective` subtypes (transient, per-tick). The `DiplomaticActionHandler` processes them synchronously in the same sub-phase and produces `FactionUpdate` objects. No deferred queue needed at this tier.

4. **Betrayal semantics**: A `Betrayal` directive from faction A toward allied faction B transitions A→B relation from ALLIED to HOSTILE immediately (bypassing TENSE/NEUTRAL), and emits a high-significance WorldEvent. B→A also flips. Both covered in E53Bb handler.

5. **NarrativeLedger wiring**: Use the existing `WorldEvent` pipeline rather than direct `NarrativeLedgerEntry` injection. `FactionDecisionPhase` emits `WorldEvent` objects into `AuthoritativeState.recent_world_events`; `CampaignOrchestrator._advance_state()` converts these to `NarrativeLedgerEntry` records. This avoids coupling `src/engine/` directly to `src/domains/campaigns/`.

6. **War exhaustion and WAR→NEUTRAL**: The `DiplomaticStateMachine` checks `military_strength < 0.3` on both sides to trigger peace. The `FactionDecisionPhase` also provides the `HOSTILE→WAR` decision threshold (`military_strength > opponent * 1.2`). These checks run each tick during `TickPhase.INIT`.

7. **VASSAL state**: Not triggered by tension/war — only via explicit `AllianceProposal` with asymmetric military_strength (proposer has >2x strength). Handled in E53Bb action handler.

8. **Dependency order**: E53Ba → E53Bb → E53Bc → E53Bd (strict linear sequence; each depends on the previous).

## Test Strategy

- `tests/unit/faction/test_diplomacy.py` — new file housing all four tickets' unit tests
- E53Ba: round-trip serialization of `DiplomaticState` values in `FactionState`
- E53Bb: each diplomatic action type produces correct `FactionUpdate` output; betrayal triggers immediate ALLIED→HOSTILE
- E53Bc: all 5 valid state transitions fire under correct threshold conditions; invalid transitions are no-ops
- E53Bd: ALLIANCE_FORMED / WAR_DECLARED / PEACE_TREATY `WorldEvent` objects are harvested into `NarrativeLedgerEntry` with correct significance values

## Open Questions

- None blocking scope. E53Ba implementation must confirm whether `diplomatic_relations: Dict[str, DiplomaticState]` requires a pydantic validator change on `FactionUpdate` or if the str→enum coercion is automatic via `DiplomaticState(str, Enum)`.
