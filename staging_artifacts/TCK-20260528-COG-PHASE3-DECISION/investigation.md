# Phase 3 Investigation Report

## Core Objective
The target is to build a robust, stateless, clean, and explainable **Adventure Decision Layer** in `src/domains/adventure/` that bridges interpreted self-models and world options to strategic projects and action intents.

## Scanning/Dependencies
1. **Existing Core state**: `EntityState` contains `self_model` under `SelfModelBundle`.
2. **Phase 1 Content**:
   - Opportunities: `ResourceOpportunityProvider` and `ServiceOpportunityProvider`.
   - Legality: `RequirementEvaluator` from `src/world/providers/requirements.py`.
   - Intents: `ActionIntent` from `src/engine/intent/action_intent.py`.
3. **Strategic system**: `StrategicState` in `src/core/strategic.py` and `StrategicIntelligenceSystem` in `src/systems/strategic.py`. 
4. **Non-Goals**: We must strictly not hardcode a specific story path or add direct one-off behavior in systems.

## Findings & Structural Strategy
- **Isolation**: Adventure decisions must live completely isolated from core schemas in `src/domains/adventure/`.
- **imperfect Decision Bias**: Scoring uses need urgency, expected benefit, expected risk, capability estimate, and personality traits (bravery, caution, greed, curiosity, industry, sociability).
- **First Objective Resolution**: Resolves only the first objective into an `ActionIntent` (such as `MOVE_TO` or a specific target action) using the adapter from Phase 1.
- **Cadence Optimization**: We'll update only eligible and dirty entities to keep timings strictly bounded.
