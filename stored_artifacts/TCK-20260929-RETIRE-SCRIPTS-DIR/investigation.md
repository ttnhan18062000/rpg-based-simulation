# Investigation — TCK-20260929-RETIRE-SCRIPTS-DIR

The full investigation trail (file-by-file disposition, exact line numbers for every
path/import fix, Makefile targets, doc citations) already lives in the ticket's own Request
Summary/Scope/Related Code Areas — it was produced by `create-tickets` from a live-session
investigation on 2026-09-29 and cross-verified against `origin/main` `e176e277e` before this
ticket was handed off. This file records what I independently re-verified before starting
implementation, rather than re-deriving the whole investigation from scratch.

## Re-verified counts
- `scripts/` (excluding `archive/` and `__pycache__/`): 29 tracked `.py`/`.ps1` files.
  - 23 move (13 → `tools/perf/`, 6 → `tools/release/`, 4 → `tools/maintenance/` pending the
    `protocol_validator.py` check below — see reconciliation note).
  - 6 delete as orphans: `certification_long_run.py`, `merge_documents.py`,
    `process_pytest_report.py`, `refresh_proofs.py`, `run_perf_optimized.py`,
    `split_milestone.py`.
- `scripts/archive/`: 5 files. 1 kept (`ledger_validator.py`, called by
  `scripts/release_gate.py:93`) → moves to `tools/release/`. 4 dead → deleted
  (`apply_traceability.py`, `remediate_checklist.py`, `report_coverage.py`,
  `validate_checklist.py`).
- `tools/extract_defs.py`, `tools/test_docker.py`: both orphaned, both deleted (matches ticket).
- Total deletions: 6 + 4 + 2 = 12. Total moves: 23 + 1 (`ledger_validator.py`) = 24.

## protocol_validator.py — resolved (was an open question in the ticket)
`grep -rn "scripts[./]protocol_validator|scripts\.protocol_validator"` across the whole repo
(excluding `.git`) returns **zero live hits** — every hit is in `tickets/done/`,
`stored_artifacts/`, `docs/archive/`, or `docs/REGISTRY.yaml`. Its target file,
`logic_checklist_exhaustive_v2.md`, doesn't exist; only the non-`_v2`
`docs/archive/logic_checklist_exhaustive.md` does, already archived. It duplicates the purpose
of the already-dead `scripts/archive/validate_checklist.py` (different implementation, same
"parse a checklist's SOURCE/TEST markers" job).
**Resolution: delete disposition, not move** — per the ticket's own fallback
("if it has none, give it a delete disposition in the table instead"). This changes the
`tools/maintenance/` move count from 4 to 3, and adds a 9th confirmed orphan (not one of the
original 8 the epic scoped, but decided the same way, by the same rule, with fresh evidence).

## turbo_run.py logging import
`src_legacy.utils.logging.StructuredJsonFormatter`/`ContextFilter` (line 9) no longer exist
(`src_legacy/` was removed). The live equivalent is `src/logging/formatter.py`, which exports
`JsonFormatter` (renamed from `StructuredJsonFormatter`) and `ContextFilter` (same name).
Fix: `from src.logging.formatter import JsonFormatter as StructuredJsonFormatter, ContextFilter`
is rejected as an alias hack — instead rename the local usage to `JsonFormatter` directly (2
call sites: `setup_turbo_logging`).

Its own relative log-path resolution (line 35, `os.path.dirname(__file__), "..", "logs"`) only
climbs one level, which lands in `tools/` post-move instead of the repo root. Fixed to the
`parents[2]` pattern already used at `tools/perf/live_map_ws_payload_measure.py:90`, applied via
a `REPO_ROOT` constant, consistent with the other 5 moved files needing the same fix
(`generate_optimization_proof.py:19`, `memory_probe.py:23`, `profile_api_payload.py:24`,
`profile_engine.py:17`, `profile_sweep.py:49-50`).

## Reuse precedent confirmed
`tools/gate_checks/` and `tools/mechanism_registry/` (from `TCK-20260916-MECHANISM-REGISTRY-TOOLS-PACKAGE`)
are the existing "domain subpackage under `tools/`, real `__init__.py`, package imports" pattern
this ticket follows for `tools/perf/`, `tools/release/`, `tools/maintenance/`.
`tools/perf/live_map_ws_payload_measure.py` already proves a script-invoked file can coexist
with a package `__init__.py` in the same directory (its own `parents[2]` / editable-install
handling at line 90 is the precedent, not a risk — confirmed unaffected by adding
`tools/perf/__init__.py` since it doesn't import its own package).
