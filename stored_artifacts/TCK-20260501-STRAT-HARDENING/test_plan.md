---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260501-STRAT-HARDENING
artifact_type: test_plan
tags: [strat, hardening]
---

# Strategic Cognition Test Plan

## Goals
Verify that actors exhibit "bounded rationality" and durable goal persistence across environmental pressures.

## Test Cases

### 1. Inventory Pressure Loop
- **Setup**: Entity has 0 free slots.
- **Action**: Attempt to harvest a node.
- **Expectation**: 
    - `ResourceTransactionResolver` returns `accepted=True` but `inventory_update=None` (dropped).
    - `StrategicIntelligenceSystem.infer_blockers` sees the drop and adds `blocker_inventory_full`.
    - `DetourSuggestionSystem` suggests `reach_location` (Town Center).
    - Entity moves to Town Center.

### 2. Critical Safety Loop
- **Setup**: Entity HP falls to 10%.
- **Action**: Tick brain.
- **Expectation**:
    - `RoutineService` generates `concern_low_hp`.
    - `DetourSuggestionSystem` suggests `reach_location` (Safe Zone/Origin).
    - Entity retreats.

### 3. Lead Suppression & Learning
- **Setup**: Entity has a lead for a resource at a blocked location.
- **Action**: Entity fails to reach it 3 times.
- **Expectation**:
    - `DetourSuggestionSystem.suppress_exhausted_leads` marks it `EXHAUSTED`.
    - Lead is no longer suggested for detours.

### 4. Project Abandonment
- **Setup**: Entity has a project that fails consistently (e.g. target always dead/gone).
- **Action**: Tick until `failure_count >= 3`.
- **Expectation**:
    - Project status becomes `ABANDONED`.
    - `boredom` for that kind increments.
    - Future utility for that project kind is penalized.
