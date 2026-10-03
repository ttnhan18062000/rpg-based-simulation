---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260410-PH1-STG15-REPRIORITIZATION
phase: done
date: 2026-04-10
tags: [ph1, stg15, reprioritization]
---

# TCK-20260410-PH1-STG15-REPRIORITIZATION: Strategic Reprioritization

**Request Summary**: Implement Phase 1 Stage 15 — Strategic Reprioritization from Life Events. This involves linking regional consequence data (danger/stability) and localized scars to the strategic appraisal pass, allowing entities to pivot their projects in response to world-tier trauma.

**Scope**:
- Signature Update: `StrategicEvaluatorService.evaluate` to accept `WorldState` (snapshot).
- Logic: Regional danger/instability detection.
- Logic: Local scar (Battlefield/Raid) detection.
- Logic: "Regional Threat" Concern generation.
- Logic: "Stability Restoration" and "Trauma Investigation" project/objective generation.
- Verification: End-to-end test verifying project pivot during high regional danger.

**Out of Scope**:
- Complex factional coordination for stability restoration (handled in future phases).
- Permanent directive mutation from regional trauma (handled in Phase 1 Stage 16+).

**Acceptance Criteria**:
- Entities correctly detect a high-danger region and generate a "Regional Threat" concern.
- Entities automatically pivot or suspend current projects to prioritize stability-related projects when the threat priority is high.
- Correctly identifies nearby scars and generates investigation objectives.
- Signature changes do not break the `AIBrain` or regression tests.

**Related Tickets**:
- TCK-20260410-PH1-STG1-6 (Core Strategic Models)
- TCK-20260409-PH1-STG13-14 (Succession and Consequences)

**Current Status**: DONE

## Implementation Summary (Stage 15)
- **World Sensing**: Updated `StrategicEvaluatorService` to accept `WorldState`, allowing it to read regional danger and local scars.
- **Crisis Response**: Implemented logic to generate high-priority (6.0) regional threat concerns when danger exceeds 0.6.
- **Strategy Pivoting**: Added dispatch logic to suspend current personal projects in favor of regional stabilization projects during crises.
- **Hysteresis**: Implemented clear thresholds (danger < 0.3) for resuming original projects, preventing strategic "flutter".
- **Verification**: All features validated via `tests/integration/ai/test_strategic_reprioritization.py`.

## Changed Files
- `src/core/logic/strategic_evaluator.py`
- `src/ai/brain.py`
- `tests/integration/ai/test_strategic_reprioritization.py` (New)

**Tier:** standard
**Type:** chore
**Priority:** P1
