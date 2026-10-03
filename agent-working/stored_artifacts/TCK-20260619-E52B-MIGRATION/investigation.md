# Investigation — TCK-20260619-E52B-MIGRATION

## Context Scanned

- `mcp__knowledge-search__search_docs` query: "population migration cohort region movement demographics pressure"
- `graphify query "population migration cohort region demographics"` — confirmed E52A nodes: RegionState.population_cohorts, DemographicCycleService, test_demographics.py
- E52A ticket (done): PopulationCohort + DemographicCycleService birth/death cycle in `src/domains/demographics/cohort.py`
- Epic parent: TCK-20260619-E52-DEMOGRAPHICS (done)

## Key Findings

### Scarcity Computation
- `ResourceEcologyService` (src/world/ecology.py) uses `node.remaining_charges / node.max_charges` per node.
- Ticket spec: scarcity = aggregate `remaining_charges / max_charges` across all resource nodes in the region; zero resources → scarcity 1.0.
- Resource nodes are looked up via `state.resource_nodes` (Dict[int, ResourceNodeState]); each node has a `position: tuple[float, float]`.
- Region membership is determined by bounds containment: `xmin <= px < xmax and ymin <= py < ymax`.

### Adjacency
- `docs/mechanics/06_worldbuilding_foundation.md`: regions are strictly disjoint by bounds (no overlap).
- Adjacency = bounds share a border edge: one axis aligns exactly (e.g., source xmax == neighbor xmin) while the other axis intervals overlap (non-degenerate).
- `LegalityServiceV2.is_adjacent()` is tile-level (Manhattan distance == 1), not region-level — not usable here.
- Must implement region-level adjacency directly from bounds.
- Determinism: sort candidates by region id before selecting.

### Update Mechanism
- No `CohortTransferUpdate` type exists. Using `WorldUpdate.population_cohorts_set` (existing field, E52A) to express both the source deduction and target addition as separate WorldUpdate entries.
- Source: cohort.count reduced by emigrant_count; target: cohort.count increased by emigrant_count (or new cohort created if bracket absent).
- `WorldEventCategory.POPULATION_MIGRATION` must be added to schema.py (E52A only added BIRTH/DEATH).

### Migration Logic
- Runs inside `process_demographics()` at COHORT_INTERVAL multiples, after birth/death pass.
- `_check_migration()` is a helper that collects WorldUpdate pairs and WorldEvents.
- Only fires if `scarcity > cohort.migration_threshold`; emigrant_count = max(1, int(cohort.count * 0.30)).
- If no adjacent regions, skip cohort.
- Target = `min(sorted_adjacent, key=lambda r: compute_regional_scarcity(r, state))` — deterministic because sorted by id first as tiebreaker.

### Tests
- Unit: `test_migration_pressure_triggers_on_scarcity_threshold` in `tests/unit/world/test_demographics.py`
- Integration: `test_cohort_migrates_on_scarcity` in `tests/integration/scenarios/test_demographics.py` (new file)

## No Duplicate Work Found
No prior migration implementation exists. E52A left migration_threshold on PopulationCohort as placeholder for this ticket.
