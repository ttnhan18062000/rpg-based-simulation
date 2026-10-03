---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M39
artifact_type: test_plan
tags: [sim, obs, m39]
---

# Test Plan - Observatory Dashboard V1 (Milestone 39)

We will exhaustively verify that the updated dashboard serves correct HTML layouts, has all required view tags, and interacts gracefully with the server endpoints.

## Test Areas

1.  **Layout Smoke Test**:
    *   GET `/api/v1/observability/ui` should return status `200` with text content containing UI headings for all five tabs.
2.  **View Element Presence**:
    *   Verify the presence of distinct HTML sections or buttons with unique IDs for all 5 dashboard views.
3.  **Redirection Test**:
    *   GET `/observability/ui` should correctly return `302`/`307` redirecting to `/api/v1/observability/ui`.
    *   GET `/api/v1/observability/live/ui` should redirect to `/api/v1/observability/ui`.

## Automation Suite

Create a new file `tests/api/test_observatory_dashboard_contract.py` which starts a mock server subprocess and runs standard assertions.
