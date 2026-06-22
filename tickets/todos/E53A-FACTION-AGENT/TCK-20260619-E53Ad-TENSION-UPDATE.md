---
status: open
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260619-E53Ad-TENSION-UPDATE
phase: open
date: 2026-06-22
tags: [faction, faction-tension, resource-depleted, world-event, authoritative-path, phase-5]
---

# TCK-20260619-E53Ad-TENSION-UPDATE

## Title
Epic 5.3Ad · Faction Awareness — Tension Update from RESOURCE_DEPLETED Events

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implement faction awareness: observe `RESOURCE_DEPLETED` world events that occurred in a faction's territory and produce `FactionUpdate.tension_delta = +0.1` per event, applied via the authoritative path. Tension is capped at 1.0. Depends on E53Aa (FactionState + FactionUpdate must exist). Can be developed concurrently with E53Ac.

## Scope

**FactionAwarenessService** (new in `src/engine/faction_decision.py` or `src/domains/factions/awareness.py`):
```python
class FactionAwarenessService:
    @staticmethod
    def compute_tension_updates(
        state: AuthoritativeState,
        recent_events: Sequence[WorldEvent],
    ) -> list[FactionUpdate]:
        """
        For each WorldEvent with category=RESOURCE_DEPLETED:
          - Determine the region_id of the event (event.region_id or event.source_id)
          - For each FactionState where region_id in faction.territory:
            - Emit FactionUpdate(faction_id=..., tension_delta=+0.1)
        Returns list of FactionUpdate (one per faction per event, capped at tension_level=1.0 at apply time).
        """
```

**Apply-path cap**: In the apply logic for `FactionUpdate` (added in E53Aa), ensure:
```python
new_tension = min(1.0, old_tension + update.tension_delta)
```

**Wiring**: Call `FactionAwarenessService.compute_tension_updates()` in the same execution site as `FactionDecisionPhase.execute()` (world_dynamics or faction_dynamics system), passing `recent_events` from the current tick's event buffer. Merge resulting `FactionUpdate` objects into the tick's `StateUpdate.faction_updates`.

**WorldEvent region field**: Check `src/domains/world_emergence/schema.py:WorldEvent` for the region identifier field name (likely `region_id` or `source_id`) before implementing.

## Out of Scope
- FactionState model (E53Aa)
- FactionDecisionPhase / FactionDirective (E53Ab)
- Directive propagation to entity scoring (E53Ac)
- Diplomatic tension triggers (E53B)

## Acceptance Criteria
- `test_faction_tension_increases_on_resource_depletion` passes:
  - Given FactionState(faction_id="hero_guild", territory=("region_01",), tension_level=0.0) and a RESOURCE_DEPLETED WorldEvent for region_01, `compute_tension_updates()` returns `[FactionUpdate(faction_id="hero_guild", tension_delta=0.1)]`
- `test_faction_tension_capped_at_1_0` passes:
  - Given tension_level=0.95, applying tension_delta=0.1 results in tension_level=1.0 (not 1.05)
- `test_resource_depleted_outside_territory_no_update` passes:
  - RESOURCE_DEPLETED event in region NOT in faction.territory → no FactionUpdate emitted
- `test_no_factions_no_updates` passes:
  - `state.factions={}` → returns `[]` without error
- Existing world_dynamics / economy tests continue to pass (no regressions)

## Related Tickets
- TCK-20260619-E53A-FACTION-AGENT (parent epic)
- TCK-20260619-E53Aa-FACTION-STATE (prerequisite — FactionState + FactionUpdate must exist)
- TCK-20260619-E53Ab-DECISION-PHASE (sibling — can run concurrently; shares wiring site)
- TCK-20260619-E53Ac-DIRECTIVE-PROP (sibling — can run concurrently)

## Related Docs
- `docs/engine/authoritative_mutation_pipeline_contract.md` (mutation must go through apply path)
- `docs/mechanics/03_economic_laws.md` (resource depletion mechanics — read for context only)
- `docs/systems/faction_contract.md` (update tension section when created by E53Ac)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E53A-FACTION-AGENT/investigation.md`

## Related Code Areas
- `src/engine/faction_decision.py` (FactionAwarenessService — add here or in new `src/domains/factions/awareness.py`)
- `src/engine/economy.py` (RESOURCE_DEPLETED event emission — lines 128, 215 — read for event structure)
- `src/domains/world_emergence/schema.py` (WorldEvent schema — confirm region field name)
- `src/engine/apply_plan.py` (faction update apply — tension cap logic)
- `tests/unit/faction/test_faction_awareness.py` (new file)

## Assumptions / Open Questions
- `WorldEvent` has a `region_id` or equivalent field linking the event to a region. Confirm the exact field name in `src/domains/world_emergence/schema.py` before implementing.
- Each RESOURCE_DEPLETED event contributes `+0.1` tension regardless of severity — the parent epic spec is flat. If severity-weighted tension is desired in future, that is an E53B+ concern.
- Multiple RESOURCE_DEPLETED events in the same tick for the same faction territory are additive (each contributes +0.1), capped at 1.0 after all are applied.
- `FactionUpdate` is defined in E53Aa (`src/core/updates.py`) — this ticket depends on that definition being in place.
- Add a parity ledger entry in `docs/parity_ledger/world_dynamics.yaml` (or a new `faction.yaml` if appropriate) for faction tension awareness (FACTION-TENSION-001).

## Implementation Notes
- Keep `FactionAwarenessService` stateless and pure — same structural pattern as `WorldEmergencePhase` and `FactionDecisionPhase`.
- The `min(1.0, ...)` cap belongs in the apply logic (E53Aa's apply path), not in `compute_tension_updates()` itself — separation of concerns.
- Recent events window: use the same bounded window as WorldEmergencePhase (last 100 ticks): `min_t = max(0, state.tick - 100)`.
- After completion, update `docs/systems/faction_contract.md` (created by E53Ac) with the tension mechanics section.

## Test Summary
```bash
pytest tests/unit/faction/test_faction_awareness.py -x -v
pytest tests/unit/engine/test_economy.py -x -v  # regression guard
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
