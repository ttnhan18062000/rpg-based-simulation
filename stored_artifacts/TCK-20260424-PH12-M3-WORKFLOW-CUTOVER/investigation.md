# Phase 12 M3 Investigation: Workflow & CI Cutover

## 1. CI Configuration
- `.github/workflows/main.yml`: Update to use `tests` as the primary gate.
- `Makefile`: Update `test` and `run` targets to default to V2.

## 2. Findings
- Makefile targets `make test` and `make run` now default to `USE_V2_ENGINE=1`.
- CI pipelines are green using the V2 substrate.
