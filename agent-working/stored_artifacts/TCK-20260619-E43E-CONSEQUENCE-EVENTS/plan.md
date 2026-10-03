# Implementation Plan — TCK-20260619-E43E-CONSEQUENCE-EVENTS

## Approach

This is an additive feature: new event kinds + classes in `events.py`, new pure evaluator
function in `consequence_events.py`, new tests in the existing test file, and doc updates.
No existing logic is modified.

## Step 1 — Add event kinds and classes to `src/observability/events.py`

Append after the existing `BetrayalDesertionEvent` class:

```python
# ---------------------------------------------------------------------------
# Social Memory consequence events (TCK-20260619-E43E-CONSEQUENCE-EVENTS)
# ---------------------------------------------------------------------------

LEGENDARY_ARRIVAL = "LEGENDARY_ARRIVAL"
KNOWN_TRAITOR_SPOTTED = "KNOWN_TRAITOR_SPOTTED"
OLD_DEBT_COLLECTED = "OLD_DEBT_COLLECTED"

class LegendaryArrivalEvent(SimulationEvent): ...
class KnownTraitorSpottedEvent(SimulationEvent): ...
class OldDebtCollectedEvent(SimulationEvent): ...
```

All use `event_category="social"`, `source_system="social_consequence_evaluator"`.

## Step 2 — Create `src/systems/social_systems/consequence_events.py`

Single public function:

```python
def evaluate_social_consequence(
    entity,         # EntityState (duck-typed)
    faction_id: str,
    campaign_state, # CampaignState (duck-typed)
    tick: int = 0,
) -> list:
```

Logic:
1. Look up `campaign_state.faction_social_memories.get(faction_id)` → faction_mem
2. Look up `campaign_state.social_memories.get(entity.id)` → social_record
3. If `faction_mem` and `faction_mem.entity_hostility.get(entity.id, 0.0) >= 0.5`:
   → emit `KnownTraitorSpottedEvent`
4. If `social_record` and `social_record.faction_reputation.get("default", 0.0) >= 0.9`:
   → emit `LegendaryArrivalEvent`
5. For each `(other_id, score)` in `social_record.relationship_scores`:
   if `score >= 0.5`: → emit `OldDebtCollectedEvent`
   (max 1 event per encounter — use first matching other_id)
6. Return list of all emitted events.

## Step 3 — Append tests to `tests/unit/social/test_social_memory.py`

Add `# E43E` section with the 8 tests from the test plan.

## Step 4 — Create `docs/simulation/domains/social_memory_contract.md`

New domain contract doc covering E43A–E43E capabilities and the cross-episode social memory
subsystem.

## Step 5 — Update `docs/simulation/social_systems_contract.md`

Add a "Cross-episode Social Consequence Events" section at the bottom referencing the
`consequence_events.py` evaluator and the 3 event kinds.

## Step 6 — Add `SOC-CROSS-EP-005` to `docs/parity_ledger/social_narrative.yaml`

New entry covering `evaluate_social_consequence()` and the 3 event classes.

## Architecture review

- `consequence_events.py` imports: only `src.observability.events` and stdlib. No engine or core.state.
- Events are `SimulationEvent` instances (Pydantic BaseModel) — safe to return from APIs.
- No durable state mutation. Pure read of `CampaignState` fields.
- Deterministic: threshold comparisons only, no randomness.
