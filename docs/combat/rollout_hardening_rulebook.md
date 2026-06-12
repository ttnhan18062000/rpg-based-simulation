---
status: active
layer: combat
authority: P1
audience: developer
---

# Rollout Hardening Rulebook (Milestone 7)

## 1. Overview
The Rollout Hardening contract specifies how the Combat and Movement Overhaul systems can be safely enabled, disabled, or isolated. This ensures that the system can be stabilized without risky "all-or-nothing" deployments.

## 2. Feature Boundaries
The overhaul is divided into four major feature families, controlled by `SimulationConfig.overhaul_features`:

| Flag | System Legacy Fallback | Description |
| :--- | :--- | :--- |
| `use_legality_v2` | Open legality (no check) | Enforces spatial occupancy and weapon/AOE range rules. |
| `use_combat_interaction_v2` | Random target switching | Enforces target stickiness and Opportunity Attacks. |
| `use_movement_model_v2` | Simple tile-step | Enforces intention priority and congestion handling (WAIT/SIDESTEP). |
| `use_tactical_evaluator_v2` | Aggressive closing | Enforces role-based kiting, retreat, and spacing. |

## 3. Safe Degradation Contract
- **Default State**: All flags should default to `True` for the target release.
- **Fail-Safe Reversion**: Disabling any `v2` flag MUST revert the logic to the `v1` implementation or a documented safe default.
- **No Corruption**: Toggling flags during a simulation run is NOT guaranteed to be safe, but starting a new simulation with any combination of flags MUST be stable.
- **Regression Linked**: Any major change to a `v2` system must be validated against the Milestone 6 Arena Regression suite before being considered "Stable".

## 4. Rollout Validation Criteria
A feature family is considered "Release Ready" when:
1. It is covered by 100% of its required Milestone-specific TDD tests.
2. It does not cause crashes in a 100-tick stress test.
3. Its behavioral outcomes fall within the accepted envelopes defined in `docs/combat/arena_regression_test_matrix.md`.
