---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260418-RESOURCE-KERNEL-M5
artifact_type: investigation
tags: [resource, kernel, m5]
---

# Investigation: Resource-Safe Engine Milestone 5

## Goal
Implement a resource governor and degradation state machine to protect simulation integrity.

## Architectural Decisions

### 1. Pressure Signaling
- We will define a `PressureSignals` container.
- Initial signals:
  - `work_debt_total`: Sum of all items in the deferred queue.
  - `tick_compute_time`: Clock time taken by the previous tick.
  - `memory_estimate`: Rough estimate based on entity count and state size.
  
### 2. Runtime Mode State Machine
- Modes: `NORMAL` (0), `CONSTRAINED` (1), `DEGRADED` (2), `SURVIVAL` (3).
- Escalation: Immediate if any signal exceeds threshold.
- Recovery: Requires all signals to be below threshold for `N` (e.g., 10) ticks (Hysteresis).

### 3. Degradation Policy
- The `Governor` provides a `Mode` to the `Scheduler`.
- `Scheduler.select_work()` will filter based on mode:
  - `NORMAL`: All.
  - `CONSTRAINED`: Filter `OPPORTUNISTIC` (e.g., keep 20%).
  - `DEGRADED`: Skip all `OPPORTUNISTIC`.
  - `SURVIVAL`: Skip all `OPPORTUNISTIC` and minimize `PERIODIC` (if non-authoritative).

### 4. Integration with Kernel
- `Kernel.tick_once()`:
  - Phase 1: Update `PressureSignals`.
  - Phase 2: `Governor.reevaluate(signals)`.
  - Phase 3: `Scheduler.select_work(state, mode)`.

## Technical Risks
- **Oscillation**: High theshold noise can cause rapid mode switching.
- **Solution**: Implement high/low watermarks and recovery cooldown.
- **Signal Accuracy**: `tick_compute_time` is noisy; may need rolling averages.
