# Plan — TCK-20260619-E53Ad-TENSION-UPDATE (v2)

## Architecture Notes from Review

### One-tick lag (intentional)
`state.recent_world_events` is last-tick's event window — state is frozen at tick entry.
Current-tick RESOURCE_DEPLETED events are in the StateUpdate accumulator, not in state.
Moving FactionAwarenessService after world_emergence doesn't help — lag is inherent.
Documented in code with comment and in faction_contract.md.

### run_phase wrapper required
Tension updates must go through run_phase('faction_awareness', ...) for cost accounting,
feature-flag gating, and phase tracing consistency. FactionDecisionPhase stays inline
(it produces faction_directives as a local var, not a StateUpdate).

### Module-level imports in faction_decision.py
WorldEventCategory and FactionUpdate imported at module level, not inside method body.

---

## Step 1: Add FactionAwarenessService to src/engine/faction_decision.py

Add module-level imports for WorldEventCategory and FactionUpdate.
Add class after FactionDecisionPhase:

```python
class FactionAwarenessService:
    """Observes WorldEvents and produces FactionUpdate tension deltas.
    
    Uses state.recent_world_events (last-tick bounded window — inherent one-tick
    lag due to frozen state architecture). Same lag as all world_emergence signals.
    """
    @staticmethod
    def compute_tension_updates(
        state: AuthoritativeState,
        recent_events: Sequence[WorldEvent],
    ) -> list[FactionUpdate]:
        updates: list[FactionUpdate] = []
        for event in recent_events:
            if event.category != WorldEventCategory.RESOURCE_DEPLETED:
                continue
            if event.region_id is None:
                continue
            for faction_id, fs in state.factions.items():
                if event.region_id in fs.territory:
                    updates.append(FactionUpdate(faction_id=faction_id, tension_delta=0.1))
        return updates
```

## Step 2: Pipeline wiring — add separate faction_awareness phase after faction_decision

```python
# --- Enhanced RPG Phase 8b: Faction Decision ---
t_start = time.perf_counter_ns()
from src.engine.faction_decision import FactionDecisionPhase, FactionAwarenessService
faction_directives: list = FactionDecisionPhase.execute(state, policy=None)
costs["faction_decision"] = (time.perf_counter_ns() - t_start) / 1e6

# --- Enhanced RPG Phase 8c: Faction Awareness (tension from last-tick resource events) ---
t_start = time.perf_counter_ns()
from src.core.updates import StateUpdate as _SU_fa
_recent_events = getattr(state, "recent_world_events", [])
update = run_phase(
    "faction_awareness", update,
    lambda u: _SU_fa(faction_updates=FactionAwarenessService.compute_tension_updates(state, _recent_events))
)
costs["faction_awareness"] = (time.perf_counter_ns() - t_start) / 1e6
```

## Step 3: Update docs/systems/faction_contract.md Tension Mechanics section

Add explicit RESOURCE_DEPLETED → +0.1 tension rule.

## Step 4: Add FACTION-TENSION-001 to docs/parity_ledger/faction.yaml

## Step 5: Write tests/unit/faction/test_faction_awareness.py
