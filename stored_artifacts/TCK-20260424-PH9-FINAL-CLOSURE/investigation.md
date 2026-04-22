# Phase 9 Strategic & Social Investigation

## Biological Decay
- Investigated `ApplyPath` to ensure biological debts (hunger, sleep) are reduced before other updates.
- Verified `RoutineService` correctly proposes `EAT`, `SLEEP`, and `REST` actions based on current debt thresholds.

## Hero Lifecycle
- Investigated `LifecycleSystem` for aging logic.
- Verified that natural death triggers `entity_removed` event and handles heirlooms.
- Verified that near-death hardening adds permanent +5 HP to the survivor.

## Regional Dynamics
- Investigated `LegalityServiceV2` for hazard enforcement.
- Verified that hazard damage is applied passively in the pipeline.
- Verified that certain actions (e.g., SABOTAGE) are suppressed in safe regions.

## Social Negotiation
- Investigated `NegotiationComponent` for cost scaling.
- Verified that trust and level affect the base cost of recruitment.
