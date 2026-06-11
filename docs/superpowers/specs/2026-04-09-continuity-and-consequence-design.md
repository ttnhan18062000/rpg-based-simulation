---
status: archive
authority: P2
audience: historical
layer: misc
original_date: 2026-04-09
---

# Design Spec: Continuity and Consequence Core Models (Phase 4 Stage 1)

**Date**: 2026-04-09
**Status**: DRAFT
**Phase**: Phase 4 (Inheritance and Succession)
**Authors**: Antigravity

## 1. Goal
The goal of this design is to establish the core data structures for Phase 4, enabling the simulation to transition from episodic behavior to durable historical continuity. This involves tracking entity successions, household legacy, regional stability, and localized "scars" from major events.

## 2. Architecture Overview
The system follows a hybrid approach:
- **State Records**: Store current and historical status for specific units (Households, Regions, Scars).
- **History Registry**: A central ledger of "Events" that provides the causal justification (the "Why") for changes in state records.

This architecture ensures that the world has both **Status** (How it is now) and **History** (What made it this way).

---

## 3. Data Models

### 3.1 World History
**`HistoricalEvent`** (Model)
- `event_id: str`: Unique identifier.
- `tick: int`: Simulation tick timestamp.
- `kind: EventKind`: Enum (`DEATH`, `RAID`, `BOSS_FALL`, `HOUSEHOLD_FOUNDED`, etc.)
- `location: Vector2 | None`: Spatial anchor.
- `involved_ids: set[int]`: References to involved entities or buildings.
- `tags: list[str]`: Narrative metadata for filtering (e.g., `["heroic", "tragic"]`).

---

### 3.2 Continuity Models

**`HouseholdRecord`** (File: `src/core/models/households.py`)
- `household_id: str`: Unique ID.
- `home_building_id: int`: Reference to building.
- `member_ids: set[int]`: Current living members.
- `former_member_ids: list[int]`: Historical roster.
- `reputation: float`: Dynamic status scalar.
- `storage_id: str | None`: Link to persistent shared storage.
- `related_event_ids: list[str]`: Pointer to `WorldHistoryRegistry` entries.
- `legacy_tags: list[str]`: Inherited traits or status.

**`SuccessorRecord`** (File: `src/core/models/continuity.py`)
- `source_entity_id: int`: The predecessor.
- `successor_entity_id: int | None`: The heir (if assigned).
- `household_id: str`: The house receiving the legacy.
- `motive_fragments: dict[str, Any]`: Residual AI drives to transfer.
- `death_event_id: str`: Link to the specific event.

---

### 3.3 Consequence Models

**`LocalScarRecord`** (File: `src/core/models/local_scars.py`)
- `location_pos: Vector2`: Exact world point.
- `kind: ScarKind`: Enum (`RAID_DAMAGE`, `BATTLE_FIELD`, `FEAR_ZONE`).
- `severity: float`: 0.0 to 1.0.
- `created_tick: int`: When it occurred.
- `recovery_rate: float`: Decay speed.
- `source_event_id: str`: Link to historical cause.
- `behavioral_modifiers: dict[str, float]`: Effects on local AI (e.g., evasion).

**`RegionConsequenceRecord`** (File: `src/core/models/regions.py`)
- `region_id: str`: Link to static Region.
- `danger_level: float`: Dynamic difficulty shift.
- `stability: float`: 0.0 to 1.0 (effects routine reliability).
- `control_pressure: dict[int, float]`: Faction influence metrics.

---

## 4. Integration & Storage
All records will be stored in registries within the `WorldState`. New registries to add:
- `world_history`: `dict[str, HistoricalEvent]`
- `household_registry`: `dict[str, HouseholdRecord]`
- `scar_registry`: `list[LocalScarRecord]` (Spatial query optimized)
- `region_consequences`: `dict[str, RegionConsequenceRecord]`

---

## 5. Clean Code & AOA Standards
- **Isolation**: Each model inherits from `SimulationModel` for snapshot compatibility.
- **Naming**: Intention-revealing nouns (e.g., `LocalScarRecord` instead of `Consequence`).
- **Safety**: No direct object pointers; all cross-linking uses IDs.
- **Small Classes**: Models will be isolated in dedicated files to maintain SRP.

---

## 6. Verification
- Unit tests for each model's serialization (JSON -> Dict -> Model).
- Integration test for `WorldState` snapshot/recovery of the new registries.
