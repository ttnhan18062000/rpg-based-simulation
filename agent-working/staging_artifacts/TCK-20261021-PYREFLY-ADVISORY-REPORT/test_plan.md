---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261021-PYREFLY-ADVISORY-REPORT
artifact_type: test_plan
tags: [delivery]
---

# Test plan — TCK-20261021-PYREFLY-ADVISORY-REPORT

New: `tests/codebase/test_pyrefly_report.py`, deterministic, no network, with Pyrefly stubbed in the unit cases.
- Normal: a recorded Pyrefly JSON fixture (small, about 5 errors) against a baseline that holds 3 of them reports 2 new, the baseline size, and file:line plus kind for each new error.
- Report-only: new errors present means exit 0, and the summary still names them.
- Failure: a missing binary means exit 2; non-JSON output means exit 2; an empty or missing baseline file means a clear message and exit 2 (never a silent "0 new").
- Config parity: the `[tool.pyrefly]` excludes equal `[tool.mypy] exclude`.
- CI shape: the `pyrefly-advisory` job has job-level `continue-on-error: true` and `timeout-minutes`, and its name is not a required check name ("Type check", "Code health"). The `typecheck` and `code-health` job blocks are unchanged (compared to a frozen copy, or by asserting that they have no pyrefly reference).
- Makefile: both targets exist, appear in `.PHONY`, and have help text containing "advisory".

Updated pins: `tests/static/test_ci_uv_install.py` (`lint` set plus pyrefly; `_LINT_JOBS` plus `pyrefly-advisory`), and any other pin the scoped runs trip.

Live check (not a unit test): run `make typecheck-pyrefly` on the branch; it reports 0 new against the fresh baseline.

Suites: `tests/codebase`, `tests/static` and `tests/docs` are light. `tests/tools` runs in lead's heavy slot, under `MemoryMax=2G`, with `--basetemp` on /data outside any repo.
