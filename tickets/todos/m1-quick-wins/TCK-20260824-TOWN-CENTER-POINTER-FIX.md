---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260824-TOWN-CENTER-POINTER-FIX
phase: open
date: 2026-08-24
tags: [world, determinism]
---

# TCK-20260824-TOWN-CENTER-POINTER-FIX

## Title
Fix the town_center Pointer Bug and Its Related Consumers

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
The original town_center pointer bug is confirmed, and deeper investigation found it worse than reported: two more broken consumers (FlowFieldService, a second parallel town_center field on the worker-protocol dataclass), plus a subtler bug where fallback consumers pick an arbitrary tile across every town in the world, not the nearest one. The author wants all of this fixed.

## Scope
- Fix WorldCompiler.compile() so it sets AuthoritativeState.town_center to a real value derived from the compiled town-type region(s), instead of leaving it at default (0,0) for every real generated world
- Fix FlowFieldService.get_flow_direction(target_kind='TOWN',...) to return direction toward the real town location instead of hardcoded ANCHORS waypoints
- Resolve WorkerPacket.town_center's dead-duplicate-state status -- give it a real consumer or remove it
- Fix StrategicRedirectionSystem.enforce() and StrategicIntelligenceSystem's routine-blocker pass to compute the tile nearest to the requesting entity, instead of an arbitrary sorted/iter pick
- Decide, and document, whether town_center should be deprecated in favor of a proper nearest-town lookup (given world composition supports multiple town-type regions) or kept single-value for worlds that today only generate one town

## Out of Scope
- Idea 56 (Drifting Loyalty)'s City-to-capital political distance measure -- confirmed no shared code path, would not consume this fix
- Hardening intelligence.py's next(iter(state.town_tiles)) determinism concern beyond what's needed for the nearest-tile fix, unless it's found to be part of the same fallback bug

## Acceptance Criteria
- [ ] WorldCompiler.compile() sets AuthoritativeState.town_center to a real value derived from the compiled town-type region(s), not left at default (0,0)
- [ ] FlowFieldService.get_flow_direction(target_kind='TOWN',...) returns direction toward the real town location, not hardcoded ANCHORS waypoints
- [ ] WorkerPacket.town_center gains a real consumer or is removed as dead duplicate state
- [ ] StrategicRedirectionSystem.enforce() and StrategicIntelligenceSystem's routine-blocker pass compute the tile nearest to the requesting entity, not an arbitrary sorted/iter pick

## Related Tickets
- TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/core/worker_protocol.py
- src/engine/executor.py
- src/engine/apply.py
- src/engine/checkpoint.py
- src/engine/scheduler.py
- src/worldbuilding/compiler.py
- src/worldassembly/resolver.py
- src/worldgeneration/generator.py
- src/systems/world_systems/navigation.py
- src/systems/strategic_systems/redirection.py
- src/systems/strategic_systems/intelligence.py
- src/town/town_navigation.py
- src/town/home_storage.py
- src/ai/goals/scorers.py
- src/ai/goals/adventure_scorer.py
- src/engine/tactical.py

## Assumptions / Open Questions
- Whether to deprecate town_center for a proper nearest-town lookup or keep it single-value (since worlds today only generate one town) is a real design decision this ticket must make explicit
- Fixing the WorldCompiler root cause may transitively fix every other direct consumer (town_navigation.py, home_storage.py, scheduler.py, scorers.py, adventure_scorer.py, tactical.py's TOWN_RETURN path), not just the 3 consumers named in the original concern -- investigate and confirm during implementation

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
