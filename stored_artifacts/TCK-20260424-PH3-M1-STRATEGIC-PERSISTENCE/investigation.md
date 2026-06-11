---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260424-PH3-M1-STRATEGIC-PERSISTENCE
artifact_type: investigation
tags: [ph3, m1, strategic, persistence]
---

# Strategic Persistence Investigation

## Current State
- `StrategicIntelligenceSystem` proposes new projects every tick if idle.
- Combat clears tactical goals but doesn't explicitly manage strategic project lifecycle.
- Scheduler occasionally dispatches `BRAIN` work for dead entities if they still have readiness.

## Findings
- Project resumption requires readiness >= 100.0.
- Combat resolution correctly routes intents, but state-injection in tests needs synchronization.
- `ent.active` is the definitive source of truth for scheduling.
