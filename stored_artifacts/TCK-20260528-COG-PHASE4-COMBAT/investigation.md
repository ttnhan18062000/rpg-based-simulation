---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260528-COG-PHASE4-COMBAT
artifact_type: investigation
tags: [cog, phase4, combat]
---

# Investigation: Phase 4 — Combat Engagement Cognition

This document tracks technical discoveries, existing code patterns, and state interactions for Phase 4.

## Core Discoveries

- **Sensory Filters**: `SensoryFilter` is already implemented under `src/cognition/` or visible systems. We should consume this visible context to gather target options rather than performing global sweeps.
- **Grudges and Personality**: Traits like bravery, caution, sociability, and industry already exist on `PersonalityComponent`. We will derive caution as `1.0 - bravery` if caution is not directly in traits.
- **Strategic State**: Projects are keyed under `StrategicComponent.projects` and objectives under `StrategicComponent.projects[id].objectives`. ObjectiveKind has definitions for defeating enemies.
- **Memory Storage**: We can store generalization schemas in `IdentityComponent.properties` or inside strategic component beliefs to avoid modifying `EntityState` fields directly.
