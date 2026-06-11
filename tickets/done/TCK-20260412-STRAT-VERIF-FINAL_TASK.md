---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260412-STRAT-VERIF-FINAL_TASK
phase: done
date: 2026-04-12
tags: [strat, verif, final_task]
---

- [x] Milestone 3: Tested Leads Logic
    - [x] Update `StrategicState` model in `strategy.py`
    - [x] Update `ActionSystem` for state application
    - [x] Update `StrategicEvaluator` to mark leads as tested
- [x] Milestone 4: Social Candidate Filtering
    - [x] Hardened filtering in `SocialCandidateSelectionService`
    - [x] Verify with tests
- [x] Milestone 5: Unit Tests for strategic logic
    - [x] Create `tests/unit/core/logic/test_strategic_reprioritization.py`
    - [x] Implement tests for `ConcernGenerationService`
    - [x] Implement tests for `DirectiveMutationService`
    - [x] Implement tests for `ProjectMutationService`
- [/] Milestone 5: E2E Verification
    - [/] Create `tests/e2e/test_strategic_reprioritization.py`
    - [ ] Define "Near Death" scenario
    - [ ] Verify strategic pivot
- [ ] Milestone 7: Final-System CLI Stabilization
    - [ ] Verify canonical headless bootstrap in `HeadlessRunner`
    - [ ] Implement Scenario-specific baseline tests
    - [ ] Verify Cognition Graph + Replay consistency

**Tier:** standard
**Type:** chore
**Priority:** P1
