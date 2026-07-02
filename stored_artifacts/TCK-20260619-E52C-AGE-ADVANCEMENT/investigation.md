# Investigation — TCK-20260619-E52C-AGE-ADVANCEMENT

## Findings

### age_ticks location
`src/core/state.py:L147` — `LifecycleComponent.age_ticks: int = 0` is the per-entity age counter.
Incremented each tick in `src/engine/apply.py:L95` (`new_age = life.age_ticks + 1`).

### Existing demographics domain
`src/domains/demographics/cohort.py` — E52A+E52B complete.
`PopulationCohort.bracket: str` already uses `"young"|"adult"|"elder"` string values.
No `get_age_bracket` function exists yet — to be added in this ticket.

### AttributeUpdate — the correct channel for entity attribute modification
`src/core/updates.py:L391` — `AttributeUpdate` provides integer deltas:
`strength_delta, agility_delta, vitality_delta, endurance_delta, intelligence_delta, spirit_delta, wisdom_delta, perception_delta, charisma_delta`.
This is the only correct, architecture-compliant way to modify attributes (EntityState is frozen; direct mutation is prohibited by architecture rules).

### Mapping ticket modifiers to AttributeUpdate fields
The ticket's conceptual modifiers map to the V2 attribute system as follows:

| Ticket modifier | Attribute delta fields |
|---|---|
| `combat_effectiveness *= 0.7` | `strength_delta`, `agility_delta` (−30% of current values) |
| `mortality_rate *= 2.0` | `vitality_delta`, `endurance_delta` (−50% of current values, representing increased mortality pressure) |
| `knowledge_reputation_weight *= 1.3` | `wisdom_delta`, `charisma_delta` (+30% of current values) |

Mechanics Bible §1 (Chapter 01) confirms all nine attributes scale 1–99; deltas derived by rounding are within bounds.

### No existing age bracket advancement service
No `ElderModifierService` or similar exists in the codebase. This ticket creates:
1. Pure function `get_age_bracket(age_ticks: int) -> str` (deterministic, no state)
2. Pure function `compute_elder_attribute_update(entity_id: int, attrs: AttributeComponent, age_ticks: int) -> Optional[EntityUpdate]`
   — returns `None` for non-elder; `EntityUpdate(entity_id, attributes=AttributeUpdate(...))` for elders

### Architecture decisions
- No engine-phase wiring is needed by the acceptance criteria. The modifier function is testable standalone.
- The `DemographicCycleService` does not need to be extended — entity-level modifiers are separate from population-level cohort updates.
- Functions are pure/static — deterministic given same inputs.
- `mortality_rate` at entity level → vitality/endurance reduction (biological layer), consistent with Mechanics Bible §4 biological laws.
