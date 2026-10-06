---
status: active
layer: engine
authority: P3
audience: agent
ticket_id: TCK-20261006-GROUP-GUARD-OBLIGATION-MOVE-OUTLIVES-ITS-LEADER
artifact_type: test_plan
tags: [engine, combat]
---

# Test plan

- Unit, `tests/unit/engine/test_pursuit_completion.py` (29): normal flow (guard ends when the leader dies, goes inactive or is gone; ends when the mover leaves the group or is ungrouped); edge cases (a live same-group leader at any distance does not end it, so adjacency is not an end; a leader that merely stops interacting does not end it); failure modes (missing target); regression-prone paths (a guard with no recognised reason and cover-seeking stay unchanged); both dispatchers (`LocalSequentialExecutor`, concurrent worker).
- Disabling controls: guard kinds untracked fails exactly 5; group condition off fails exactly 1.
- Regression: `tests/unit/engine` and the two mechanism-registry checks, 330 passed, 1 skipped.
- Corpus: legacy vs after arms, 4 worlds x 2 runs.

## Proof Plan

- Level: unit, plus a real-kernel corpus measurement.
- Proof kind: regression with disabling controls; the corpus is a measurement only, because it contains no live-mover instance.
- Oracle source: the Sticky-Task Law in `docs/engine/kernel.md` and divergence 2.70/2.71.
- Expected effect: a guard move ends when its leader is dead, inactive, gone, or no longer in the mover's group; recognised combat moves and cover-seeking are unchanged.
- Selected commands: `pytest tests/unit/engine/test_pursuit_completion.py`; `probes/measure.sh <label> [legacy]`.

## Code-health gates (run in a scratch venv at the uv.lock versions)

`ast-grep`, `mypy`, `prek` and `ruff` are not installed in the project venv, so `tests/codebase` cannot run there (44 "tool not found" failures). The blocking gates were reproduced in a scratch venv (`mypy==2.1.0 mypy-baseline==0.7.4 ruff==0.16.10 ast-grep-cli==0.45.3`, first on PATH, project venv behind it):
- `python3 -m codebase.health check`: first run **FAIL, 1 worse**: `src/engine/executor.py LocalSequentialExecutor.execute` function-length 140 > ceiling 138, from gate 4's comment growing from 2 lines to 4. Fixed by trimming the comment back to 2 lines; re-run **OK: 0 new, 0 worse**.
- `python3 -m codebase.structure.packages validate`: 0 problems.
- `mypy src/ | mypy_baseline filter`: 10 lines, all `Returning Any` in files this batch does not touch (`worldbuilding`, `lab`, `observability`, `worldassembly`, `scenarios`); none in `candidate_selector.py`, `executor.py` or `worker_logic.py`.
CI remains the first run in the real environment.
