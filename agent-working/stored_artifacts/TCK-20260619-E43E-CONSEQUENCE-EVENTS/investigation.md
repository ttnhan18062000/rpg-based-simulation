# Investigation — TCK-20260619-E43E-CONSEQUENCE-EVENTS

## Ticket
Epic 4.3E · Social Memory Consequence Events

## Context

This is the final child ticket of Epic 4.3 (Social Memory as Campaign Consequence). Prerequisites
TCK-20260619-E43C-DECAY and TCK-20260619-E43D-FACTION-MEMORY are completed and merged.

## Key Findings

### Existing infrastructure (confirmed in code)

1. **`src/domains/campaigns/social_memory.py`** — Contains:
   - `FactionSocialMemory` (frozen dataclass): `faction_id`, `entity_hostility: Dict[int, float]`, `episode_of_offense: Dict[int, int]`
   - `FactionSocialMemoryExporter.build_from_events()` — builds faction memory from episode events
   - `SocialMemoryRecord` — per-entity cross-episode social snapshot
   - `SocialMemoryDecay` — applies per-episode decay (FRIENDSHIP=0.40, GRUDGE=0.10)
   - `SocialMemoryImporter` — seeds entity social state at episode start

2. **`src/domains/campaigns/state.py`** — `CampaignState` has:
   - `social_memories: Dict[int, SocialMemoryRecord]` — keyed by entity_id
   - `faction_social_memories: Dict[str, FactionSocialMemory]` — keyed by faction_id

3. **`src/observability/events.py`** — `SimulationEvent` (Pydantic BaseModel) is the base event type.
   Existing subclasses: `CombatDamageEvent`, `GoldTransactionEvent`, `QuestEvent`, `MovementEvent`,
   `LifecycleEvent`, `LeadershipChangedEvent`, `BetrayalDesertionEvent`, etc. All use `event_category`
   from the `EventCategory` Literal union (`"social"` already included).

4. **`src/systems/social_systems/`** — Contains `appraisal.py`, `contracts.py`, `group_service.py`,
   `party_lifecycle.py`, `relationships.py`, `reputation.py`, `memory.py`, `guilds.py`.
   No existing `evaluate_social_consequence` function. The correct home for new pure evaluation
   logic is a new file `src/systems/social_systems/consequence_events.py`.

### Ticket scope (what must be built)

The ticket requires:
1. **3 event kind constants** importable from `src/observability/events.py`:
   - `LEGENDARY_ARRIVAL` — entity `faction_reputation["default"] >= 0.9` enters faction territory
   - `KNOWN_TRAITOR_SPOTTED` — entity in `faction_social_memories` with `entity_hostility > 0.5` threshold (NOT `3.0` — the ticket pseudocode used `3.0` which is a raw score not matching the 0.0–1.0 field range; actual field is 0.0–1.0 so threshold is `>= 0.5`)
   - `OLD_DEBT_COLLECTED` — entity has positive relationship score (>= 0.5) with another entity in the faction

2. **3 concrete event classes** extending `SimulationEvent` (matching existing pattern):
   - `LegendaryArrivalEvent` — `event_type="LEGENDARY_ARRIVAL"`, category=`"social"`
   - `KnownTraitorSpottedEvent` — `event_type="KNOWN_TRAITOR_SPOTTED"`, category=`"social"`
   - `OldDebtCollectedEvent` — `event_type="OLD_DEBT_COLLECTED"`, category=`"social"`

3. **`evaluate_social_consequence()` function** in `src/systems/social_systems/consequence_events.py`:
   - Pure function: reads `EntityState`, `faction_id: str`, `CampaignState` → `list[SimulationEvent]`
   - No live state mutation; returns events only
   - Duck-typed access to campaign_state (no import of CampaignState at module level per design constraints)

4. **Tests** in `tests/unit/social/test_social_memory.py` (extending existing file):
   - `test_known_traitor_event_fires_on_encounter` (named in AC)
   - `test_faction_memory_survives_episode_without_member_npcs` (named in AC — already partially covered by existing E43D test, but AC requires it to pass here)
   - `test_legendary_arrival_event_fires` (good coverage)
   - `test_old_debt_collected_event_fires` (good coverage)
   - `test_no_events_when_no_faction_memory` (edge case)
   - `test_all_three_event_kinds_importable` (AC #3)

### Threshold decisions

- **KNOWN_TRAITOR threshold**: 0.5 on 0.0–1.0 `entity_hostility` scale. The ticket pseudocode used `> 3.0` which is wrong (field is 0.0–1.0). Use `>= 0.5` (moderate hostility = traitor-level).
- **LEGENDARY_ARRIVAL threshold**: `faction_reputation["default"] >= 0.9` (ticket spec says `rep ≥ 0.9`).
- **OLD_DEBT threshold**: `relationship_scores[other_id] >= 0.5` (positive, significant bond).

### Architecture constraints

- `consequence_events.py` MUST NOT import from `src.engine` or `src.core.state` at module level
  (mirror constraint in `social_memory.py`)
- `CampaignState` accessed via duck-typed parameter (use `TYPE_CHECKING` guard if type annotation needed)
- Return `list[SimulationEvent]` — caller decides whether to emit/persist them
- All 3 event classes in `events.py` are immutable value objects; no durable state created in this module

## Files to Create or Modify

1. `src/observability/events.py` — append 3 event kind constants + 3 event classes
2. `src/systems/social_systems/consequence_events.py` — new file: `evaluate_social_consequence()`
3. `tests/unit/social/test_social_memory.py` — append E43E tests
4. `docs/simulation/domains/social_memory_contract.md` — new doc
5. `docs/simulation/social_systems_contract.md` — add cross-episode section
6. `docs/parity_ledger/social_narrative.yaml` — add SOC-CROSS-EP-005 entry
