---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M39
artifact_type: investigation
tags: [sim, obs, m39]
---

# Investigation Notes - Observatory Dashboard V1 (Milestone 39)

## Current State Analysis

1.  **FastAPI Server**:
    *   Exposes endpoints `/api/v1/observability/live/status` (current tick, speed, memory, counters).
    *   Exposes endpoint `/api/v1/observability/live/health` (live anomaly and rule assessments).
    *   Exposes router `src/api/routes/history.py` (lists runs and sweeps from local repositories).
    *   Exposes router `src/api/routes/search.py` (queries runs, events, anomalies, timelines, and metric trends).
2.  **HTML/JS Dashboard**:
    *   Served at `/api/v1/observability/ui`.
    *   Currently renders a two-column view containing only Live Overview (left panel) and WebSocket ticker (right panel).
    *   Contains placeholder components for entity inspection.

## Core Features Required for V1

*   **View 1 — Live Overview**:
    *   Integrates existing WebSocket live ticker and engine status controls.
    *   Adds status values for `SIM_CADENCE` / active governor modes.
*   **View 2 — Completed Runs**:
    *   Queries `/api/v1/observability/history/runs` using `fetch` at startup/tab-switch.
    *   Lists runs in a beautiful list/grid with metadata (Scenario, Status, Seed, Ticks Completed).
    *   Selecting a run dynamically fetches that run's manifest via `/api/v1/observability/history/runs/{run_id}` and shows detailed health score, failure reason, anomalies summary, and law violations.
*   **View 3 — Sweeps & Baselines**:
    *   Queries `/api/v1/observability/history/sweeps` via `fetch`.
    *   Lists multi-run sweeps.
    *   Selecting a sweep retrieves its summary via `/api/v1/observability/history/sweeps/{sweep_id}` displaying run counts, worst-performing seeds, health distributions, and most common anomalies.
*   **View 4 — Event Search**:
    *   Provides inputs for: `run_id` (selected from completed runs or entered), `entity_id`, `tick_start`, `tick_end`, `severity`.
    *   Queries the `/api/v1/observability/search/events` and `/api/v1/observability/search/anomalies` endpoints.
    *   Displays paginated event lists and evidence payloads in formatted tables.
*   **View 5 — Entity Timeline**:
    *   Allows entering/selecting an `entity_id` and `run_id`.
    *   Queries `/api/v1/observability/search/entity-timeline`.
    *   Displays the chronological list of events and anomalies for that entity.
