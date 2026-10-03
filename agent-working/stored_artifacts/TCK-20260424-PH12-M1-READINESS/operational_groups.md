---
content_type: doc
status: historical
layer: misc
authority: P2
audience: agent
tags: [ph12, m1, readiness]
---

# Phase 12 Operational Cutover Groups

## Group A: Headless CLI (Priority 1)
- **Consumers**: Automation scripts, CI runners.
- **Entrypoint**: `python3 -m src.cli.entry`
- **Workflow**: `SIMULATE -> RECORD -> VERIFY`
- **Dependency**: 100% bit-identical movement parity.

## Group B: Developer API (Priority 2)
- **Consumers**: Frontend v2, External debuggers.
- **Entrypoint**: `python3 -m src.api.server`
- **Workflow**: `SERVE -> WEBSOCKET_STREAM -> INTROSPECT`
- **Dependency**: `LegalityService` enforcement.

## Group C: Deterministic Replay (Priority 3)
- **Consumers**: Analysts, Regression tools.
- **Entrypoint**: `python3 -m src.cli.entry --replay`
- **Workflow**: `LOAD_REPLAY -> STEP -> COMPARE`
- **Dependency**: `ReplayManager` finalization logic.
