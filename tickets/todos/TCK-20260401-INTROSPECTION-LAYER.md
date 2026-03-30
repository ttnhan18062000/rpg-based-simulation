# TCK-20260401-INTROSPECTION-LAYER: Rendering & Explainability Endpoints

## Description
This ticket addresses the fourth priority of the `final_implementation_plan.md`. It involves building the dedicated introspection layer that provides rich rendering data (combat traces, AI reasoning, stat breakdowns) without polluting the main overview stream.

## Scope
- **Stat Breakdowns**: Implement endpoints to explain how effective stats are derived (base + modifiers).
- **Combat Traces**: Build detailed combat resolution logs including roll values and elemental modifiers.
- **AI Explanation**: Provide "reasoning" traces for actor decisions (goal weights, perception filters).
- **Turn-order Views**: Expose the scheduler's internal projection for the next `next_act_at` sequence.

## Acceptance Criteria
- [ ] `GET /api/v1/inspect/entity/{id}` returns rich aspect-specific metadata.
- [ ] `GET /api/v1/combat/trace/{tick}` provides detailed resolution logs.
- [ ] Main world stream size is reduced by offloading rich details to these specialized endpoints.
- [ ] UI is powered by the same truth source as the simulation engine.

## Related Tickets
- [TCK-20260331-RUNTIME-INTEGRITY](file:///home/vboxuser/Work/rpg-based-simulation/tickets/inprogress/TCK-20260331-RUNTIME-INTEGRITY.md)

## Status
TODO
