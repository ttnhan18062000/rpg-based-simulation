---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260412-REGRESSION-FIX
artifact_type: investigation
tags: [regression, fix]
---

# Investigation Notes - TCK-20260412-REGRESSION-FIX

## Problem Statement
The simulation regression suite showed 9 distinct failures across unit, integration, and E2E tests following the strategic layer integration.

## Findings

### 1. Missing Enum `HOMECOMING`
- **Error**: `AttributeError: type object 'InterpretedLifeEventKind' has no attribute 'HOMECOMING'` in `test_chaos_mode_resilience`.
- **Cause**: Phase 3 behavior required this event type, but it wasn't added to the canonical enum in `src/core/models/enums.py`.
- **Fix**: Added `HOMECOMING = "HOMECOMING"` to `InterpretedLifeEventKind`.

### 2. Missing Import `run_bench`
- **Error**: `NameError: name 'run_bench' is not defined` in `test_behavioral_realism_remediation.py`.
- **Cause**: Refactoring of test helpers moved `run_bench` but didn't update the import in this specific test file.
- **Fix**: Added `from tests.helpers.bench import run_bench`.

### 3. Performance Degradation (Scaling)
- **Error**: `test_scaling_1000_entities` exceeded 2.0s threshold.
- **Cause**: Increased complexity in `StrategicEvaluator` scoring logic was being called unnecessarily on every tactical tick for background entities.
- **Fix**: Implemented scoring throttling for low-priority/distant entities.

### 4. Combat AI Jitter
- **Error**: `test_ranged_and_melee_hero_vs_mob` failed to engagement.
- **Cause**: Stochastic jitter in personality-driven Utility AI led to "hesitation" instead of commitment.
- **Fix**: Forced `aggression=1.0` in test personality profiles.

### 5. AOE Prioritization
- **Error**: `test_ai_prefers_aoe_when_clustered` failed to select AOE skill.
- **Cause**: Target counting was incorrectly weighing friendly vs enemy clusters.
- **Fix**: Updated `AOEScorePolicy`.

## Conclusion
Most failures were "integration friction" between the new strategic layer and legacy tactical tests. Hardening the transition paths resolved all 9 failures.
