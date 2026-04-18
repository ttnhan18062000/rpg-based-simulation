# Implementation Plan - Milestone 3: Congestion & Advanced Anti-Oscillation

Focusing on broadening the movement model's handling of oscillation and hardening congestion logic in tight spaces.

## User Review Required

> [!IMPORTANT]
> **Oscillation Threshold**: I am setting the threshold for movement oscillation to **2 full cycles** (A-B-A-B) before triggering a forced `WAIT`. This is more aggressive than the combat stalemate detector to prevent jitter.
> **Safe Sidestepping**: Yielding entities will **not** sidestep into "danger" (tiles that are closer to known hostiles than their current position or within weapon range of a known threat).

## Proposed Changes

### [Component] Navigation State & Updates

#### [MODIFY] [mind.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/aspects/mind.py)
- Add `oscillation_counter: int = 0` to `NavigationState`.
- Add `last_route_hash: str | None = None` to `NavigationState` to detect reroute flip-flopping.

#### [MODIFY] [base.py](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/base.py)
- Extend `NavigationUpdate` to support `oscillation_counter` and `last_route_hash`.

---

### [Component] Movement Model Logic

#### [MODIFY] [movement_model.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/logic/movement_model.py)
- **Implement `_detect_oscillation`**: 
  - Analyze `nav.pos_history`.
  - Detect A-B-A patterns.
  - Return `True` if a repeat is found (2-cycle threshold).
- **Implement Reroute Hysteresis**:
  - Store a hash of the current route.
  - If the new route hash is different, only switch if the improvement is > 2 tiles OR if the current route is hard-blocked for 2+ ticks.
- **Implement Safety-First Sidestepping**:
  - `_find_sidestep` will include a proximity heuristic to avoid moving closer to known threats if the actor is not in RETREAT mode.
- **Refine `select_step`**:
  - Incorporate the oscillation check.
  - If oscillating, force the entity to `WAIT` (Stationary) for 1 tick to "clear the rhythm".

---

### [Component] Regression Suite

#### [NEW] [test_congestion_milestone_3.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/movement/test_congestion_milestone_3.py)
- **Scenario 1: Blocked Retreat**: Narrow corridor, low-HP ally trying to move AWAY from threat, high-HP ally blocking them. Low-HP should force low-priority to yield.
- **Scenario 2: Corridor Negotiation**: Two allies meeting in a 1-tile wide lane. Verify tie-breaking logic prevents infinite dancing.
- **Scenario 3: Reroute Flip-Flop**: Set up two paths where one intermittently blocks. Verify entity doesn't jitter between them.

## Verification Plan

### Automated Tests
- `pytest tests/movement/test_congestion_milestone_3.py`
- `pytest tests/core/test_movement_v2.py` (Existing movement tests)

### Manual Verification
- Trace monitoring of `NavigationUpdate` reasons to confirm `ReasonCode.WAITING` or `ReasonCode.YIELDING` are populated correctly during congestion.
