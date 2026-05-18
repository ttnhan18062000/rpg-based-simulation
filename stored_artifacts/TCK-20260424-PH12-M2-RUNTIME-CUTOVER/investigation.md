# Phase 12 M2 Investigation: Runtime Entrypoint Cutover

## 1. Entrypoint Identification
- `src/__main__.py`: Primary entrypoint.
- `src/server.py`: REST/WebSocket server.
- `src/headless.py`: CLI simulation runner.

## 2. V2 Integration Surface
- `src/engine/manager.py`: Bridge between legacy requests and V2 runtime.
- `src/api/presenters/`: Shaped read-models for API consumers.

## 3. Findings
- The entrypoints have been successfully refactored to check `USE_V2_ENGINE` environment flag.
- When enabled, `V2EngineManager` intercepts the tick loop and provides the simulation substrate.
- Telemetry signals from `src` are correctly routed to legacy-compatible stdout/logs.
