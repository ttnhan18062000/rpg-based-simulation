---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260527-COG-PHASE1-INVESTIGATION
artifact_type: investigation
tags: [cog, phase1, investigation]
---

# Investigation Report - Phase 1 World Capability Foundation

## Overview of Phase 1 Specification
Phase 1 focuses on building a "World Capability Foundation" that exposes structured options to entities so they can eventually make smarter decisions in Phase 2. It transitions the simulation from a hardcoded set of choices to a dynamically appraised landscape of resources, services, and queries.

## Comparison against existing docs/entity/
- Currently, `EntityState` contains `StrategicComponent` (active projects, objectives, blockers, leads, concerns, etc.), which is fully documented in `entity_base.md`.
- However, we lack the static world database side (registries) and narrow provider queries that check requirements dynamically before exposing options (Resource/Service Opportunity Providers).
- Wiring this up will connect the low-level mechanical structures (e.g. `ResourceTransferIntent`, durabilities, gold transaction checks) into high-level choice classification (Route Families).

## Clean Code and Brainstorming Analysis
- We want to avoid duplicate state mapping. Registries must be read-only, loaded at startup, and accessed in O(1) time.
- The `RequirementEvaluator` should use small, highly cohesive predicates that evaluate individual state conditions without side effects.
