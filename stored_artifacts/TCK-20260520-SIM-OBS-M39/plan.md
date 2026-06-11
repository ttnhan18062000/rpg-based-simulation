---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M39
artifact_type: plan
tags: [sim, obs, m39]
---

# Implementation Plan - Observatory Dashboard V1 (Milestone 39)

We will design and implement the first production-grade SPA dashboard that provides comprehensive simulation telemetry, run manifests, sweep analysis, multi-run query, and entity timelines.

## Proposed Changes

### UI & API Server

#### [MODIFY] [server.py](file:///home/vboxuser/Work/rpg-based-simulation/src/api/server.py)

We will completely expand the HTML served at `/api/v1/observability/ui` to include:
- A navigation bar at the top of the content pane to switch between the 5 views:
  - **Live Overview**
  - **Completed Runs**
  - **Sweeps & Baselines**
  - **Event Search**
  - **Entity Timeline**
- Implement dynamic client-side rendering with pure modern ES6 JavaScript.
- Fetch runs, sweeps, events, anomalies, timelines, and metrics asynchronously from the stabilized FastAPI `/api/v1/observability/history/*` and `/api/v1/observability/search/*` endpoints.
- Enhance the visual style with Outfit & JetBrains Mono fonts, smooth CSS animations, neon green/blue/amber color accents, glassmorphic cards, and detailed JSON data inspect collapsibles.
- Handle zero-states elegantly (e.g. "No runs found" or "Enter search filters to query events").

## Verification Plan

### Automated Tests
- Run uvicorn server in uvicorn test sub-processes and execute automated HTTP queries verifying that `/api/v1/observability/ui` serves rich HTML with the 5 views.
- Add regression test suite `tests/api/test_observatory_dashboard_contract.py`.

### Manual Verification
- Render and visual inspection of the dashboard using the browser tool to confirm that tabs render flawlessly and transition smoothly.
