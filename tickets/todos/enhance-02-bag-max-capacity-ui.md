# Enhance 02: Show Entity Bag Max Capacity in UI

## Summary

The InspectPanel inventory section should display the entity's current bag usage relative to max capacity (e.g., `"12 / 20 items"` or a capacity bar).

## Current State

The InspectPanel shows inventory items but does not indicate how full the bag is or what the maximum capacity is.

## Proposed Changes

1. **Backend:** Ensure the entity's `bag_capacity` (or equivalent max inventory size) is included in the `/api/v1/state` response `EntitySchema`
2. **Frontend:** In `InspectPanel.tsx` inventory tab, add a capacity indicator:
   - Text: `"Items: 12 / 20"`
   - Optional: thin progress bar showing fill percentage
   - Color coding: green (< 50%), yellow (50–80%), red (> 80%)

## Affected Code

- `src/api/schemas.py` — add `bag_capacity` to `EntitySchema` if not present
- `frontend/src/types/api.ts` — add `bag_capacity` to `Entity` type
- `frontend/src/components/InspectPanel.tsx` — inventory tab capacity display

## Labels

`enhance`, `frontend`, `ui`, `small`
