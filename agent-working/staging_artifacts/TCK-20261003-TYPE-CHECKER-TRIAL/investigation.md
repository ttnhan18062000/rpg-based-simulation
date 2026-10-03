---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-TYPE-CHECKER-TRIAL
artifact_type: investigation
tags: [delivery]
---

# Investigation — TCK-20261003-TYPE-CHECKER-TRIAL

Context scan: `search_docs` (only the original mypy ticket and the D13 type-safety audit) and `graphify query` (nothing relevant) first.

## Starting facts
- Current checker: mypy 2.1.0, `[tool.mypy]` in pyproject.toml (python_version 3.11, strict off, `ignore_missing_imports`, five V1 packages excluded), advisory behind mypy-baseline (TCKs just landed on this branch). Measured on the branch base: 1,569 errors, 1,716 output lines, 239 file paths, 38 s uncached, 407 MB.
- Candidates named by roadmap 6.2: **basedpyright** (has a native baseline file) and **Pyrefly**. `ty` is excluded (its only suppression path edits source).
- Both install from PyPI with uv without touching the project: basedpyright 1.40.1 (needs the `nodejs-wheel-binaries` 24.19.0 wheel) and pyrefly 1.3.2. They are installed in scratch environments outside the repository; pyproject.toml, uv.lock, CI and the Makefile are not changed (ticket Out of Scope).
- Machine: 6 cores, 11 GB RAM, no swap; heavy runs are one at a time under `systemd-run --user --scope -p MemoryMax=2G -p MemorySwapMax=0`, exit status checked separately.

## Method decisions
- One commit for all three checkers (recorded SHA). Same source scope as mypy: `src/` minus the five excluded V1 packages. Same dependency view: each checker is pointed at the main project environment's interpreter / site-packages so third-party imports resolve as they do for mypy.
- Config lives in a scratch directory (never in the repository): equivalent Python version (3.11), no strict mode, missing imports ignored, the same excludes. Defaults otherwise, so the comparison reflects what a drop-in adoption costs.
- Per checker record: version, wall time (cold and warm), peak RSS (`/usr/bin/time -v`), error count (and warnings separately where the tool distinguishes them), baseline support (no source edits), and overlap with mypy.
- Overlap is measured at two levels because messages differ: (file, line) pairs and files with at least one error. Reported as intersection sizes and per-checker unique counts, with the top rule/category families per checker.
- Baseline support is checked, not assumed: basedpyright `--writebaseline` / baseline file; Pyrefly's suppression and baseline options (does it have one that does not edit source?).
