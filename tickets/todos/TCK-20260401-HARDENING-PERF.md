# TCK-20260401-HARDENING-PERF: Infrastructure Safety & Performance Optimization

## Description
This ticket addresses the fifth priority of the `final_implementation_plan.md`. It focuses on infrastructure safety (replacing or hardening pickle) and transport efficiency (payload caching).

## Scope
- **Serialization Safety**: Audit and replace `pickle` with schema-checked JSON/BSON for recovery payloads.
- **Transport Caching**: Precompute tick overview payloads once per tick to serve multiple clients efficiently.
- **Stream Compression**: Optimize the binary WebSocket stream for high-entity-count scenarios.
- **Phase Invariants**: Add runtime assertions for phase-boundary safety.

## Acceptance Criteria
- [ ] `pickle` is removed from all high-risk infrastructure channels.
- [ ] Tick overview generation takes < 2ms for 50+ entities.
- [ ] Payload size remains stable even as simulation complexity grows.

## Related Tickets
- [TCK-20260331-RUNTIME-INTEGRITY](file:///home/vboxuser/Work/rpg-based-simulation/tickets/inprogress/TCK-20260331-RUNTIME-INTEGRITY.md)

## Status
TODO
