# Phase 12 Milestone 2 Execution Plan: Runtime Cutover

## 1. Entrypoint Delegation (`src/__main__.py`)
- Refactor `main()` in `src/__main__.py`.
- Add an environment variable check `USE_LEGACY_SRC`.
- If `USE_LEGACY_SRC` is not set or falsy, import and call `src.cli.entry.main()`.
- Else, proceed with legacy `_run_server`, `_run_cli`, etc.

## 2. CLI Argument Alignment
- Audit `src/cli/entry.py` to ensure it handles common flags correctly.
- Add a "Cutover Warning" to `src` output to notify the operator they are using the V2 engine.

## 3. API Server Delegation
- Ensure `src.api.server.create_v2_app` is fully compatible with the expected FastAPI lifecycle.
- Verify that `src` routes are mounted or served correctly when `python -m src serve` is called.

## 4. Smoke Testing
- Run `python3 -m src cli --ticks 10 --seed 42`.
- Run `python3 -m src serve` and hit the `/health` or `/status` endpoint.
- Verify rollback via `USE_LEGACY_SRC=1 python3 -m src cli --ticks 10`.
