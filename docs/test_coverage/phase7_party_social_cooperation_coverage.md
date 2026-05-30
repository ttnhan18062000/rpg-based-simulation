# Test Coverage Audit: Phase 7 — Party / Social Cooperation Adventure

This document outlines the test coverage partition for social cooperation mechanics, ensuring that Phase 7 tests are high-fidelity, life-strategy-oriented, and non-redundant with existing social/contract mechanisms.

## 1. Existing Coverage (Non-Goals for Phase 7 Duplication)

The current test suites in the repository already cover standard social and contract appraisal mechanics, including:
- **Contract Appraisal by Trust**: Verifies acceptance limits based on baseline trust values.
- **Contract Appraisal by Greed**: Verifies financial trade-offs and greedy acceptance behaviors.
- **Contract Lifecycle**: Covers active contract state updates and ticking down duration.
- **Low-Trust Recruiter Penalty**: Applies negative scoring to recruiters with low familiarity or trust history.
- **Public vs. Private Trust Priority**: Ensures personal interactions overwrite global public reputation.
- **Social Bonds**: Validates incrementing/decrementing of social affinity bonds between entities.
- **Arena Group Coordination**: Tests that multi-entity teams can perform basic battle groups formation.

## 2. Phase 7 Test Scope (Social Cooperation as a Life Strategy)

Phase 7 introduces the missing cognitive decision loop that bridges active objectives, self-assessed capability, spatial partner candidates selection, trust, cooperation learning, and behavioral updates. The new tests focus on:
- **Help-Seeking Decision**: When does an entity choose to ask for support instead of going solo?
- **Partner Selection / Fit**: Evaluating spatial compatibility, role fit, availability, cost, and historical trust.
- **Party Objective Alignment**: Checking if party members are aligned without losing individual agency.
- **Party Cohesion / Abandonment**: Simulating drift, high-risk warnings, low HP, and abandonment decisions.
- **Cooperation Learning**: Memorizing successful rescues, reliable assists, and betrayals, modifying future partner evaluations.
- **Orchestrated Integration Phase**: Validating that the bounded `CooperationPhase` evaluates correctly without global scans or Direct durable mutations.

## 3. Test Cases Audit Matrix

| Test Module / File | Test Category | Target Mechanics Verified |
|:---|:---|:---|
| `test_phase7_cooperation_boundary.py` | Unit | Immutable boundary, no direct mutations, generic self-model inputs |
| `test_phase7_cooperation_postures.py` | Unit | Posture vocabulary definitions, trace tracking, fail-fast unknowns |
| `test_phase7_help_need_evaluator.py` | Unit | RISKY combat support needs, HEALER/SCOUT needs, easy objective soloing |
| `test_phase7_partner_candidate_provider.py` | Unit | Spatial candidate scoping, dead/hostile exclusion, result capping |
| `test_phase7_partner_fit_evaluator.py` | Unit | Role/trust mapping, cost penaltization, past betrayal penalties |
| `test_phase7_cooperation_decision_service.py` | Unit | Personality trait (brave vs. cautious, greedy) biasing, defer logic |
| `test_phase7_cooperation_intent_bridge.py` | Unit | Mapping chosen postures to safe Contract Intents or Strategic Blockers |
| `test_phase7_party_objective_alignment.py` | Unit | Survival priority override of leader objective, alignment checks |
| `test_phase7_party_cohesion_service.py` | Unit | Dead leader impact, distance-based regroup hints, HP-based retreat |
| `test_phase7_cooperation_learning.py` | Unit | Bounded trust adjustments for success (+), rescue (+++), abandonment (---) |
| `test_phase7_cooperation_events.py` | Unit | Observability parity, serializing chosen/rejected candidate details |
| `test_phase7_cooperation_phase.py` | Integration | Execution speed, feature-flag bypass, scoped checks, intent mapping |
| `test_phase7_social_cooperation_scenarios.py` | Integration | End-to-end stories (risky target request, brave vs. cautious, betrayal loop) |
| `test_phase7_social_cooperation_budget.py` | Performance | Benchmarks: 100+ entities, 50 active parties, latency < 5.0ms |
