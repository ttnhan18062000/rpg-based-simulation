# RPG Engine: Divergence Register

This document tracks intentional divergences from legacy RPG logic. Every row in the logic checklist marked as `INTENTIONAL DIVERGENCE` must link to an entry here explaining the rationale.

## Divergence Entries

### DIV-001: Stamina Regen Scaling
- **Law**: `RPG-RES-NNN`
- **Rationale**: Legacy engine used a non-linear scaling that created "infinite stamina" loops. V2 uses a linear regen with exhaustion thresholds to preserve tactical tension.
- **Status**: ACTIVE

### DIV-002: Social Appraisal Bias
- **Law**: `RPG-SOC-NNN`
- **Rationale**: Legacy used raw random rolls for recruitment. V2 uses a deterministic trust/utility score to ensure replayability and AI fairness.
- **Status**: ACTIVE
