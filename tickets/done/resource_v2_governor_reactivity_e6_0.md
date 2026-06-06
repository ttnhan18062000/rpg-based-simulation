# TCK-20260503-GOVERNOR-REACTIVITY-HARDENING

## Title
Fixing Governor Reactivity Lag (Zero-Tick Throttle)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Reduce the 1-tick delay in Governor response to extreme hardware or compute pressure.

## Scope
- Implement a "Mid-Tick Emergency Throttle" in the `Kernel`.
- If a tick exceeds the 100ms hard budget *during* resolution, trigger an immediate signal to abort or simplify remaining non-critical phases.

## Acceptance Criteria
- [ ] The engine must stay below 100ms per tick even during 50v50 mass combat spikes.
- [ ] The Governor must be able to switch `RuntimeMode` mid-tick if compute cost spikes unexpectedly.

## Related Code Areas
- src/engine/kernel.py
- src/engine/governor.py
