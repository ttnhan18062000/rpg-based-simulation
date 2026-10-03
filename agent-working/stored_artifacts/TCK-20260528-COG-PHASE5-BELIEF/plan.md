---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260528-COG-PHASE5-BELIEF
artifact_type: plan
tags: [cog, phase5, belief]
---

# Plan: Phase 5 — Information / Belief / Source-Trust Loop

This document coordinates the technical plan for Phase 5.

## Proposed Changes

### Component: `src/domains/information`

We will create a modular information/belief stratum.

#### [NEW] `schema.py`
- Define `InformationSourceProfile`, `InformationSourceCandidate`, `NormalizedInformationResponse`, `InformationAssimilationResult`, `RouteImpactHint` schemas.
- Define `InformationQuery` input shapes.

#### [NEW] `router.py`
- Implement `InformationQueryRouter` matching query scopes vs source profiles within proximity/cost limits.

#### [NEW] `normalizer.py`
- Implement `InformationResponseNormalizer` aligning distinct responses into normalized standard models.

#### [NEW] `assimilation.py`
- Implement `InformationAssimilationService` updating knowledge facts and unknowns within capacity restrictions.

#### [NEW] `contradiction.py`
- Implement `BeliefContradictionService` updating claim matches vs observations.

#### [NEW] `trust.py`
- Implement `SourceTrustUpdateService` performing slow gradual clamps inside [0.0, 1.0].

#### [NEW] `bridge.py`
- Implement `ObservationBeliefBridge` converting direct observations to beliefs.

#### [NEW] `route_impact.py`
- Implement `BeliefRouteImpactService` providing hints to redirect route scorers.

#### [NEW] `resolver.py`
- Implement `InformationIntentResolver` mapping queries into executable ActionIntents.

#### [NEW] `phase.py`
- Implement `InformationBeliefPhase` behind a feature flag.

## Verification Plan

### Automated Tests
- We will add 14 test files checking unit, integration, scenarios, and budget performance targets.
