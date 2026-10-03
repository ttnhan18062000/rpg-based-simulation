---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-MYPY-BASELINE-ADVISORY
artifact_type: test_plan
tags: [delivery]
---

# Test Plan — TCK-20261003-MYPY-BASELINE-ADVISORY

All runs one at a time under `systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0`; exit status checked separately.

- Unit (new `tests/tools/test_mypy_gate.py`): summary text for 0 and N new errors; `--annotate` warning only when N > 0; could-not-run (mypy exit 2, filter missing) writes the summary line and warning and returns 2; summary appended, not overwritten; exit codes pass through (0, 1).
- End to end (tmp_path project with its own `[tool.mypy]` and `[tool.mypy_baseline]`): sync a baseline from a file with one error; insert lines above it → gate exit 0; add a new error → exit 1 and only that error printed; duplicate message → exit 1; fix an error without re-sync → exit 0 (allow_unsynced).
- Static: `test_typecheck_gate_configured.py` edited and extended (baseline config keys, baseline file exists and is non-empty, Makefile target filters, CI step runs the gate, still named `mypy`, still `continue-on-error`, no `pip install mypy`); `test_ci_uv_install.py` unaffected; INFRA-TYPE-001 test_path resolves.
- Real data: `mypy src/ ...` → `filter` exit 0 with nothing printed; baseline line count recorded; `uv lock --check`; `uv export` diff.
- PR run (after owner push): the typecheck job stays green, its summary shows the new-error count (0), the other jobs unchanged.
