---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-MYPY-BASELINE-ADVISORY
artifact_type: investigation
tags: [delivery]
---

# Investigation — TCK-20261003-MYPY-BASELINE-ADVISORY

Context scan: `search_docs` (hits: TCK-20260623-TYPE-CHECKER, audit D13) and `graphify query` (no useful nodes) first. The planner's pre-check of mypy-baseline 0.7.4 is cited and reproduced below.

## Current state
- `[tool.mypy]` in pyproject.toml: python_version 3.11, strict false, ignore_missing_imports, warn_return_any, warn_unused_ignores; five V1 packages excluded (ai, town, quests, entities, progression). mypy 2.1.0 is locked in `dev`.
- `make typecheck-py`: `python3 -m mypy src/ --config-file pyproject.toml --no-error-summary || true`. CI `typecheck` job: the same command with `|| true` and step-level `continue-on-error`, step named `mypy`.
- Pins on this: `tests/static/test_typecheck_gate_configured.py` (the `[tool.mypy]` section; the Makefile `typecheck-py` target contains `mypy src/` and `pyproject.toml`; the workflow has a step matching `name:\s*mypy` and the text `mypy src/`; no `pip install mypy`), and parity ledger INFRA-TYPE-001 in `docs/parity_ledger/infrastructure.yaml` (v2_evidence cites the Makefile target and the CI step).

## Measurements (reproduced here, mypy 2.1.0 from the main `.venv`, 2 GB cap)
- `mypy src/ ... --no-error-summary`: 1,569 errors, 1,716 output lines (errors plus notes), 239 file paths, 38 s wall, 407 MB peak RSS. Matches the planner's 1,569 errors / 236 files / 48 s / ~400 MB.

## mypy-baseline 0.7.4 behaviour (scratch env, real output; reproduces the planner's toy-file pre-check)
- Config is read from `[tool.mypy_baseline]` in pyproject.toml (keys used and verified: `baseline_path`, `allow_unsynced`, `hide_stats`); `--config`/CLI flags override it.
- `sync` writes entries with the line number replaced by `0` (`path:0: error: ...`) unless `--preserve-position`: 1,716 lines for the real output (errors and their notes).
- Same output through `filter`: exit 0, nothing printed.
- Every line number shifted by +40 (an unrelated edit above existing errors): `filter` exit 0, nothing printed. **This is the "unrelated edit above an existing error" criterion; it holds.**
- One genuinely new error: exit 1, prints only that error.
- A second identical message in the same file counts as new (exit 1, prints the extra one).
- A fixed error whose baseline entry was not re-synced: with `allow_unsynced = true` exit 0; without it (`--config /dev/null`) exit 1 ("Great work! ... run sync"). Without `allow_unsynced`, any domain fixing a type error in src/ would turn the gate red once it blocks.
- `python -m mypy_baseline` works as the entry point (console script not needed).

## Decisions to record
- Dependency group: `dev` (the typecheck job and `make typecheck-py` already use it; mypy is there). Not `lint`: the typecheck job passes `--no-group lint`.
- Baseline path: `registries/mypy_baseline.txt`.
- Re-sync policy: `allow_unsynced = true` in config (CI and `make typecheck-py` never fail on fixed-but-unsynced); `sync` is run by the codebase domain together with the code-health registry reseed, never by a domain fixing a single error, and only on main. Soak records how often a sync is needed.
- Where to record the baseline path and entry count (ticket scope: "registry or snapshot"): in the ticket's Implementation Notes and `docs/guidelines/python_code_standard.md`, not as a new snapshot metric (that would change the snapshot schema and its pinned tests; the planner decides if a metric is wanted).
