# UI Contract: Bounded Strategic Cognition

## Overview
This document defines how UI consumers (frontend dashboards, inspector tools) should consume and render the bounded cognition data exposed by the API.

## API Schemas
Routes returning `AIDecisionSchema` or `StrategicStateSchema` now include a `strategy` block with the following cognitive fields.

### 1. Capacity Profile (`capacity`)
Static limits derived from character traits.

| Field | Type | Description |
| :--- | :--- | :--- |
| `planning_budget` | `int` | Max evaluated complexity. |
| `detour_depth_limit` | `int` | Max sub-objective depth. |
| `active_slice_limit` | `int` | Max concurrent inputs. |
| `lead_retention_limit` | `int` | Max memory slots for leads. |

### 2. Live Usage (`usage`)
Real-time utilization of the cognitive budget.

| Field | Type | Rendering Recommendation |
| :--- | :--- | :--- |
| `active_slice_used` | `int` | Display as Progress Bar: `used / active_slice_limit`. |
| `dropped_candidates_count` | `int` | Show as Alert if > 0. |
| `retained_leads_used` | `int` | Detail stat for memory usage. |

### 3. Overload Alert (`overload`)
Status indicators for cognitive failure.

| Field | Type | Description |
| :--- | :--- | :--- |
| `is_overloaded` | `bool` | True if budget was exceeded this tick. |
| `overload_score` | `float` | Pressure intensity (0.0 to 1.0+). |

## UI Interpretation Rules
1. **The Overload Alert**:
   - `is_overloaded == true`: Should be rendered with high-priority visual cues (e.g., Red flashing icon, "COGNITIVE OVERLOAD" text).
   - `overload_score > 0.8`: Should be rendered as "Strained" (e.g., Yellow/Orange bars).

2. **The Budget Bar**:
   - `used / limit` ratio should drive the color of the bar.
   - `< 0.5`: Green (Optimal).
   - `0.5 - 0.8`: Yellow (Busy).
   - `> 0.8`: Red (Strained).

3. **Missing Data**:
   - If `capacity` is null, the entity is a "simple" actor (non-strategic) or hasn't performed a strategic tick yet. Render empty or placeholder state.
