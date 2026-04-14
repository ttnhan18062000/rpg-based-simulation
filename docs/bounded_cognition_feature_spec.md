# Feature Specification: Bounded Strategic Cognition

## Purpose
The Bounded Strategic Cognition engine introduces deterministic cognitive limits to AI agents. It ensures that agents do not have "infinite" metacognition, creating realistic behavioral variation based on character traits (Intellect, Wisdom, Perception, Charisma) and preventing performance degradation under strategic pressure.

## Data Contract: Cognition CAPACITY Profile
The core contract is the `CognitionCapacityProfile`, derived deterministically from entity attributes.

| Field | Purpose |
| :--- | :--- |
| `planning_budget` | Max concurrent objectives/projects evaluated in appraisal. |
| `judgment_stability` | Resistance to identity drift and project abandonment. |
| `evidence_quality` | Required certainty for a lead to be considered valid. |
| `social_bandwidth` | Max concurrent social bonds/contracts tracked. |
| `detour_depth_limit` | Max nesting of sub-objectives (A -> B -> C). |
| `active_slice_limit` | Max candidates (concerns, leads, etc.) passed to brain. |
| `concern_intake_limit` | Max new concerns processed per tick. |
| `lead_retention_limit` | Max leads kept in memory before dropping low-certainty ones. |

## Profile Derivation Rules
Profiles are built using the `CognitionCapacityBuilder` based on normalized attributes (1-15 scale):
- **Planning Budget**: Primarily `INT` + `WIS`.
- **Judgment Stability**: Primarily `WIS`, penalized by fatigue (low stamina).
- **Active Slice**: Primarily `INT` + `WIS`.
- **Lead Retention**: Primarily `PER` + `INT`.
- **Social Bandwidth**: Primarily `CHA`.

## Bounded Cognition Rules (Operational Semantics)
1. **Candidate Pressure & Overload**:
   - If (Concerns + Leads + Opportunities + Contracts) > `active_slice_limit`, the system drops low-priority candidates.
   - Dropping candidates triggers the `is_overloaded` flag and populates `overload_score`.

2. **Detour Limiting**:
   - When deriving sub-objectives, if the current chain depth >= `detour_depth_limit`, further nesting is blocked.

3. **Lead Filtering**:
   - Leads with `certainty` < `(1.0 - evidence_quality)` are ignored or treated as rumors.

## API Exposure
Exposed via `StrategicStateSchema`:
- `capacity`: The static profile (limits).
- `usage`: Live stats (current count, dropped count).
- `overload`: Alert status and pressure score.

## Replay & Export Exposure
- **Replay**: Every tick records `active_slice_used`, `is_overloaded`, and `dropped_candidates_count`.
- **Graph**: A dedicated `cognition_profile` node is linked from the entity root, containing capacity and usage attributes.
