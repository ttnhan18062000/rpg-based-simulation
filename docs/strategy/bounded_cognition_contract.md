---
status: active
layer: strategy
authority: P1
audience: developer
---

# Bounded Cognition Contract

## Purpose
This document defines the exact data contract and derivation rules for an entity's cognition capacity. This foundation is used to bound strategic reasoning and differentiate thinker quality across the simulation.

## Inputs
The profile is derived from these authoritative entity fields:
- `progression.attributes`: `int_`, `wis`, `per`, `cha`
- `progression.attribute_caps`: `int_cap`, `wis_cap`, `per_cap`, `cha_cap`
- `progression.stamina`: current stamina value
- `progression.max_stamina`: maximum stamina value
- `personality`: `curiosity` (p_cur), `caution` (p_cau), `neuroticism` (p_neu)

## Normalization Rules
Attributes are normalized against their caps:
- `_norm_attr(val, cap) = clamp((val - 1) / (cap - 1), 0.0, 1.0)`
- Fallback `int_=1`, `wis=1`, `per=1`, `cha=1` if missing.
- Fallback `cap=15` if missing.

Stamina is normalized as a ratio:
- `sr = stamina / max_stamina` (fallback `1.0` if `max_stamina <= 0`)
- `fatigue = 1.0 - sr`

## Profile Fields & Formulas
All values are clamped and rounded as specified.

| Field | Range | Formula |
| :--- | :--- | :--- |
| `planning_budget` | 1 - 9 | `int(_clamp(3.0 + 5.0 * n_int + 1.0 * n_wis + traits - stress, 1, 9))` |
| `judgment_stability` | 0.05 - 0.95 | `round(_clamp(0.35 + 0.45 * n_wis + 0.10 * n_int - 0.20 * fatigue + traits - stress - (p_neu * 0.10), 0.05, 0.95), 3)` |
| `evidence_quality` | 0.05 - 0.95 | `round(_clamp(0.30 + 0.50 * n_per + 0.10 * n_wis + 0.05 * n_int - 0.20 * fatigue + traits - stress, 0.05, 0.95), 3)` |
| `social_bandwidth` | 1 - 7 | `int(_clamp(2.0 + 4.0 * n_cha + 1.0 * n_wis, 1, 7))` |
| `detour_depth_limit` | 1 - 4 | `int(_clamp(1.0 + 2.0 * n_int + 1.0 * n_wis + archetype, 1, 4))` |
| `active_slice_limit` | 1 - 9 | `int(_clamp(3.0 + 4.0 * n_int + 2.0 * n_wis + traits, 1, 9))` |
| `concern_intake_limit` | 1 - 5 | `int(_clamp(2.0 + 2.0 * n_wis + 1.0 * n_int, 1, 5))` |
| `lead_retention_limit` | 1 - 7 | `int(_clamp(2.0 + 3.0 * n_per + 2.0 * n_int + traits + (p_cur * 1.5), 1, 7))` |
| `candidate_zone_limit` | 1 - 5 | `int(_clamp(1.0 + 3.0 * n_per + 1.0 * n_int, 1, 5))` |
| `ally_evaluation_limit` | 1 - 7 | `social_bandwidth` |
| `blocker_resolution_patience` | 0.05 - 0.95 | `round(_clamp(0.30 + 0.35 * n_int + 0.25 * n_wis - 0.20 * fatigue, 0.05, 0.95), 3)` |
| `resume_reliability` | 0.05 - 0.95 | `round(_clamp(0.25 + 0.35 * n_int + 0.25 * n_wis + 0.10 * n_per - 0.20 * fatigue - stress + (p_cau * 0.15), 0.05, 0.95), 3)` |
| `interruption_resistance` | 0.05 - 0.95 | `round(_clamp(0.20 + 0.45 * n_wis + 0.15 * n_int - 0.15 * fatigue - stress, 0.05, 0.95), 3)` |
| `abandonment_threshold_mod` | 0.50 - 1.50 | `round(_clamp(0.80 + 0.30 * n_wis - 0.10 * fatigue + archetype, 0.50, 1.50), 3)` |
| `contradiction_sensitivity` | 0.05 - 0.95 | `round(_clamp(0.20 + 0.50 * n_per + 0.10 * n_wis, 0.05, 0.95), 3)` |
| `source_trust_learning_rate` | 0.01 - 0.90 | `round(_clamp(0.10 + 0.40 * n_wis + 0.25 * n_cha, 0.01, 0.90), 3)` |

## Sparse Personality Mapping
- **Deterministic Deltas**: Only `curiosity`, `caution`, and `neuroticism` have mapped effects on cognitive profiles.
- **Strategic Determinism**: Unmapped traits (`aggression`, `greed`, `loyalty`, `ambition`) have **ZERO** effect on the capacity profile to prevent unexpected behavioral jitter.
- **Proof Integrity**: This sparse mapping is enforced by `tests/ai/test_cognition_capacity_builder.py`.

## Determinism & Purity
- **Non-mutating**: The builder must not modify any entity state.
- **RNG-Independent**: Purity must be maintained; no random influences allowed.
- **Purely Derived**: The profile must be derived fresh or cached outside persistent domain truth.

## Non-Goals
- Persistence of the profile in authoritative entity state (it is derived).
