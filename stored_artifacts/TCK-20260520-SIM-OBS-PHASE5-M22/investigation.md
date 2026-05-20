# Investigation - Entity Inspector V1 (Milestone 22)

## 1. Concurrency Analysis
- The main simulation tick loop executes inside a dedicated daemon thread `v2-engine-loop` spawned by `V2EngineManager`.
- Concurrency control is achieved using `threading.Lock` under `V2EngineManager._state_lock`.
- `V2EngineManager` preserves the latest successfully completed tick state in `_latest_state`.
- All operations on `_latest_state` are read-only and immutable. `EntityState` itself implements components with frozenset and tuple collections to ensure immutability during serialization.
- Reading the latest state inside `EntityInspector` must hold the `_state_lock` briefly to clone or extract the entity state, preventing any interference with thread progression.
- Retaining event timelines: The `Kernel` indexes simulation events to `EntityTimelineStore`. The store has its own internal thread-safe `threading.Lock` covering `_timelines` mutation, ensuring non-blocking reads.

## 2. API Schema Selection
The following compact fields are specified in `obs_sim_phase5.md` for `EntityInspectionSnapshot`:
- `entity_id` (int): Entity identifier.
- `exists` (bool): `True` if found.
- `alive` (bool): `True` if combat hp > 0 and alive.
- `position` (tuple[float, float]): Navigational position coordinates.
- `faction_id` (int): Faction ID.
- `region_id` (Optional[str]): Active regional ID.
- `current_goal` (Optional[str]): Current strategic objective/project ID.
- `current_target` (Optional[str]): E.g., target node or coordinates.
- `current_action` (Optional[str]): The kind of task being performed.
- `combat_summary` (dict): hp, max_hp, tactical role.
- `inventory_summary` (dict): gold, items count, slots.
- `quest_summary` (list[dict]): Compact list of active quest details.
- `strategic_summary` (dict): count of blockers, leads, contracts, boredom levels.
- `recent_timeline_events` (list[dict]): A list of serialized events.
- `latest_rejection_reason` (Optional[str]): Latest failed interaction/movement.
- `latest_anomaly_flags` (list[str]): Deduced anomaly descriptors.

## 3. High Performance Resolution
- Resolving a single entity is $O(1)$ direct hash map lookup: `state.entities.get(entity_id)`.
- No full-world scans or filtering occur.
- Non-existent entities immediately abort and return a clean default snapshot with `exists=False`.
