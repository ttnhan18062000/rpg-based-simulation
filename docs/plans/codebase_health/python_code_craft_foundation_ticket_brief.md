---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-02
tags: [architecture, planning, process-improvement]
---

# Python Code Craft — Foundation Ticket Brief (M1 to M3)

Scoping brief for `create-tickets`. The binding plan is
`docs/plans/codebase_health/python_code_craft_roadmap.md` (rev 2, approved 2026-10-02). Read it for
evidence, existing-work mapping, conflicts and the toolchain table. This brief only says which
parts become tickets now.

## Constraints that apply to every ticket

- **No file under `src/` may be modified.** No autofix, no reformat, no inline suppression comments
  (`# noqa`, `# type: ignore`). Existing violations are held in an external baseline. Each ticket's
  acceptance criteria must include a check that `git diff --stat` shows no `src/` path.
- No change to simulation behaviour, and no change to `tests/` beyond tests for the new tooling.
- Governing files (`CLAUDE.md`, `.claude/settings.json`, hooks) are not edited by these tickets.
  `.claude/agents/`, `.claude/workflows/` and `.claude/skills/` belong to the `agent-working` domain
  and are not edited either.
- New tooling goes in a `tools/code_health/` subpackage per `docs/guidelines/repo_tooling_layout.md`.
- Reuse what exists (roadmap Section 4): extend `tools/codebase_health_snapshot.py`, do not build a
  second metrics tool; do not add a new dead-code detector; do not re-file the pairs in
  `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS`.
- Out of scope for this pass: roadmap milestones M4 (CI gates, mypy blocking, prek), M5 (package
  registry, ast-grep, import-linter), M6 (agent integration) and M7 (refactor lane).

## Concern 0: Epic — Python Code Craft Foundation

A scope-only epic-tier ticket that tracks the three milestones below as its children and cites the
roadmap. It closes when M1, M2 and M3 are done. It implements nothing itself.

## Concern 1: M1 — Python code standard document

Write `docs/guidelines/python_code_standard.md`: short, checkable rules for function and class
design, size and complexity thresholds (roadmap Section 6.1), naming, docstrings, typing, error
handling and module layout. Each rule states whether a tool enforces it or a reviewer judges it.
It cites `docs/guidelines/design_patterns.md` and `docs/engine/architecture_reference.md` §9 and
does not restate them. Also: add a row to `docs/guidelines/subsystem_ownership_lifecycle.md`, and
register the roadmap in `docs/plans/plans_tracking.md`. Docs only.

## Concern 2: M2 — uv as the single dependency source

Finish the half-done uv adoption. Today dependencies are declared in `pyproject.toml`,
`requirements.txt` and a stale `uv.lock`; CI installs with `pip install -r requirements.txt`; CI
runs Python 3.13 while `pyproject.toml` says `>=3.11` and mypy targets 3.11. Deliver: dependencies
declared once in `pyproject.toml` with dev tooling in a dependency group; a refreshed `uv.lock`;
`requirements.txt` kept as a generated export until every CI job is moved; **one** CI job migrated
to `uv sync` first, the rest following only after it is green; the Python version statement
aligned; `docs/guidelines/agent_working_environment.md` updated. It must keep the knowledge-search
stack split (`TCK-20260702-CI-REQUIREMENTS-SPLIT`), satisfy the CI static tests under
`tests/static/`, and keep `tests/static/test_no_hardcoded_venv_interpreter_path.py` passing.
This may reasonably split into more than one ticket (declare and lock; migrate CI).

## Concern 3: M3 — Measure and baseline

Depends on Concern 2 for installing the tools. Deliver, with no `src/` edits:

- Configuration for `ruff check` (no formatter), `complexipy`, `jscpd`, and a small line-count
  script for function, class and module length (no existing tool offers that with a baseline).
- `tools/code_health/`: adapters that normalise each tool's JSON output, and one ratchet command
  that fails only when a violation is new or worse than its baseline row. Matching is by file and
  symbol, not line number, so moved code does not resurface as new.
- `registries/code_health_exceptions.jsonl` with a CLI and validator modelled on
  `tools/capability_envelope_baseline.py`, seeded from a full scan with `reviewed: false`. Unlike
  the tag and layer registries, rows are deleted when debt is paid.
- A `make code-health` entry point (and `make lint-py`).
- Craft metrics added to `tools/codebase_health_snapshot.py`, and the first snapshot taken.
- Tests for the adapters, the ratchet and the registry validator.

Each tool must be confirmed to work on this repo or be dropped with the reason recorded; the
versions and features in the roadmap came from web research and are not all verified. This concern
may reasonably split (tool configuration; ratchet and registry; snapshot extension).
