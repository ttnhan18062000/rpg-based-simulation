# Bounded Cognition — Milestone 1 Contract

## Purpose
This document defines the exact data contract and derivation rules for an entity's cognition capacity. This foundation is used to bound strategic reasoning and differentiate thinker quality across the simulation.

## Inputs
The profile is derived from these authoritative entity fields:
- `progression.attributes`: `int_`, `wis`, `per`, `cha`
- `progression.attribute_caps`: `int_cap`, `wis_cap`, `per_cap`, `cha_cap`
- `progression.stamina`: current stamina value
- `progression.max_stamina`: maximum stamina value

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
| `planning_budget` | 3 - 9 | `int(round(3.0 + 5.0 * n_int + 1.0 * n_wis))` |
| `judgment_stability` | 0.10 - 0.95 | `round(0.35 + 0.45 * n_wis + 0.10 * n_int - 0.20 * fatigue, 3)` |
| `evidence_quality` | 0.10 - 0.95 | `round(0.30 + 0.50 * n_per + 0.10 * n_wis + 0.05 * n_int - 0.20 * fatigue, 3)` |
| `social_bandwidth` | 2 - 7 | `int(round(2.0 + 4.0 * n_cha + 1.0 * n_wis))` |
| `detour_depth_limit` | 1 - 4 | `int(round(1.0 + 2.0 * n_int + 1.0 * n_wis))` |
| `active_slice_limit` | 3 - 9 | `int(round(3.0 + 4.0 * n_int + 2.0 * n_wis))` |
| `concern_intake_limit` | 2 - 5 | `int(round(2.0 + 2.0 * n_wis + 1.0 * n_int))` |
| `lead_retention_limit` | 2 - 7 | `int(round(2.0 + 3.0 * n_per + 2.0 * n_int))` |
| `candidate_zone_limit` | 1 - 5 | `int(round(1.0 + 3.0 * n_per + 1.0 * n_int))` |
| `ally_evaluation_limit` | 2 - 7 | `int(round(2.0 + 4.0 * n_cha + 1.0 * n_wis))` |
| `blocker_resolution_patience` | 0.10 - 0.95 | `round(0.30 + 0.35 * n_int + 0.25 * n_wis - 0.20 * fatigue, 3)` |
| `resume_reliability` | 0.10 - 0.95 | `round(0.25 + 0.35 * n_int + 0.25 * n_wis + 0.10 * n_per - 0.20 * fatigue, 3)` |
| `interruption_resistance` | 0.05 - 0.95 | `round(0.20 + 0.45 * n_wis + 0.15 * n_int - 0.15 * fatigue, 3)` |
| `abandonment_threshold_mod` | 0.60 - 1.20 | `round(0.80 + 0.30 * n_wis - 0.10 * fatigue, 3)` |
| `contradiction_sensitivity` | 0.10 - 0.90 | `round(0.20 + 0.50 * n_per + 0.10 * n_wis, 3)` |
| `source_trust_learning_rate` | 0.05 - 0.85 | `round(0.10 + 0.35 * n_per + 0.20 * n_wis + 0.10 * n_cha, 3)` |

## Determinism & Purity
- **Non-mutating**: The builder must not modify any entity state.
- **RNG-Independent**: Purity must be maintained; no random influences allowed.
- **Purely Derived**: The profile must be derived fresh or cached outside persistent domain truth.

## Non-Goals
- Persistence of the profile in authoritative entity state (it is derived).
- Incorporation of traits/personality in Milestone 1.
